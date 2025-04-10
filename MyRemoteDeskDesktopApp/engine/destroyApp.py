import sys
import json
import moni
from datetime import date
import pymysql

def main():
    try:
        # Parse command-line argument (JSON string)
        if len(sys.argv) < 2:
            print("Missing JSON input argument")
            sys.exit(1)

        json_object = json.loads(sys.argv[1])
        e_id = json_object.get("e_id")
        o_id = json_object.get("o_id")

        if not e_id or not o_id:
            print("Missing 'e_id' or 'o_id' in JSON")
            sys.exit(1)

        # Connect to the MySQL database
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='',
            database='myremotedesk',
            port=3306
        )
        print("✅ Connected with PyMySQL!")

        with connection.cursor() as cursor:
            # Show the current database
            cursor.execute("SELECT DATABASE();")
            result = cursor.fetchone()
            print("📂 Current database:", result)

            # Loop through activity data and insert into the table
            for w, t in moni.show_activity():
                today = date.today()
                sql = """
                    INSERT INTO MonitoringDetails 
                    (md_title, md_total_time_seconds, md_date, e_id_id, o_id_id)
                    VALUES (%s, %s, %s, %s, %s)
                """
                val = (w, t, today, e_id, o_id)
                cursor.execute(sql, val)
                connection.commit()
                print(f"✅ Inserted: {w} - {t} seconds")

    except Exception as e:
        print("❌ Error:", e)

    finally:
        try:
            if connection:
                connection.close()
                print("🔌 Connection closed")
        except NameError:
            pass

if __name__ == "__main__":
    main()

# import sys
# import json
# import moni
# from datetime import date

# import mysql.connector
# from mysql.connector import Error

# try:
#     connectiondb = mysql.connector.connect(
#         host="127.0.0.1",
#         user="root",
#         password="",
#         database="myremotedesk",
#         port=3306
#     )

#     if connectiondb.is_connected():
#         cursordb = connectiondb.cursor()
#         print("Connected to MySQL Server!")
#         print("Connection object:", connectiondb)

# except Error as e:
#     print("Error while connecting to MySQL:", e)

# finally:
#     if 'connectiondb' in locals() and connectiondb.is_connected():
#         cursordb.close()
#         connectiondb.close()
#         print("MySQL connection is closed")

# json_object = json.loads(sys.argv[1])

# e_id = json_object["e_id"]
# o_id = json_object["o_id"]

# for w, t in moni.show_activity():
#     today = date.today()
#     sql = "INSERT INTO MonitoringDetails (md_title, md_total_time_seconds, md_date, e_id_id, o_id_id) VALUES (%s, %s, %s, %s, %s)" 
#     val = (w,t, today, e_id, o_id)
#     cursordb.execute(sql, val)
#     connectiondb.commit()
#     print(cursordb.rowcount, "record inserted.")

