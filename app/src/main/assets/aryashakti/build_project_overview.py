"""Generate an evidence-based AryaShakti project handover overview."""
import ast
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "ARYASHAKTI_PROJECT_OVERVIEW.md"
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "static", "media", "logs"}


def read(relative_path):
    path = ROOT / relative_path
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return ""


def python_files():
    return [
        path for path in ROOT.rglob("*.py")
        if not any(part in SKIP_DIRS for part in path.parts)
    ]


def requirements():
    text = "\n".join(read(name) for name in ("requirements.txt", "requirements.cleaned.txt", "require.txt"))
    names = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)", line)
        if match:
            names.add(match.group(1).lower())
    return names


def settings_apps():
    text = read("Project/settings.py")
    match = re.search(r"INSTALLED_APPS\s*=\s*\[(.*?)\]", text, re.S)
    if not match:
        return []
    return re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))


def url_prefixes():
    text = read("Project/urls.py")
    return re.findall(
        r"path\(\s*['\"]([^'\"]*)['\"]\s*,\s*include\(['\"]([^'\"]+)['\"]",
        text,
    )


def direct_routes():
    routes = []
    for path in ROOT.rglob("urls.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for route, target in re.findall(
            r"path\(\s*['\"]([^'\"]*)['\"]\s*,\s*([^,\n]+)", text
        ):
            if "include" not in target:
                routes.append((str(path.relative_to(ROOT)), route, target.strip()))
    return routes


def model_inventory():
    result = Counter()
    examples = []
    for path in ROOT.rglob("models.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        classes = []
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            is_model = any(
                isinstance(base, ast.Name) and base.id in {"Model", "BaseModel"}
                or isinstance(base, ast.Attribute) and base.attr in {"Model", "BaseModel"}
                for base in node.bases
            )
            if is_model:
                classes.append(node.name)
        if classes:
            app = path.parent.name
            result[app] += len(classes)
            examples.extend(f"{app}.{name}" for name in classes[:8])
    return result, examples


def env_vars():
    text = read("Project/settings.py")
    names = set(re.findall(r"os\.environ(?:\.get)?\(\s*['\"]([A-Z0-9_]+)", text))
    names.update(re.findall(r"os\.environ\[['\"]([A-Z0-9_]+)['\"]\]", text))
    return sorted(names)


def has_any(text, values):
    lowered = text.lower()
    return any(value.lower() in lowered for value in values)


def file_list(directory, suffix=None):
    path = ROOT / directory
    if not path.exists():
        return []
    items = []
    for child in sorted(path.iterdir()):
        if child.name.startswith("."):
            continue
        if suffix and child.suffix != suffix:
            continue
        items.append(child.name)
    return items


def bullets(items, empty="Not detected"):
    return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"


def generate():
    settings = read("Project/settings.py")
    requirements_set = requirements()
    apps = settings_apps()
    prefixes = url_prefixes()
    routes = direct_routes()
    model_counts, model_examples = model_inventory()
    variables = env_vars()
    all_python = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in python_files())
    route_files = sorted({path for path, _, _ in routes})
    api_prefix_lines = [f"`/{prefix}` -> `{module}`" for prefix, module in prefixes]
    app_names = [app for app in apps if "." not in app or app.split(".")[0] in {"django", "rest_framework", "drf_yasg", "storages", "import_export", "django_crontab", "corsheaders", "pgvector"}]
    integrations = []
    integration_map = {
        "Razorpay": ["razorpay", "RAZORPAY"],
        "Firebase / FCM": ["firebase_admin", "firebase_token"],
        "Google Pub/Sub": ["pubsub_v1", "PubSubListener"],
        "SMS / OTP providers": ["send_sms", "send_smsv2", "OTP_VERIFY_URL"],
        "ONNX sentence embeddings": ["onnxruntime", "advisory_embeddings", "pgvector"],
        "Azure / cloud storage": ["django-storages", "azure", "S3Boto3Storage"],
        "OpenAI / generative AI": ["openai", "google-genai"],
        "PAMS / bank validation": ["pams", "PAMS"],
    }
    for name, signals in integration_map.items():
        if has_any(all_python + settings, signals):
            integrations.append(name)

    background = []
    if "celery" in requirements_set or (ROOT / "Project/celery.py").exists():
        background.append("Celery tasks are configured in `Project/celery.py` and `libraries/celery_task.py`.")
    if "django-crontab" in requirements_set or "CRONJOBS" in settings:
        background.append("Django crontab jobs are declared as `CRONJOBS` in `Project/settings.py`.")
    if "ThreadPoolExecutor" in all_python:
        background.append("Several views/services use in-process thread pools for notifications and parallel work.")
    if "pubsub" in all_python.lower():
        background.append("Pub/Sub listeners are available through the management-command/listener modules.")

    important_apis = [
        "`POST /api/v1/auth/send-otp` and `POST /api/v1/auth/otp/verify`: login OTP and token issuance.",
        "`POST /api/v1/auth/signup` and `POST /api/v1/auth/create_farmer`: user creation flows.",
        "`/api/farm_list_admin/`: organization/admin farm listing.",
        "`/api/v1/payment/`: orders, subscriptions, Razorpay webhooks, and payment services.",
        "`/api/v1/record/`: activity, task, training, and advisory-related APIs.",
        "`/api/v1/verify/`: document, boundary, Aadhaar, and verification workflows.",
        "`/api/v1/farm_category/`, `/api/v1/insurance/`, `/api/v1/procurement/`, and `/api/v1/survey/`: domain modules exposed under versioned routes.",
    ]

    overview = f"""# AryaShakti Project Overview

Generated from the checked-in source by `build_project_overview.py`. This document is a static handover aid; live role permissions, environment values, external credentials, and database contents must be verified in the target environment.

## 1. What the project does
AryaShakti is a Django/ Django REST Framework backend for agricultural operations. It manages farmers, farms, organizations, crops, activities, subscriptions, payments, advisories, procurement, insurance, verification, notifications, and supporting admin workflows.

## 2. Technology stack
- Python with Django and Django REST Framework.
- PostgreSQL/PostGIS-style database configuration through `Project/settings.py`.
- Redis is declared in Docker Compose for asynchronous/background services.
- Gunicorn serves the API in the Docker image; WhiteNoise serves static assets.
- Celery, Django crontab, Firebase Admin, Razorpay, Google Pub/Sub, ONNX Runtime, pgvector, and cloud storage packages are present in the project dependencies.
- Swagger/ReDoc schemas are exposed from `Project/urls.py`.

## 3. Project structure
- `Project/`: settings, root URLs, WSGI, Celery, storage configuration.
- `app_farm/`: core farmers, farms, organizations, authentication, legacy APIs, and services.
- `recordActivity/`: activities, tasks, training, advisory embeddings, and semantic search.
- `payment/`, `subscription_service/`: payments, packages, subscriptions, and service balances.
- `verification/`, `insurance/`, `procurement/`: domain workflows and external integrations.
- `core/`: shared models, permissions, base views, and management commands.
- `libraries/`: integration clients and reusable service helpers.
- `templates/`, `static/`, `media/`, `logs/`: presentation, assets, uploaded/generated files, and logs.
- `Dockerfile`, `docker-compose.yml`, and `docker-compose2.yml`: container and local service definitions.

## 4. Main Django applications
The configured Django applications include:
{bullets(app_names)}

Model counts statically detected by app:
{bullets([f"`{app}`: {count} model classes" for app, count in sorted(model_counts.items())])}

## 5. API architecture
- Root API prefixes are defined in `Project/urls.py`.
{bullets(api_prefix_lines)}
- Legacy APIs are generally under `/api/` and newer service APIs under `/api/v1/`.
- Views use `APIView`, DRF serializers/validators, shared `BaseView` classes, and direct function-based views.
- Route source files detected: {len(route_files)}; direct route declarations detected: {len(routes)}.
- Swagger and ReDoc are available under `/swagger/` and `/redoc/` when enabled by deployment configuration.

## 6. Authentication
- The project-wide DRF default is `CustomTokenAuthentication`.
- Tokens are stored in the `AuthenticationToken` model and are normally sent as `Authorization: Token <key>`.
- `CustomTokenAuthentication` validates the token, checks active/deleted user state, and returns the user/token pair.
- Some legacy APIs use a `secret-key` query/body parameter instead of the DRF token flow.
- `BaseView` applies `CustomTokenAuthentication` and `IsAuthenticated`; `BaseViewWithoutAuthentication` is used for public flows such as OTP send/verify.
- API-level role permission enforcement is present in the data model but the check in `app_farm/authentication.py` is currently commented out; verify effective permissions before relying on role restrictions.

## 7. User roles
The main role names referenced by code are:
{bullets(["`Sponsor`", "`Admin`", "`Farmer`", "`BD`", "`BDManager`", "`ZONAL_HEAD`"])}

Roles are database-backed through `app_farm.user_roles`; actual role rows and permissions must be queried in the target database.

## 8. Important business flows
- OTP login: send OTP, verify OTP, update login/device state, and issue an `AuthenticationToken` for existing users.
- Signup/farmer creation: validate secret key and registration data, create a user with verified state, assign a role, and issue a token.
- Farm operations: create, list, update, filter, and administer farms by organization, location, crop, health, and stress state.
- Subscription/payment: process orders, create `UserSubscription`/`UserService` records, deduct service validity, and handle Razorpay callbacks.
- Activities/training: create and manage farm activities, tasks, subtasks, training, and execution records.
- Advisory search: create embeddings for crop/disease advisories and use pgvector similarity search.
- Verification/insurance/procurement: connect domain records to external validation, insurance, procurement, and document workflows.

## 9. Database architecture
- Database connection values are supplied through environment variables and configured in `Project/settings.py`.
- Django models and migrations define the application schema; PostgreSQL/PostGIS features are used by the project.
- `recordActivity` also contains pgvector fields/migrations for advisory embeddings.
- Key model areas include users/roles, organizations/farms, activities, payments/subscriptions, verification, procurement, insurance, CMS, and notifications.
- Example model classes detected: {", ".join(f"`{item}`" for item in model_examples[:25])}.

## 10. External integrations
{bullets(integrations)}

Integration credentials and endpoint configuration are environment-driven; never place real values in this generated document or source control.

## 11. Background processing
{bullets(background)}
- Docker Compose declares a Django API service, Redis, and a Celery worker with concurrency 2.
- The Docker image starts migrations/collectstatic, a PMS listener process, and Gunicorn.
- Inspect `Project/settings.py`, `Project/celery.py`, `libraries/celery_task.py`, `crons/`, and `core/management/commands/` before changing schedules or worker counts.

## 12. File handling
- Static files are collected into `staticfiles/` and served/configured through WhiteNoise.
- Media and uploaded files use Django storage settings; `Project/storage_backends.py` configures cloud-backed storage support.
- Upload and document workflows are spread across verification, procurement, CMS, farm, and record activity modules.
- Review file size/type validation and external signed-URL behavior before changing upload APIs.

## 13. Error handling & logging
- DRF uses `app_farm.custom_exception.custom_exception_handler` as the configured exception handler.
- Many older views catch broad exceptions and return project-specific error payloads; inspect the endpoint before assuming standard DRF errors.
- Application logs are written to `logs/` in local/container configurations, while Kubernetes deployments primarily expose stdout/stderr to centralized logging.
- API responses commonly include status, message, data, and internal error codes.

## 14. Configuration / environment variables
The settings module reads these variable names without exposing their values:
{bullets([f"`{name}`" for name in variables])}

Use `.env`, deployment secret/config objects, or the approved configuration system. Do not commit credentials, tokens, certificates, or database passwords.

## 15. Important services
- `app_farm.services.auth`: OTP, signup, farmer creation, and authentication token flows.
- `app_farm.services.farmer`: farmer-facing role and farm services.
- `app_farm.services.organizations`: organization workflows.
- `libraries/`: SMS, Firebase, payment, storage, Pub/Sub, AI, and domain-provider clients.
- `recordActivity.vector_files.advisory_embeddings`: lazy-loaded ONNX embedding service.
- `core.views.BaseView`: shared authenticated API behavior.

## 16. Important APIs
{bullets(important_apis)}

Confirm exact request schemas in the endpoint validator and serializer before testing. Legacy and versioned endpoints can have different token/secret-key requirements.

## 17. Typical request flow
1. The request enters a root URL prefix in `Project/urls.py`.
2. Django resolves the app route to a view or service API.
3. DRF authentication runs when the view inherits `BaseView` or declares authentication classes.
4. A validator checks query/body data.
5. The view queries or mutates Django models and may call an external service.
6. A serializer builds the response, or a project response helper returns the standard envelope.
7. Exceptions are handled by local `try/except` blocks or the configured DRF exception handler.
8. Logs go to application stdout/stderr and/or configured log files.

## 18. Things to understand first
- Read `Project/settings.py`, `Project/urls.py`, `core/views.py`, and `app_farm/authentication.py` first.
- Understand the difference between `/api/` legacy routes and `/api/v1/` service routes.
- Trace users, roles, organizations, farms, subscriptions, and `AuthenticationToken` together.
- Inspect validators and serializers beside every API; many business rules are implemented there rather than in models.
- Verify environment variables and external credentials before running payment, SMS, Firebase, storage, or Pub/Sub flows.
- Treat broad exception handlers and commented permission checks as review points.
- Query live role rows and permissions before concluding that a role can or cannot call an endpoint.
- Confirm deployment image/branch, Gunicorn worker count, database target, and migration state before debugging production-like behavior.
"""
    OUTPUT.write_text(overview, encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"Detected {len(app_names)} configured apps, {len(routes)} direct routes, and {sum(model_counts.values())} model classes.")


if __name__ == "__main__":
    generate()
