import csv
from datetime import datetime
from edupage_api import Edupage
from edupage_api.timeline import EventType
from notion_client import Client
import time
from edupage_api.login import LoginException

# Login to Edupage with retry
edupage = Edupage()
max_retries = 5
retry_delay = 5  # Sekunden warten zwischen den Versuchen

for attempt in range(1, max_retries + 1):
    try:
        edupage.login(
            "samuel.dueckmann",
            "Agent_099",
            "dbs",
        )
        print("Login erfolgreich!")
        break  # Wenn Login klappt, Schleife beenden
    except (LoginException, Exception) as e:
        print(f"Login-Versuch {attempt} fehlgeschlagen: {e}")
        if attempt == max_retries:
            raise  # Nach letztem Versuch Fehler werfen
        time.sleep(retry_delay)  # Warten und nochmal probieren

notifications = edupage.get_notifications()

# Filter for homework notifications
homework = list(filter(lambda x: x.event_type == EventType.HOMEWORK, notifications))
classTests = list(filter(lambda x: x.event_type == EventType.EVENT, notifications))

# Prepare a list to hold processed homework data
homework_data = []
class_tests = []

# Get today's date
today = datetime.now()

subject_abbreviations = {
    "Mathematik": "M",
    "Deutsch": "D",
    "Englisch": "E",
    "Biologie": "Bio",
    "Chemie": "Ch",
    "Physik": "Ph",
    "Geschichte": "G",
    "Geographie": "Geo",
    "Kunst": "BK",
    "Sport": "Spo",
    "Informationstechnik": "IT",
    "Dogmatik": "D",
    "Gemeinschaftskunde": "GK",
    "WBS": "WBS",
    'Diakonie in Aktion': 'Dia',
}

# Class Tests
for classTest in classTests:
    ad = classTest.additional_data
    c_date = None
    c_title = None
    c_subject = None

    if ad:
        c_date_str = ad.get('dateto')
        c_title = ad.get('name')
        c_subject = classTest.recipient

        if c_subject:
            c_subject = c_subject.replace('Klasse 9 A · ', '').strip()
            c_subject = subject_abbreviations.get(c_subject, c_subject)

            if not c_title:
                c_title = c_subject

        c_title =  str(c_subject + ': ' + c_title)

        if c_date_str and c_title:
            try:
                c_date = datetime.strptime(c_date_str, "%Y-%m-%d")
                if c_date > today:  # Include only future dates
                    class_tests.append({"date": c_date, "title": str(c_title), 'subject': c_subject})
            except ValueError:
                print(f"Invalid date format: {c_date_str}")

# Homework
for hw in homework:
    additional_data = hw.additional_data
    date = None
    title = None
    subject = None

    if additional_data:
        date_str = additional_data.get("date")  # Get date as string
        title = additional_data.get("nazov")  # Get title
        subject = hw.recipient

        if title:
            title = title.replace("\n", "").strip()
            title = title.replace('"','').strip()
            title = title.replace('Geändert: ', '').strip()

        if subject:
            subject = subject.replace('Klasse 9 A · ', '').strip()

        # Process entries where date is valid and after today
        if date_str and title:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if date > today:  # Include only future dates
                    homework_data.append({"date": date, "title": title, 'subject': subject})
            except ValueError:
                print(f"Invalid date format: {date_str}")

# Function to check if a task already exists in the Notion database
def get_existing_titles():
    existing_titles = []
    query = notion.databases.query(database_id=database_id)
    for result in query.get("results", []):
        if "properties" in result:
            title_property = result["properties"].get("Title", {}).get("title", [])
            if title_property:
                existing_titles.append("".join([t["plain_text"] for t in title_property]))
    return set(existing_titles)

def c_get_existing_titles():
    c_existing_titles = []
    c_query = notion_2.databases.query(database_id=c_database_id)
    for c_result in c_query.get("results", []):
        if "properties" in c_result:
            c_title_property = c_result["properties"].get("Title", {}).get("title", [])
            if c_title_property:
                c_existing_titles.append("".join([t["plain_text"] for t in c_title_property]))
    return set(c_existing_titles)

# Get existing titles from Notion database
existing_titles = get_existing_titles()
c_existing_titles = c_get_existing_titles()

for ct in class_tests:
    if ct["title"] not in c_existing_titles:
        notion_2.pages.create(
            parent={"database_id": c_database_id},
            properties={
                "Title": {"title": [{"text": {"content": ct["title"]}}]},
                "Date": {"date": {"start": ct["date"].strftime("%Y-%m-%d")}},
                "Subject": {"select": {"name": ct['subject']}},
            },
        )
        print(f"Added: {ct['title']}")

# Add new tasks to Notion database
for hw in homework_data:
    if hw["title"] not in existing_titles:
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Title": {"title": [{"text": {"content": hw["title"]}}]},
                "Date": {"date": {"start": hw["date"].strftime("%Y-%m-%d")}},
                "Subject": {"select": {"name": hw['subject']}},
            },
        )
        print(f"Added: {hw['title']}")

print("New homework has been added to the Notion database.")