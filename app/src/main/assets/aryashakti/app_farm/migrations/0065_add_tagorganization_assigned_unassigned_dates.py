from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app_farm", "0064_tagtype_dynamic_tag_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="tagorganization",
            name="tag_assigned_date",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="tagorganization",
            name="tag_unassigned_date",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
