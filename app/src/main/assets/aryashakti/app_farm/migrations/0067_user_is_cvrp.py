from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_farm', '0066_user_can_edit_org_details'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_cvrp',
            field=models.BooleanField(default=False),
        ),
    ]