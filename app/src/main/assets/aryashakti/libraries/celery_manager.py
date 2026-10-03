from libraries.celery_task import celery_test_task, update_farm_boundaries_from_geojson_csv
from celery.result import AsyncResult
from farm_category.models import CelreyTaskStatus


class CeleryManager:

    @staticmethod
    def trigger_test_task(name):
        """
        Trigger celery test task
        """
        task = celery_test_task.delay(name)

        return {
            "task_id": task.id
        }

    @staticmethod
    def get_task_status(task_id):
        """
        Check celery task status
        """
        task = AsyncResult(task_id)

        return {
            "task_id": task_id,
            "status": task.status,
            "result": str(task.result)
        }

    @staticmethod
    def trigger_boundary_update_task(input_csv, batch_size=500):
        task = update_farm_boundaries_from_geojson_csv.delay(input_csv=input_csv, batch_size=batch_size)
        return {
            "task_id": task.id
        }

    @staticmethod
    def get_boundary_update_task_status(task_id):
        job = CelreyTaskStatus.objects.filter(task_id=task_id).first()

        if not job:
            return {
                "task_id": task_id,
                "status": CelreyTaskStatus.STATUS_FAILED,
                "message": "Task not found or not completed yet"
            }

        return {
            "task_id": job.task_id,
            "status": job.status,
            "total_processed": job.total_processed,
            "updated": job.updated_count,
            "inserted": job.inserted_count,
            "skipped": job.skipped_count,
            "failed": job.failed_count,
            "result_files": job.result_files,
            "error_message": job.error_message,
        }