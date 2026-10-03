"""Create a self-contained Excel audit of APIs changed from master to main."""
import html
import csv
import ast
import re
import subprocess
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Compare the remote branches that Bitbucket will merge, not local working branches.
OLD, NEW = "origin/master", "origin/main"
ROOT = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8")


_show_cache = {}
_class_cache = {}


def show(ref, path):
    key = (ref, path)
    if key in _show_cache:
        return _show_cache[key]
    try:
        _show_cache[key] = git("show", f"{ref}:{path}")
    except subprocess.CalledProcessError:
        _show_cache[key] = ""
    return _show_cache[key]


def url_files(ref):
    return [p for p in git("ls-tree", "-r", "--name-only", ref).splitlines() if p.endswith("/urls.py")]


def prefixes(ref):
    content = show(ref, "Project/urls.py")
    return {module.replace(".urls", ""): prefix for prefix, module in re.findall(
        r"path\(['\"]([^'\"]*)['\"],\s*include\(['\"]([^'\"]+\.urls)['\"]", content)}


def class_block(ref, source, view):
    cache_key = (ref, source)
    if cache_key not in _class_cache:
        text = show(ref, source)
        blocks = {}
        try:
            tree = ast.parse(text)
            lines = text.splitlines(keepends=True)
            blocks = {
                node.name: "".join(lines[node.lineno - 1:node.end_lineno])
                for node in tree.body if isinstance(node, ast.ClassDef)
            }
        except SyntaxError:
            blocks = None
        _class_cache[cache_key] = blocks
    cached = _class_cache[cache_key]
    if cached is not None:
        return cached.get(view, "")
    text = show(ref, source)
    match = re.search(r"^class\s+" + re.escape(view) + r"\b.*?(?=^class\s+|\Z)", text, re.M | re.S)
    return match.group(0) if match else ""


def methods(ref, source, view):
    body = class_block(ref, source, view)
    return ", ".join(m.upper() for m in re.findall(r"^\s+def\s+(get|post|put|patch|delete)\s*\(", body, re.M)) or "Verify"


def human_path(path):
    return re.sub(r"<(?:(?:int|str|uuid):)?([^>]+)>", r"{\1}", path)


def routes(ref):
    result = {}
    prefix_map = prefixes(ref)
    for file in url_files(ref):
        module = file.rsplit("/", 1)[0]
        if module not in prefix_map:
            continue
        content = show(ref, file)
        # This intentionally tracks urlpatterns that map directly to views.Class.as_view().
        pattern = r"^\s*path\(\s*['\"]([^'\"]*)['\"]\s*,\s*views\.([A-Za-z_]\w*)\.as_view\(\)"
        for suffix, view in re.findall(pattern, content, re.M):
            path = human_path(prefix_map[module] + suffix)
            source = module + "/views.py"
            result[path] = {"module": module, "url_file": file, "view": view,
                            "source": source, "methods": methods(ref, source, view)}
    return result


def purpose(row):
    name = row["view"]
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name).replace("APIView", " API").replace("View", "")
    return text.strip()


def test_focus(change, route):
    if change == "New API":
        return "Test authentication, required inputs, success response, validation errors, and authorization."
    if change == "Changed existing API":
        return "Regression-test the existing contract: inputs, status codes, response schema, permissions, and edge cases."
    return "Confirm consumers have migrated; verify the expected replacement or decommissioning behavior."


DETAILS = {
    "/api/v1/payment/bank-validation-pams": (
        "Added PAMS Penny Drop bank validation. Requires name, acc_num, ifsc, bank_name, and city_name; registers/fetches the bank account, calls PAMS, saves pams_account_id, and returns verified or pending validation status.",
        "payment/urls.py; payment/views.py; payment/validator.py; payment/models.py; payment/migrations/0016_userbankaccount_pams_account_id.py; app_farm/utils/helper.py; libraries/pams.py; libraries/pubsub/pms_sub_listener.py; libraries/pubsub/pubsub_listener.py; core/management/commands/start_pms_listener.py; Project/settings.py; requirements.txt",
        "Confirmed by commit messages: introduce PAMS/Penny Drop bank-account verification and return the PAMS response (commits 05c66d0f, fd65ae0d, efc1b1cf).",
    ),
    "/api/v1/payment/bank-validation-by-admin-pams": (
        "Added admin-initiated PAMS Penny Drop validation. Same PAMS flow as above, plus required user_id to select the account owner.",
        "payment/urls.py; payment/views.py; payment/validator.py; payment/models.py; payment/migrations/0016_userbankaccount_pams_account_id.py; app_farm/utils/helper.py; libraries/pams.py; libraries/pubsub/pms_sub_listener.py; libraries/pubsub/pubsub_listener.py; core/management/commands/start_pms_listener.py; Project/settings.py; requirements.txt",
        "Confirmed by commit messages: introduce PAMS/Penny Drop bank-account verification and return the PAMS response (commits 05c66d0f, fd65ae0d, efc1b1cf).",
    ),
    "/api/v1/payment/razorpay-webhooks": (
        "Changed payment-link handling: the Kutumb/CA Life member submission is commented out, so a paid Razorpay payment will no longer trigger that call. Procurement payout and insurance-status paths remain.",
        "payment/views.py",
        "Not explicitly stated in the commit messages. Inference from the code: prevent or defer the CA Life member-submission side effect after Razorpay payment.",
    ),
    "/api/v1/record/send-conversation-ms/": (
        "Changed image-upload error handling. Unsupported files now return HTTP 400 with INVALID_FILE; other upload failures return HTTP 400 with UPLOAD_FAILED, instead of propagating the upload exception.",
        "recordActivity/views.py",
        "Confirmed by commit 210c0e89: Improve upload validation errors in recordActivity.",
    ),
    "/api/v1/verify/boundary-update/": (
        "Changed boundary task handling. CSV-upload/task-creation flow was removed; known task IDs return persisted status details. If the supplied task ID is not found, the code attempts to return an undefined response variable and falls into the HTTP 500 error handler—treat this as a regression risk.",
        "verification/views.py",
        "Not explicitly stated in the commit messages. This was modified during the PAMS integration changes; the intended product reason needs confirmation from the developer/PR owner.",
    ),
}


def change_details(path, row):
    return DETAILS.get(path, ("Implementation class changed; inspect the evidence files before testing.", row["url_file"] + "; " + row["source"], "Reason not documented in the commit history."))


def cell(value):
    value = html.escape("" if value is None else str(value))
    return f'<c t="inlineStr"><is><t>{value}</t></is></c>'


def sheet_xml(rows):
    body = []
    for index, row in enumerate(rows, 1):
        body.append("<row r=\"%s\">%s</row>" % (index, "".join(cell(x) for x in row)))
    last_col = chr(64 + len(rows[0])) if len(rows[0]) <= 26 else "Z"
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
            'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
            f'<autoFilter ref="A1:{last_col}{len(rows)}"/>'
            '<cols><col min="1" max="1" width="20" customWidth="1"/>'
            '<col min="2" max="2" width="14" customWidth="1"/>'
            '<col min="3" max="3" width="13" customWidth="1"/>'
            '<col min="4" max="4" width="50" customWidth="1"/>'
            '<col min="5" max="5" width="32" customWidth="1"/>'
            '<col min="6" max="6" width="30" customWidth="1"/>'
            '<col min="7" max="7" width="58" customWidth="1"/>'
            '<col min="8" max="8" width="42" customWidth="1"/>'
            '</cols><sheetData>' + "".join(body) + '</sheetData></worksheet>')


def write_xlsx(path, sheets):
    content_types = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + ''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, len(sheets)+1)) + '</Types>')
    workbook = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        + ''.join(f'<sheet name="{html.escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i, (name, _) in enumerate(sheets, 1))
        + '</sheets></workbook>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships" Target="xl/workbook.xml"/>'
        '</Relationships>')
    wb_rels = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + ''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets)+1)) + '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as book:
        book.writestr("[Content_Types].xml", content_types)
        book.writestr("_rels/.rels", rels)
        book.writestr("xl/workbook.xml", workbook)
        book.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        for i, (_, rows) in enumerate(sheets, 1):
            book.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows))


old, new = routes(OLD), routes(NEW)
records = []
for path in sorted(set(old) | set(new)):
    before, after = old.get(path), new.get(path)
    if before is None:
        change, item = "New API", after
    elif after is None:
        change, item = "Removed API", before
    elif class_block(OLD, before["source"], before["view"]) != class_block(NEW, after["source"], after["view"]):
        change, item = "Changed existing API", after
    else:
        continue
    detail, files, why = change_details("/" + path, item)
    records.append([change, item["module"], item["methods"], "/" + path, purpose(item), item["view"], detail, why, files, test_focus(change, item)])

headers = ["Change type", "API area", "HTTP method(s)", "Endpoint", "Feature / handler", "View class", "What changed / added", "Why changed", "Changed or added files", "QA test focus"]
summary = [
    ["API change audit", "master → main"],
    ["Generated (UTC)", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")],
    ["Branch divergence", git("rev-list", "--left-right", "--count", f"{OLD}...{NEW}").strip() + " (master-only, main-only commits)"],
    ["New API routes", sum(r[0] == "New API" for r in records)],
    ["Changed existing API routes", sum(r[0] == "Changed existing API" for r in records)],
    ["Removed API routes", sum(r[0] == "Removed API" for r in records)],
    ["Scope", "Direct Django urlpatterns mapped to views.Class.as_view(); a changed existing API means its implementation class differs between refs."],
    ["Test note", "Methods are read from the view class in main. Verify environment configuration and external-provider credentials before integration tests."],
]
write_xlsx(ROOT / "main_into_master_api_change_audit.xlsx", [("Summary", summary), ("API inventory", [headers] + records)])
with (ROOT / "main_into_master_api_change_audit_detailed.csv").open("w", newline="", encoding="utf-8-sig") as csv_file:
    csv.writer(csv_file).writerows([headers] + records)
print(f"Wrote {len(records)} API change rows")
