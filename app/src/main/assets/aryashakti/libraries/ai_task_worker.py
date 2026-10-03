# Import task function
from datetime import date, timedelta
from recordActivity.models import SmartFarms, ProjectTaskUser, ProjectTask
from pop_manage.models import ActivityPOP

def assign_farm_tasks():
    today = date.today()
    farms = SmartFarms.objects.filter(next_run=today).all()  # Get all SmartFarm records
    
    for farm in farms:
        farm_instance = farm.farm  # Use farm instance from SmartFarm
        if not farm_instance.sowing_date:
            continue  # Skip farms without a sowing date

        days_after_sowing = (today - farm_instance.sowing_date.date()).days  # Calculate DAS

        # Get relevant activity tasks based on DAS range
        activities = ActivityPOP.objects.filter(
            crop=farm_instance.crop, 
            from_das__lte=days_after_sowing, 
            to_das__gte=days_after_sowing
        )

        assigned_tasks = []
        for activity in activities:
            # Check if task already exists for today
            task_exists = ProjectTaskUser.objects.filter(
                project_task__activity_record=activity.activity_records_id,
                farm=farm_instance,
                project_task__task_type="activity",
                project_task__project=farm_instance.project,
                project_task__created_at=today
            ).exists()
            
            if task_exists:
                print(f"Task '{activity.activity_records_id.name}' already exists for Farm ID: {farm_instance.farm_id}, skipping.")
                continue

            project_task, created = ProjectTask.objects.get_or_create(
                task_name=activity.activity_records_id.name,
                project=farm_instance.project,  # Assuming SmartFarm is linked to a Project
                task_type="activity",
                activity_record=activity.activity_records_id
            )

            # Assign task to a user (assuming farmer is the assigned user)
            ProjectTaskUser.objects.get_or_create(
                assigned_to=farm_instance.farmer, 
                project_task=project_task, 
                farm=farm_instance,
                status="pending"
            )

            print(f"Assigned task '{project_task.task_name}' to Farmer ID: {farm_instance.farmer.id} for Farm ID: {farm_instance.farm_id}")

        # Update next_run date for the farm
        farm.next_run = today + timedelta(days=7)  # Adjust the next run date logic as needed
        farm.save()




def assign_farm_tasks_test():
    today = date.today()
    farms = SmartFarms.objects.filter(next_run=today).all()  # Get all SmartFarm records
    project_id=1
    # print(farms)
    for farm in farms:
        farm_instance = farm.farm  # Use farm instance from SmartFarm
        if not farm_instance.sowing_date:
            continue  # Skip farms without a sowing date

        days_after_sowing = (today - farm_instance.sowing_date.date()).days  # Calculate DAS

        # Get relevant activity tasks based on DAS range
        activities = ActivityPOP.objects.filter(
            crop=farm_instance.crop_id, 
            from_das__lte=days_after_sowing, 
            to_das__gte=days_after_sowing
        )

        # print(activities)

        if not activities.exists():  # If no activities found, check sowing date
            print(farm_instance.sowing_date.date())
            # if farm_instance.sowing_date.date() == today:
            print(f"Assigning tasks for the next 7 days for Farm ID: {farm_instance.id}")
            for day_offset in range(1, 8):  # Assign tasks for next 7 days
                future_day = today + timedelta(days=day_offset)
                pop_activities = ActivityPOP.objects.filter(
                    crop=farm_instance.crop_id,
                    from_das__lte=day_offset, 
                    to_das__gte=day_offset
                )
                for pop_activity in pop_activities:
                    project_task, created = ProjectTask.objects.get_or_create(
                        task_name=pop_activity.activity_records_id.name,
                        project_id=project_id,
                        task_type="activity",
                        activity_record=pop_activity.activity_records_id
                    )

                    print(farm_instance)
                    ProjectTaskUser.objects.get_or_create(
                        assigned_to=farm_instance.added_by,
                        project_task=project_task,
                        farm=farm_instance,
                        status="pending"
                    )
                    print(f"Created Task for {future_day}: {project_task.task_name}")
            continue  # Move to the next farm

        assigned_tasks = []
        for activity in activities:
            # Check if task already exists for today
            task_exists = ProjectTaskUser.objects.filter(
                project_task__activity_record=activity.activity_records_id,
                farm=farm_instance,
                project_task__task_type="activity",
                project_task__project_id=project_id,
                project_task__created_at=today
            ).exists()
            
            if task_exists:
                print(f"Task '{activity.activity_records_id.name}' already exists for Farm ID: {farm_instance.id}, skipping.")
                continue

            project_task, created = ProjectTask.objects.get_or_create(
                task_name=activity.activity_records_id.name,
                project_id=project_id,
                task_type="activity",
                activity_record=activity.activity_records_id
            )

            ProjectTaskUser.objects.get_or_create(
                assigned_to=farm_instance.added_by,
                project_task=project_task,
                farm=farm_instance,
                status="pending"
            )

            print(f"Farmer Activity: {activity.activity_records_id.name}, DAS: {days_after_sowing}")
            print(f"Package of Practice for Crop {farm_instance.crop_id.crop_name}: {activity.from_das} to {activity.to_das}")
            print(f"Assigned Task: {project_task.task_name} to Farmer ID: {farm_instance.user.id}")

        # Update next_run date for the processed farm
        farm.next_run = today + timedelta(days=7)  # Adjust the next run date logic as needed
        farm.save()