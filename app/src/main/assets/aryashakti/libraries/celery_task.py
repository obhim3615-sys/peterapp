# from celery import shared_task
# import time


# from broadcast.models import NotificationLog
# from libraries.noms import NoMS

from celery import shared_task
from django.db import close_old_connections, transaction
from django.conf import settings
from broadcast.models import NotificationLog
from app_farm.models import farm
from farm_category.models import FarmsCategory, CelreyTaskStatus
from libraries.noms import NoMS
import logging
import time
import csv
import io
import json
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def celery_test_task(self, name):
    print(f"Celery started for {name}")

    time.sleep(5)

    print(f"Celery finished for {name}")

    return f"Hello {name}"




# @shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 3})
# def send_sms_task(self, phone, params, doms_id, language, sender_id, receiver_id, sms_template_id):

#     try:
#         noms = NoMS()
#         print("initialised NoMS")

#         status = noms.send_smsv2(
#             0,
#             "TRANSACTIONAL",
#             "User",
#             {
#                 "parameterMap": params,
#                 "domsTemplateId": doms_id,
#                 "sendTo": phone,
#                 "sendFrom": "aryaMK"
#             },
#             language
#         )

#         log = NotificationLog.objects.create(
#             sender_id=sender_id,
#             receiver_id=receiver_id,
#             sms_template_id=sms_template_id,
#             receiver_phone=phone,
#             status="pending"
#         )

#         if status.get("success"):
#             log.status = "success"
#         else:
#             log.status = "failed"

#         log.response = status
#         log.save()

#     except Exception as e:
#         raise e



@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={'max_retries': 3}
)
def send_sms_task(self, phone, params, doms_id, language, sender_id, receiver_id, sms_template_id):

    # 🔹 Ensure DB connection is fresh (important for long-running workers)
    close_old_connections()

    # 🔹 Create log FIRST (so we never lose trace)
    log = NotificationLog.objects.create(
        sender_id=sender_id,
        receiver_id=receiver_id,
        sms_template_id=sms_template_id,
        receiver_phone=phone,
        status="pending",
        response={}
    )

    try:
        logger.info(f"[SMS TASK START] phone={phone}, task_id={self.request.id}")

        noms = NoMS()

        status = noms.send_smsv2(
            0,
            "TRANSACTIONAL",
            "User",
            {
                "parameterMap": params,
                "domsTemplateId": doms_id,
                "sendTo": phone,
                "sendFrom": "aryaMK"
            },
            language
        )

        # 🔹 Update log based on response
        if status and status.get("success"):
            log.status = "success"
        else:
            log.status = "failed"

        log.response = status or {}

        logger.info(f"[SMS TASK SUCCESS] phone={phone}, status={log.status}")

    except Exception as e:
        # 🔹 Capture failure properly
        log.status = "failed"
        log.response = {"error": str(e)}

        logger.error(
            f"[SMS TASK ERROR] phone={phone}, task_id={self.request.id}, error={str(e)}"
        )

        # 🔹 Re-raise so Celery retry works
        raise e

    finally:
        # 🔹 Always save log
        log.save()

        # 🔹 Clean DB connections again (good practice)
        close_old_connections()

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={'max_retries': 3}
)
def process_device_management_action(self, action, user_id, device_id, payload=None):

    from django.utils import timezone
    from app_farm import models as app_models

    payload = payload or {}
    action = str(action or '').strip().lower()
    device_id = str(device_id or '').strip()

    if not device_id:
        logger.warning(f"[DEVICE TASK] empty device_id, action={action}, user_id={user_id}")
        return

    try:
        try:
            user_obj = app_models.user.objects.get(id=user_id)
        except app_models.user.DoesNotExist:
            logger.warning(f"[DEVICE TASK] user_id={user_id} not found, action={action}")
            return

        if action == 'login':
            device_type = payload.get('device_type', 'mobile')
            model = payload.get('model', '')
            os = payload.get('os', '')
            device_name = payload.get('device_name', device_id)
            now = timezone.now()

            with transaction.atomic():
                existing = app_models.UserDeviceManagement.objects.select_for_update().filter(
                    user=user_obj,
                    device_id__iexact=device_id
                ).order_by('-id').first()

                if existing:
                    existing.device_id = device_id
                    existing.device_name = device_name
                    existing.device_type = device_type
                    existing.device_os = os
                    existing.device_model = model
                    existing.is_active = True
                    existing.last_used = now
                    existing.save(update_fields=[
                        'device_id', 'device_name', 'device_type', 'device_os',
                        'device_model', 'is_active', 'last_used', 'updated_at'
                    ])
                else:
                    app_models.UserDeviceManagement.objects.create(
                        user=user_obj,
                        device_id=device_id,
                        device_name=device_name,
                        device_type=device_type,
                        device_os=os,
                        device_model=model,
                        is_active=True,
                        last_used=now,
                    )

            logger.info(f"[DEVICE TASK] login recorded user_id={user_id} device_id={device_id}")

        elif action == 'logout':
            app_models.UserDeviceManagement.objects.filter(
                user=user_obj,
                device_id__iexact=device_id
            ).update(is_active=False)
            logger.info(f"[DEVICE TASK] logout recorded user_id={user_id} device_id={device_id}")

    except Exception as e:
        logger.error(
            f"[DEVICE TASK ERROR] task_id={self.request.id}, action={action}, "
            f"user_id={user_id}, device_id={device_id}, error={str(e)}"
        )
        raise e


def _build_request_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _convert_geojson(data):
    features = []

    source_features = []
    if isinstance(data, list):
        source_features = data
    elif isinstance(data, dict):
        source_features = data.get("features", [])

    for feature in source_features:
        geometry = feature.get("geometry") if isinstance(feature, dict) else None
        if not geometry:
            continue

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": geometry.get("type"),
                    "coordinates": geometry.get("coordinates"),
                },
            }
        )

    return features


def _boundary_exists(existing_boundary):
    if existing_boundary is None:
        return False

    if isinstance(existing_boundary, str):
        value = existing_boundary.strip()
        return value not in ("", "{}", "[]", "null", "None")

    if isinstance(existing_boundary, (list, dict)):
        return len(existing_boundary) > 0

    return True


def _normalized_geojson_url(row):
    raw_url = row.get("vid_farm_geojson_url") or row.get("farm_geojson_url") or ""
    url = str(raw_url).strip()
    if not url:
        return ""

    base_url = url.split("?", 1)[0].split("#", 1)[0]
    if not base_url.lower().endswith(".geojson"):
        return f"{url}.geojson"

    return url


def _iter_csv_stream_in_batches(csv_file, batch_size, start_index=1, end_index=None):
    reader = csv.DictReader(csv_file)
    batch = []

    for row_number, row in enumerate(reader, start=1):
        if row_number < start_index:
            continue

        if end_index is not None and row_number > end_index:
            break

        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def _iter_csv_in_batches(csv_path, batch_size, start_index=1, end_index=None):
    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as csv_file:
        yield from _iter_csv_stream_in_batches(csv_file, batch_size, start_index=start_index, end_index=end_index)


def _boundary_from_row(row, session):
    json_data_raw = row.get("json_data")
    if json_data_raw and str(json_data_raw).strip():
        parsed = json.loads(json_data_raw)
        return _convert_geojson(parsed)

    geojson_url = _normalized_geojson_url(row)
    if not geojson_url:
        raise ValueError("Empty geojson url and empty json_data")

    response = session.get(geojson_url, timeout=30)
    response.raise_for_status()
    return _convert_geojson(response.json())


@shared_task(bind=True)
def update_farm_boundaries_from_geojson_csv(
    self,
    input_csv="geojson_data_extracted_test_set.csv",
    batch_size=500,
    start_index=1,
    end_index=None,
    csv_content=None,
    source_name=None,
):
    task_id = str(getattr(self.request, "id", "") or "")
    description = "Boundary update in farm_category from CSV geojson_data/json_data"

    try:
        start_index = int(start_index or 1)
    except (TypeError, ValueError):
        start_index = 1

    if start_index < 1:
        start_index = 1

    try:
        end_index = int(end_index) if end_index not in (None, "") else None
    except (TypeError, ValueError):
        end_index = None

    job_status, _ = CelreyTaskStatus.objects.update_or_create(
        task_id=task_id,
        defaults={
            "description": description,
            "status": CelreyTaskStatus.STATUS_FAILED,
            "input_csv": str(source_name or input_csv),
            "batch_size": int(batch_size),
            "error_message": None,
        },
    )

    batch_size = int(batch_size or 500)
    if batch_size <= 0:
        batch_size = 500

    if csv_content is None:
        csv_path = Path(input_csv)
        if not csv_path.is_absolute():
            csv_path = Path(settings.BASE_DIR) / csv_path

        if not csv_path.exists():
            message = f"CSV file not found: {csv_path}"
            job_status.status = CelreyTaskStatus.STATUS_FAILED
            job_status.error_message = message
            job_status.save(update_fields=["status", "error_message", "updated_at"])
            raise FileNotFoundError(message)

        batch_iterator = _iter_csv_in_batches(csv_path, batch_size, start_index=start_index, end_index=end_index)
    else:
        batch_iterator = _iter_csv_stream_in_batches(
            io.StringIO(csv_content),
            batch_size,
            start_index=start_index,
            end_index=end_index,
        )

    updated_records = []
    inserted_records = []
    skipped_records = []
    failed_records = []

    updated = 0
    inserted = 0
    skipped = 0
    failed = 0

    session = _build_request_session()

    try:
        for batch_no, batch_rows in enumerate(batch_iterator, start=1):
            logger.info("Boundary update batch started: batch=%s records=%s", batch_no, len(batch_rows))

            for row in batch_rows:
                raw_farm_id = row.get("farm_id")
                geojson_url = _normalized_geojson_url(row)

                try:
                    farm_id = int(raw_farm_id)
                except (TypeError, ValueError):
                    failed += 1
                    failed_records.append(
                        {
                            "farm_id": raw_farm_id,
                            "geojson_url": geojson_url,
                            "reason": "Invalid farm_id",
                        }
                    )
                    continue

                try:
                    boundary_data = _boundary_from_row(row, session)

                    with transaction.atomic():
                        farm_category = FarmsCategory.objects.select_for_update().filter(farm_id=farm_id).first()

                        if farm_category:
                            if _boundary_exists(farm_category.boundary):
                                skipped += 1
                                skipped_records.append(
                                    {
                                        "farm_id": farm_id,
                                        "geojson_url": geojson_url,
                                        "reason": "Boundary already exists",
                                    }
                                )
                            else:
                                farm_category.boundary = boundary_data
                                farm_category.save(update_fields=["boundary", "updated_at"])
                                updated += 1
                                updated_records.append(
                                    {
                                        "farm_id": farm_id,
                                        "geojson_url": geojson_url,
                                    }
                                )
                        else:
                            farm_obj = farm.objects.filter(id=farm_id).first()
                            if not farm_obj:
                                skipped += 1
                                skipped_records.append(
                                    {
                                        "farm_id": farm_id,
                                        "geojson_url": geojson_url,
                                        "reason": "Farm does not exist",
                                    }
                                )
                                continue

                            FarmsCategory.objects.create(farm=farm_obj, boundary=boundary_data)
                            inserted += 1
                            inserted_records.append(
                                {
                                    "farm_id": farm_id,
                                    "geojson_url": geojson_url,
                                }
                            )

                except Exception as exc:
                    failed += 1
                    logger.exception("Boundary update failed for farm_id=%s", farm_id)
                    failed_records.append(
                        {
                            "farm_id": farm_id,
                            "geojson_url": geojson_url,
                            "reason": str(exc),
                        }
                    )

            logger.info(
                "Boundary update batch completed: batch=%s updated=%s inserted=%s skipped=%s failed=%s",
                batch_no,
                updated,
                inserted,
                skipped,
                failed,
            )

        task_details = {
            "start_index": start_index,
            "end_index": end_index,
            "updated_records": updated_records,
            "inserted_records": inserted_records,
            "skipped_records": skipped_records,
            "failed_records": failed_records,
        }

        total_processed = updated + inserted + skipped + failed
        final_status = CelreyTaskStatus.STATUS_PASSED if failed == 0 else CelreyTaskStatus.STATUS_FAILED

        job_status.status = final_status
        job_status.total_processed = total_processed
        job_status.updated_count = updated
        job_status.inserted_count = inserted
        job_status.skipped_count = skipped
        job_status.failed_count = failed
        job_status.result_files = task_details
        job_status.error_message = None if failed == 0 else "Some records failed during processing"
        job_status.save(
            update_fields=[
                "status",
                "total_processed",
                "updated_count",
                "inserted_count",
                "skipped_count",
                "failed_count",
                "result_files",
                "error_message",
                "updated_at",
            ]
        )

        return {
            "task_id": task_id,
            "status": job_status.status,
            "total_processed": total_processed,
            "updated": updated,
            "inserted": inserted,
            "skipped": skipped,
            "failed": failed,
            "start_index": start_index,
            "end_index": end_index,
            "task_details": task_details,
        }

    except Exception as exc:
        logger.exception("Boundary update task failed: task_id=%s", task_id)
        job_status.status = CelreyTaskStatus.STATUS_FAILED
        job_status.error_message = str(exc)
        job_status.save(update_fields=["status", "error_message", "updated_at"])
        raise

    finally:
        session.close()
