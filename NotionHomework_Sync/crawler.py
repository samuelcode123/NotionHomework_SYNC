import csv
from datetime import datetime
from edupage_api import Edupage
from edupage_api.timeline import EventType
from notion_client import Client

# Notion API Setup
notion = Client(auth="ntn_K6086584265nF41A97FMtGd0LaKUDxJwhPUPOmMRTuqajl")
database_id = "18916ac9e7c98073b303dbc7a7c769b0"

# Login to Edupage
edupage = Edupage()
edupage.login(
    "samuel.dueckmann",
    "Agent_099",
    "dbs",
)

notifications = edupage.get_notifications()

# Filter for homework notifications
homework = list(filter(lambda x: x.event_type == EventType.HOMEWORK, notifications))

# Prepare a list to hold processed homework data
homework_data = []

# Get today's date
today = datetime.now()

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

# Get existing titles from Notion database
existing_titles = get_existing_titles()

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