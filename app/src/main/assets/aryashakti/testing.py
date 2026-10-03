import psycopg2
import json
import os


path_to_file = 'test.json'
with open(path_to_file, 'r') as data_file:
    data = json.load(data_file)

# print(type(data))
collection_array = []
for key, value in data.items():
    if key == "mobile_number":
        pass
    else:
        collection_array.append(json.dumps({"phone_no": key, "status": "TRUE"}))

import sys 
#sys.exit()
#print(collection_array[0])
conn = None
try:
    conn = psycopg2.connect(
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
    )
    print ("opened  database successfully", conn)
    cur = conn.cursor()
    
    # _query = f"""insert into "app_farm_user_phonenumber_map" values ({i}, '{item}'); """
    #cur.execute("INSERT INTO my_table (json_column_name) VALUES (%s)", (element,))
   
    for (i , item) in enumerate(collection_array):
        cur.execute("INSERT INTO app_farm_user_phonenumber_map (id, phone_no) VALUES (%s, %s)", (i+1, item))
        # cur.execute( f"""insert into "app_farm_user_phonenumber_map" values ({i+2}, {item}); """)
    #print("successfully inserted records")    


except psycopg2.Error as e:
    raise
finally:
    if conn is not None:
        conn.commit()
        conn.close()
    #print("connection is closed")