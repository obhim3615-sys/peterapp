"""Build a role-focused API, authentication, and database access CSV."""
import ast
import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_PREFIX = "role_api_access_audit"

KNOWN_ROLES = {
    "Sponsor": "Sponsor",
    "Admin": "Admin",
    "Farmer": "Farmer",
    "BD": "BD",
    "BDManager": "BDManager",
    "ZONAL_HEAD": "ZONAL_HEAD",
}

URL_MODULES = {"Project.urls"}
MODEL_CACHE = {}
SOURCE_CACHE = {}


def module_path(module):
    """Resolve a dotted Python module to its source file in this repository."""
    candidate = ROOT / Path(*module.split("."))
    if candidate.with_suffix(".py").exists():
        return candidate.with_suffix(".py")
    init_file = candidate / "__init__.py"
    return init_file if init_file.exists() else None


def module_from_file(path):
    relative = path.relative_to(ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def source_for(module):
    if module not in SOURCE_CACHE:
        path = module_path(module)
        SOURCE_CACHE[module] = (path, path.read_text(encoding="utf-8") if path else "")
    return SOURCE_CACHE[module]


def joined_path(prefix, suffix):
    value = "/".join(part.strip("/") for part in (prefix, suffix) if part)
    return "/" + value if value else "/"


def resolve_module(value, aliases, current_module):
    value = value.strip().strip("'\"")
    if value in aliases:
        return aliases[value]
    if "." in value:
        return value
    package = current_module.rsplit(".", 1)[0]
    return f"{package}.{value}"


def imports(text, current_module):
    aliases = {}
    for module, alias in re.findall(
        r"from\s+([\w.]+)\s+import\s+(?:\w+\s+as\s+)?([A-Za-z_]\w*)", text
    ):
        imported = re.search(
            rf"from\s+{re.escape(module)}\s+import\s+([A-Za-z_]\w*)(?:\s+as\s+{re.escape(alias)})?",
            text,
        )
        if imported:
            name = imported.group(1)
            if module.startswith("."):
                base = current_module.rsplit(".", 1)[0]
                module_name = f"{base}.{module.lstrip('.')}.{name}".replace("..", ".")
            else:
                module_name = f"{module}.{name}"
            aliases[alias] = module_name
    for alias, module in re.findall(
        r"from\s+([\w.]+)\s+import\s+\w+\s+as\s+([A-Za-z_]\w*)", text
    ):
        aliases[alias] = module
    for module, alias in re.findall(
        r"from\s+([\w.]+)\s+import\s+([A-Za-z_]\w*)", text
    ):
        if alias not in aliases:
            aliases[alias] = f"{module}.{alias}"
    return aliases


def get_ast(text):
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def node_source(text, node):
    lines = text.splitlines(keepends=True)
    end = getattr(node, "end_lineno", node.lineno)
    return "".join(lines[node.lineno - 1:end])


def find_definition(module, name):
    path, text = source_for(module)
    tree = get_ast(text)
    if not tree:
        return None, ""
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return path, node_source(text, node)
    return path, ""


def scan_urls(module, prefix="", visited=None):
    visited = visited or set()
    key = (module, prefix)
    if key in visited:
        return []
    visited.add(key)
    path, text = source_for(module)
    if not path:
        return []

    aliases = imports(text, module)
    routes = []
    include_pattern = re.compile(
        r"(?:path|re_path)\(\s*['\"]([^'\"]*)['\"]\s*,\s*include\(([^)]+)\)"
    )
    for suffix, target in include_pattern.findall(text):
        target = target.strip()
        if target.startswith(("'", '"')):
            child_module = resolve_module(target, aliases, module)
        else:
            child_module = resolve_module(target, aliases, module)
        routes.extend(scan_urls(child_module, joined_path(prefix, suffix), visited))

    direct_pattern = re.compile(
        r"(?:path|re_path)\(\s*['\"]([^'\"]*)['\"]\s*,\s*"
        r"([A-Za-z_]\w*)\.([A-Za-z_]\w*)(?:\.as_view\(\))?"
    )
    for suffix, alias, view in direct_pattern.findall(text):
        view_module = aliases.get(alias, f"{module.rsplit('.', 1)[0]}.{alias}")
        if view_module.endswith(".views") or view_module.endswith(".api"):
            source_module = view_module
        else:
            source_module = view_module
        routes.append(
            {
                "endpoint": joined_path(prefix, suffix),
                "url_module": module,
                "url_file": str(path.relative_to(ROOT)),
                "view": view,
                "view_module": source_module,
            }
        )
    return routes


def humanize(value):
    value = value.replace("_", " ")
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    return value.strip().capitalize()


def class_methods(source):
    tree = get_ast(source)
    if not tree:
        return "Verify"
    methods = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.lower() in {
            "get", "post", "put", "patch", "delete", "head", "options",
        }:
            methods.append(node.name.upper())
    return ", ".join(dict.fromkeys(methods)) or "Verify"


def role_terms(role):
    value = role.lower()
    return {value, value.replace("_", ""), KNOWN_ROLES.get(role, role).lower()}


def explicit_roles(source):
    found = set()
    lowered = source.lower()
    role_markers = "user_role|role_name|user_type|slugs\[['\"]user_roles"
    if not re.search(role_markers, lowered):
        return found
    for role, role_value in KNOWN_ROLES.items():
        terms = {role.lower(), role_value.lower()}
        if any(re.search(rf"\b{re.escape(term)}\b", lowered) for term in terms):
            found.add(role)
    return found


def authentication_info(source):
    lowered = source.lower()
    if "allowany" in lowered or "baseviewwithoutauthentication" in lowered:
        return "Public / AllowAny or no explicit authentication"
    if "customtokenauthentication" in lowered or "baseview" in lowered:
        return "Authenticated: CustomTokenAuthentication + IsAuthenticated"
    if "tokenauthentication" in lowered:
        return "Authenticated: DRF TokenAuthentication"
    if "isauthenticated" in lowered:
        return "Authenticated: IsAuthenticated"
    return "No explicit authentication found; verify project defaults"


def token_access(source):
    access = []
    if "customtokenauthentication" in source.lower() or "baseview" in source.lower():
        access.append("Authorization: Token <AuthenticationToken.key>")
    if "secret-key" in source.lower() or "secret_key" in source.lower():
        access.append("secret-key query/body parameter")
    if "bearer" in source.lower() or "jwt" in source.lower():
        access.append("Bearer/JWT token reference")
    if not access:
        access.append("No token input detected")
    return "; ".join(dict.fromkeys(access))


def input_fields(source):
    patterns = [
        r"request\.(?:GET|POST|data|query_params)\.get\(\s*['\"]([^'\"]+)",
        r"(?:req_data|request\.data|request\.GET)\[\s*['\"]([^'\"]+)['\"]\s*\]",
    ]
    fields = []
    for pattern in patterns:
        fields.extend(re.findall(pattern, source))
    return ", ".join(dict.fromkeys(fields)) or "Not statically identified"


def model_inventory():
    models = {}
    for path in ROOT.glob("**/models.py"):
        if any(part in {".venv", "site-packages", "migrations"} for part in path.parts):
            continue
        app = path.parent.name
        text = path.read_text(encoding="utf-8")
        tree = get_ast(text)
        if not tree:
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(
                isinstance(base, ast.Name) and base.id == "Model"
                or isinstance(base, ast.Attribute) and base.attr == "Model"
                for base in node.bases
            ):
                continue
            body = node_source(text, node)
            table_match = re.search(r"db_table\s*=\s*['\"]([^'\"]+)", body)
            table = table_match.group(1) if table_match else f"{app}_{node.name.lower()}"
            models[node.name] = {
                "table": table,
                "purpose": humanize(node.name),
                "source": str(path.relative_to(ROOT)),
            }
    return models


def database_details(source, models):
    operations = defaultdict(set)
    for model_name, metadata in models.items():
        patterns = [
            rf"\b{re.escape(model_name)}\.objects\.(\w+)",
            rf"\bmodels\.{re.escape(model_name)}\.objects\.(\w+)",
        ]
        for pattern in patterns:
            for operation in re.findall(pattern, source):
                operations[model_name].add(operation)
        if re.search(rf"\b{re.escape(model_name)}\s*\(", source):
            operations[model_name].add("instantiate")
    for name, ops in re.findall(r"\b([A-Za-z_]\w*)\.objects\.(filter|get|create|all|update|delete|bulk_create)\b", source):
        if name in models:
            operations[name].add(ops)
    if not operations:
        return "No model access statically identified", "No database operation statically identified", "Verify view dependencies"
    model_text = []
    operation_text = []
    purpose_text = []
    for name in sorted(operations):
        metadata = models[name]
        model_text.append(f"{name} ({metadata['table']})")
        operation_text.append(f"{name}: {', '.join(sorted(operations[name]))}")
        purpose_text.append(f"{name}: {metadata['purpose']}")
    return "; ".join(model_text), "; ".join(operation_text), "; ".join(purpose_text)


def role_match(role, source):
    explicit = explicit_roles(source)
    if role == "all":
        return True, "All roles selected"
    if explicit:
        if role in explicit:
            return True, f"Explicit role reference: {', '.join(sorted(explicit))}"
        return False, "Explicitly references another role"
    if "allowany" in source.lower() or "baseviewwithoutauthentication" in source.lower():
        return True, "Public endpoint; role is not restricted"
    return True, "Authenticated endpoint; no role-specific check found"


def collect_rows(role):
    models = model_inventory()
    rows = []
    for route in scan_urls("Project.urls"):
        source_path, source = find_definition(route["view_module"], route["view"])
        if not source:
            continue
        include, match_reason = role_match(role, source)
        if not include:
            continue
        db_models, db_operations, db_purpose = database_details(source, models)
        rows.append(
            [
                role,
                match_reason,
                route["endpoint"],
                class_methods(source),
                humanize(route["view"]),
                route["view"],
                str(source_path.relative_to(ROOT)) if source_path else route["view_module"],
                authentication_info(source),
                token_access(source),
                input_fields(source),
                db_models,
                db_operations,
                db_purpose,
                "Inspect serializer and response branches in the evidence file.",
                route["url_file"],
            ]
        )
    return sorted(rows, key=lambda row: row[2])


def main():
    print("Available roles:")
    for role in KNOWN_ROLES:
        print(f"  - {role}")
    print("  - all")
    selected = input("Enter a role to audit [all]: ").strip()
    role = selected or "all"
    if role.lower() == "all":
        role = "all"
    else:
        match = next((name for name in KNOWN_ROLES if name.lower() == role.lower()), None)
        if not match:
            raise SystemExit(f"Unknown role: {selected}. Choose one of: {', '.join(KNOWN_ROLES)}")
        role = match

    rows = collect_rows(role)
    suffix = "all" if role == "all" else re.sub(r"[^a-z0-9]+", "_", role.lower()).strip("_")
    output = ROOT / f"{OUTPUT_PREFIX}_{suffix}.csv"
    headers = [
        "Selected role",
        "Role relevance / access basis",
        "Endpoint",
        "HTTP methods",
        "Feature",
        "View class/function",
        "View source",
        "Authentication",
        "Token / access required",
        "Request inputs detected",
        "Database models / tables",
        "Database operations",
        "Database purpose",
        "Response / review note",
        "URL source",
    ]
    with output.open("w", newline="", encoding="utf-8-sig") as csv_file:
        csv.writer(csv_file).writerows([headers] + rows)
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
