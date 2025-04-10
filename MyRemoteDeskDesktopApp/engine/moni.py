from __future__ import print_function
import time
import json
import datetime
import sys
import plotly.graph_objects as go
import moni
from datetime import date
import pymysql
from dateutil import parser

# Windows-specific imports
import importlib

if sys.platform in ['Windows', 'win32', 'cygwin']:
    win32gui = importlib.import_module("win32gui")
    auto = importlib.import_module("uiautomation")
else:
    win32gui = None
    auto = None



# MySQL connection
json_object = json.loads(sys.argv[1])
e_id = json_object["e_id"]
o_id = json_object["o_id"]

# Connect to the database
try:
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='myremotedesk',
        port=3306
    )
    print("Connected with PyMySQL!")

    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE();")
        result = cursor.fetchone()
        print("Current database:", result)

        # Loop through activities and insert into the database
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
            print(cursor.rowcount, "record inserted.")

except Exception as e:
    print("Error:", e)

finally:
    if connection:
        connection.close()
        print("Connection closed")


class AcitivyList:
    def __init__(self, activities):
        self.activities = activities

    def initialize_me(self):
        activity_list = AcitivyList([])
        with open('activities.json', 'r') as f:
            data = json.load(f)
            activity_list = AcitivyList(
                activities=self.get_activities_from_json(data)
            )

        return activity_list

    def get_activities_from_json(self, data):
        return_list = []
        for activity in data['activities']:

            return_list.append(
                Activity(
                    name=activity['name'],
                    time_entries=self.get_time_entires_from_json(activity),
                )
            )
        self.activities = return_list
        return return_list

    def get_time_entires_from_json(self, data):
        return_list = []
        for entry in data['time_entries']:
            return_list.append(
                TimeEntry(
                    start_time=parser.parse(entry['start_time']),
                    end_time=parser.parse(entry['end_time']),
                    days=entry['days'],
                    hours=entry['hours'],
                    minutes=entry['minutes'],
                    seconds=entry['seconds'],
                )
            )
        self.time_entries = return_list
        return return_list

    def serialize(self):
        return {
            'activities': self.activities_to_json()
        }

    def activities_to_json(self):
        activities_ = []
        for activity in self.activities:
            activities_.append(activity.serialize())

        return activities_


class Activity:
    def __init__(self, name, time_entries):
        self.name = name
        self.time_entries = time_entries

    def serialize(self):
        return {
            'name': self.name,
            'time_entries': self.make_time_entires_to_json()
        }

    def make_time_entires_to_json(self):
        time_list = []
        for time in self.time_entries:
            time_list.append(time.serialize())

        return time_list


class TimeEntry:
    def __init__(self, start_time, end_time, days, hours, minutes, seconds):
        self.start_time = start_time
        self.end_time = end_time
        self.total_time = end_time - start_time
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def _get_specific_times(self):
        self.days, self.seconds = self.total_time.days, self.total_time.seconds
        self.hours = self.days * 24 + self.seconds // 3600
        self.minutes = (self.seconds % 3600) // 60
        self.seconds = self.seconds % 60

    def serialize(self):
        return {
            'start_time': self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'end_time': self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            'days': self.days,
            'hours': self.hours,
            'minutes': self.minutes,
            'seconds': self.seconds
        }


def url_to_name(url):
    string_list = url.split('/')
    return string_list[2]


def get_active_window():
    _active_window_name = None
    if sys.platform in ['Windows', 'win32', 'cygwin']:
        window = win32gui.GetForegroundWindow()
        _active_window_name = win32gui.GetWindowText(window)
    else:
        print("sys.platform={platform} is not supported."
              .format(platform=sys.platform))
        print(sys.version)
    return _active_window_name


def get_chrome_url():
    if sys.platform in ['Windows', 'win32', 'cygwin']:
        window = win32gui.GetForegroundWindow()
        chromeControl = auto.ControlFromHandle(window)
        edit = chromeControl.EditControl()
        return 'https://' + edit.GetValuePattern().Value
    else:
        print("sys.platform={platform} is not supported."
              .format(platform=sys.platform))
        print(sys.version)
    return None


def show_activity():

    b = list()
    d = list()
    try:
        with open('activities.json', 'r') as jsonfile:
            a = json.load(jsonfile)
            e = a['activities']
    except Exception:
        print("no json data")
        exit(0)

    for i in e:
        b.append(i['name'])

    tot = 0

    for i in e:
        sed = 0
        for j in i["time_entries"]:
            sed = sed + int(j["minutes"])*60 + \
                int(j["seconds"])+int(j["hours"])*3600
            tot = tot+sed
        d.append(sed)

    kek = time.strftime("%H:%M:%S", time.gmtime(tot))
    kek = "Time used : "+kek
    print(b)
    print(d)
    combineBD = zip(b, d)
    zipped_list = list(combineBD)

    return zipped_list


def erase():
    open("activities.json", "w").close()


def record(active_window_name, activity_name, start_time, activeList, first_time, e_id, o_id, cursordb, connectiondb):
    try:
        activeList = activeList.initialize_me()
    except Exception as e:
        print('No json:', e)

    try:
        while True:
            if sys.platform not in ['linux', 'linux2']:
                new_window_name = get_active_window()
                if 'Google Chrome' in new_window_name:
                    chrome_url = get_chrome_url()
                    if chrome_url:
                        new_window_name = url_to_name(chrome_url)

            if new_window_name and active_window_name != new_window_name:
                print(f"Switched from '{active_window_name}' to '{new_window_name}'")
                activity_name = new_window_name
                current_time = datetime.datetime.now()

                # Insert activity into DB
                sql = "INSERT INTO monitoring (m_title, m_log_ts, e_id_id, o_id_id) VALUES (%s, %s, %s, %s)"
                val = (activity_name, current_time, e_id, o_id)
                try:
                    cursordb.execute(sql, val)
                    connectiondb.commit()
                    print(f"{cursordb.rowcount} record inserted.")
                except Exception as e:
                    print("DB insert failed:", e)

                # Track time
                if not first_time:
                    end_time = datetime.datetime.now()
                    time_entry = TimeEntry(start_time, end_time, 0, 0, 0, 0)
                    time_entry._get_specific_times()

                    exists = False
                    for activity in activeList.activities:
                        if activity.name == activity_name:
                            exists = True
                            activity.time_entries.append(time_entry)
                            break

                    if not exists:
                        new_activity = Activity(activity_name, [time_entry])
                        activeList.activities.append(new_activity)

                    # Save to JSON
                    try:
                        with open('activities.json', 'w') as json_file:
                            json.dump(activeList.serialize(), json_file, indent=4, sort_keys=True)
                    except Exception as e:
                        print("Failed to write JSON:", e)

                # Reset start time
                start_time = datetime.datetime.now()
                first_time = False
                active_window_name = new_window_name

            time.sleep(1)

    except KeyboardInterrupt:
        print("Recording stopped.")
        try:
            with open('activities.json', 'w') as json_file:
                json.dump(activeList.serialize(), json_file, indent=4, sort_keys=True)
        except Exception as e:
            print("Final save failed:", e)

def mainRecord(e_id, o_id):
    active_window_name = str()
    activity_name = ""
    start_time = datetime.datetime.now()
    activeList = AcitivyList([])
    first_time = True
    record(active_window_name, activity_name,start_time, activeList, first_time, e_id, o_id)
