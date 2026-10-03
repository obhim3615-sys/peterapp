import psycopg2
from psycopg2 import sql
from django.conf import settings
from django.contrib.gis.geos import Point,GEOSGeometry
import json


import requests


MASKING_API = "https://addhar-masked-image.vikshep.com/upload_file_direct"

def mask_aadhaar_file(uploaded_file):
    """Send file to masking API and return (masked_bytes, media_type, filename)."""
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.read(),
            uploaded_file.content_type or "application/octet-stream",
        )
    }
    resp = requests.post(MASKING_API, files=files, stream=True)
    resp.raise_for_status()

    media_type = resp.headers.get("Content-Type", "application/octet-stream")
    disposition = resp.headers.get("Content-Disposition", "attachment; filename=masked.png")
    filename = disposition.split("filename=")[-1].strip('"').strip()

    return resp.content, media_type, filename



def insert_into_remote_db(table_name, data):
    """
    Inserts data into a specified table in the remote database.

    :param table_name: Name of the table where data should be inserted.
    :param data: Dictionary of data to be inserted.
    :param db_name: Name of the remote database.
    :param user: Username for the remote database.
    :param password: Password for the remote database.
    :param host: Host address of the remote database.
    :param port: Port number of the remote database.
    """
    db_name=settings.PRAKSHEP_DB_NAME
    db_user=settings.PRAKSHEP_DB_USER
    db_password=settings.PRAKSHEP_DB_PASSWORD
    db_host=settings.PRAKSHEP_DB_HOST
    db_port=settings.PRAKSHEP_DB_PORT
    # try:
        # Establish the connection to the remote database
    connection = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    cursor = connection.cursor()    

    # Prepare the insert statement with special handling for Point geometry
    # Convert any Point objects to the ST_MakePoint and ST_SetSRID format
    columns = []
    values = []

    for key, value in data.items():
        columns.append(sql.Identifier(key))
        if isinstance(value, Point):
            if value.srid is None:
                value.srid = 4326  # Set the SRID if not already set
            elif value.srid != 4326:
                value.transform(4326)  # Transform to the correct SRID if needed
            geom_value = sql.SQL("ST_SetSRID(ST_MakePoint({}, {}), {})").format(
                sql.Literal(value.x), sql.Literal(value.y), sql.Literal(value.srid)
            )
            values.append(geom_value)
        elif isinstance(value, dict):
            json_value = sql.Literal(json.dumps(value))  # Convert dictionary to JSON string
            values.append(json_value)
        else:
            values.append(sql.Literal(value))

    # Build the final SQL query
    query = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values})").format(
        table=sql.Identifier(table_name),
        columns=sql.SQL(', ').join(columns),
        values=sql.SQL(', ').join(values)
    )

    # Execute the insert statement
    cursor.execute(query)

    # Commit the transaction
    connection.commit()
    # except Exception as e:s
    #     print(f"An error occurred: {e}")
    # finally:
        # Close the cursor and connection
    if cursor:
        cursor.close()
    if connection:
        connection.close()