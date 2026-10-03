from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('recordActivity', '0058_remove_dronesprayactivity_kml_area_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
    ]
