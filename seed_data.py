from database import(
    init_db,register_user,
    get_conn
)
from datetime import datetime, timedelta
import random

print("Starting seed data generation...")

#checking Database and Tables exist
init_db()
print("Database ready.")

#Student accounts
students = [
    {"name": "Priya Sharma",   "email": "priya.sharma@davv.ac.in",   "password": "priya1234",   "guardian_email": "sharma.family@gmail.com",       "role": "student"},
    {"name": "Anjali Verma",   "email": "anjali.verma@davv.ac.in",   "password": "anjali1234",  "guardian_email": "verma.anjali.parent@gmail.com", "role": "student"},
    {"name": "Riya Patel",     "email": "riya.patel@davv.ac.in",     "password": "riya1234",    "guardian_email": "patel.riya.home@gmail.com",     "role": "student"},
    {"name": "Sneha Joshi",    "email": "sneha.joshi@davv.ac.in",    "password": "sneha1234",   "guardian_email": "joshi.sneha.mom@gmail.com",     "role": "student"},
    {"name": "Kavya Singh",    "email": "kavya.singh@davv.ac.in",    "password": "kavya1234",   "guardian_email": "singh.kavya.family@gmail.com",  "role": "student"},
    {"name": "Pooja Mishra",   "email": "pooja.mishra@davv.ac.in",   "password": "pooja1234",   "guardian_email": "mishra.pooja.parent@gmail.com", "role": "student"},
    {"name": "Neha Gupta",     "email": "neha.gupta@davv.ac.in",     "password": "neha1234",    "guardian_email": "gupta.neha.home@gmail.com",     "role": "student"},
    {"name": "Divya Tiwari",   "email": "divya.tiwari@davv.ac.in",   "password": "divya1234",   "guardian_email": "tiwari.family@gmail.com",       "role": "student"},
    {"name": "Sakshi Dubey",   "email": "sakshi.dubey@davv.ac.in",   "password": "sakshi1234",  "guardian_email": "dubey.sakshi.parent@gmail.com", "role": "student"},
    {"name": "Meera Yadav",    "email": "meera.yadav@davv.ac.in",    "password": "meera1234",   "guardian_email": "yadav.meera.home@gmail.com",    "role": "student"},
    {"name": "Rahul Chouhan",  "email": "rahul.chouhan@davv.ac.in",  "password": "rahul1234",   "guardian_email": "chouhan.rahul.dad@gmail.com",   "role": "student"},
    {"name": "Amit Pandey",    "email": "amit.pandey@davv.ac.in",    "password": "amit1234",    "guardian_email": "pandey.amit.family@gmail.com",  "role": "student"},
    {"name": "Vikram Solanki", "email": "vikram.solanki@davv.ac.in", "password": "vikram1234",  "guardian_email": "solanki.vikram.home@gmail.com", "role": "student"},
    {"name": "Rohit Malviya",  "email": "rohit.malviya@davv.ac.in",  "password": "rohit1234",   "guardian_email": "malviya.rohit.parent@gmail.com","role": "student"},
    {"name": "Admin User",     "email": "admin@davv.ac.in",          "password": "admin1234",   "guardian_email": "admin.davv@gmail.com",          "role": "admin"},
]

registered = 0
for s in students:
    success = register_user(
         name           = s["name"],
        email          = s["email"],
        password       = s["password"],
        guardian_email = s["guardian_email"],
        role           = s["role"]
    )
    if success:
        registered += 1

print(f"Registered {registered} new student accounts.")

# Get user IDs from database
conn = get_conn()
users = conn.execute(
    "SELECT id, name FROM users WHERE role = 'student'"
).fetchall()
conn.close()

users = [dict(u) for u in users]
print(f"Found {len(users)} student accounts in database.")

incident_templates = [

    {
        "location": "Girls Hostel Pathway Alleys",
        "reports": [
            ("Someone was following me along the hostel pathway "
             "at night, I was terrified and ran back",            5),
            ("Two unknown men standing near the hostel alley "
             "at 11pm, felt very unsafe and threatened",          5),
            ("Street lights are broken along the hostel pathway, "
             "very dark and isolated after 8pm",                  3),
            ("Saw suspicious activity near the hostel alleys, "
             "group of outsiders sitting there at night",          4),
            ("Felt very uneasy walking alone here after 9pm, "
             "no security visible anywhere",                       3),
        ]
    },

    {
        "location": "DAVV Cricket & Football Grounds",
        "reports": [
            ("Ground is completely dark after 7pm, "
             "lights not working on the far side near boundary",   2),
            ("Some outsiders were using the ground at night, "
             "no security was present",                            3),
            ("The area near the equipment room is isolated "
             "and feels very unsafe after dark",                   3),
            ("Suspicious group sitting near the cricket ground "
             "boundary wall late at night",                        4),
        ]
    },

    {
        "location": "DAVV Takshashila Main Entrance",
        "reports": [
            ("Main entrance gate was open late at night with "
             "no security guard present",                          3),
            ("Noticed suspicious auto rickshaws waiting outside "
             "entrance for a long time after 10pm",               2),
            ("Entrance is well lit and security present during "
             "the day, felt safe",                                 1),
        ]
    },

    {
        "location": "Indian Coffee House (ICH Campus Canteen)",
        "reports": [
            ("Group of outsiders sitting near canteen after "
             "closing time, causing disturbance",                  3),
            ("Canteen area is empty and poorly lit after 9pm, "
             "felt unsafe walking past alone",                     2),
            ("Verbal argument between people near canteen, "
             "situation became tense",                             3),
            ("Fine during the day but feels deserted and "
             "unsafe in the evening",                              2),
        ]
    },

    {
        "location": "Jawaharlal Nehru Boys Hostel Complex",
        "reports": [
            ("Security guard was not present at the hostel "
             "complex for about 30 minutes around 10pm",           3),
            ("Noticed a stranger loitering near the hostel "
             "entrance in the evening",                            2),
            ("Hostel complex well lit, guard present, "
             "felt safe",                                          1),
        ]
    },

    {
        "location": "IET Main Gate",
        "reports": [
            ("Main gate is well lit and security is always "
             "present, felt completely safe",                      1),
            ("Guard checked ID properly, good security",           1),
            ("Suspicious person loitering outside main gate "
             "for a long time at night",                           2),
        ]
    },

    {
        "location": "DAVV Central Library",
        "reports": [
            ("Library is well lit with CCTV, felt completely "
             "safe studying till closing time",                    1),
            ("Security rounds happen regularly near library",      1),
        ]
    },

    {
        "location": "SCSIT (School of Computer Science)",
        "reports": [
            ("SCSIT block is isolated at night, no lighting "
             "around the back entrance after 8pm",                 3),
            ("Felt unsafe walking alone near SCSIT after "
             "college hours, very few people around",              3),
            ("Unknown persons standing near SCSIT back gate "
             "late at night",                                      4),
        ]
    },

    {
        "location": "Vigyan Bhawan & Botanical Gardens",
        "reports": [
            ("Botanical garden area is completely dark at night, "
             "no lighting or security visible",                    4),
            ("Very isolated area after 6pm, would not recommend "
             "walking here alone",                                 4),
            ("Suspicious activity noticed near the garden "
             "boundary after sunset",                              3),
        ]
    },

    {
        "location": "IIPS (International Inst. of Professional Studies)",
        "reports": [
            ("IIPS block area is quiet and safe during the day, "
             "security present",                                   1),
            ("Felt slightly uneasy near IIPS after 9pm, "
             "very few people around",                             2),
        ]
    },

    {
        "location": "IMS (Institute of Management Studies)",
        "reports": [
            ("IMS area is well maintained and safe during "
             "college hours",                                      1),
            ("Parking near IMS is dark and isolated at night, "
             "no CCTV visible",                                    3),
        ]
    },

]

def random_past_time(days_back_max=6):
    minutes_back = random.randint(30, days_back_max * 24 * 60)
    past_time    = datetime.now() - timedelta(minutes=minutes_back)
    return past_time.strftime("%Y-%m-%d %H:%M:%S")

# Only insert reports if there are no reports yet
# Prevents duplicating data if run this script multiple times
conn = get_conn()
existing_count = conn.execute(
    "SELECT COUNT(*) FROM incident_reports"
).fetchone()[0]

report_count = 0

if existing_count == 0 and users:
    for template in incident_templates:
        for description, severity in template["reports"]:
            student   = random.choice(users)
            past_time = random_past_time(days_back_max=14)

            conn.execute(
                """INSERT INTO incident_reports
                   (user_id, user_name, location_name,
                    description, severity, reported_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    student["id"],
                    student["name"],
                    template["location"],
                    description,
                    severity,
                    past_time
                )
            )
            report_count += 1

    conn.commit()
    print(f"Added {report_count} incident reports.")
else:
    print(f"Skipped reports — {existing_count} already exist.")

conn.close()

#SOS Alerts
sos_events = [
    {"user_name": "Priya Sharma",  "latitude": 22.6798, "longitude": 75.8812, "status": "resolved"},
    {"user_name": "Anjali Verma",  "latitude": 22.6802, "longitude": 75.8792, "status": "resolved"},
    {"user_name": "Kavya Singh",   "latitude": 22.6790, "longitude": 75.8795, "status": "resolved"},
    {"user_name": "Sneha Joshi",   "latitude": 22.6798, "longitude": 75.8812, "status": "resolved"},
    {"user_name": "Riya Patel",    "latitude": 22.6802, "longitude": 75.8792, "status": "active"},
    {"user_name": "Pooja Mishra",  "latitude": 22.6808, "longitude": 75.8818, "status": "resolved"},
    {"user_name": "Neha Gupta",    "latitude": 22.6820, "longitude": 75.8825, "status": "active"},
    {"user_name": "Divya Tiwari",  "latitude": 22.6798, "longitude": 75.8812, "status": "resolved"},
]

conn = get_conn()
existing_sos = conn.execute(
    "SELECT COUNT(*) FROM sos_alerts"
).fetchone()[0]

sos_count = 0

if existing_sos == 0:
    for event in sos_events:
        student = conn.execute(
            "SELECT id FROM users WHERE name = ?",
            (event["user_name"],)
        ).fetchone()

        if student:
            past_time = random_past_time(days_back_max=10)

            conn.execute(
                """INSERT INTO sos_alerts
                   (user_id, user_name, latitude,
                    longitude, status, triggered_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    student["id"],
                    event["user_name"],
                    event["latitude"],
                    event["longitude"],
                    event["status"],
                    past_time
                )
            )
            sos_count += 1

    conn.commit()
    print(f"Added {sos_count} SOS alerts.")
else:
    print(f"Skipped SOS alerts — {existing_sos} already exist.")

conn.close()

# UPDATE zone safety levels based on reports
print("Updating zone safety levels...")

from ai import auto_update_zones
changes = auto_update_zones()

if changes:
    print("Zone safety changes:")
    for c in changes:
        print(f"  {c}")
else:
    print("Zones already at correct safety levels.")

# Load all reports into ChromaDB for RAG
print("Loading reports into RAG memory...")

try:
    from ai import load_all_reports_into_rag
    load_all_reports_into_rag()
    print("RAG memory loaded.")
except Exception as e:
    print(f"RAG loading skipped: {e}")

# Print Summary
print("\n" + "="*50)
print("SEED DATA COMPLETE")
print("="*50)

conn = get_conn()
user_count   = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
report_count = conn.execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0]
sos_count    = conn.execute("SELECT COUNT(*) FROM sos_alerts").fetchone()[0]
zone_counts  = conn.execute(
    "SELECT safety_level, COUNT(*) FROM zones GROUP BY safety_level"
).fetchall()
conn.close()

print(f"Users           : {user_count}")
print(f"Incident reports: {report_count}")
print(f"SOS alerts      : {sos_count}")
print("Zone safety levels:")
for row in zone_counts:
    print(f"  {row[0]}: {row[1]} zones")

print("\nLogin credentials for demo:")
print("Student  -> priya.sharma@davv.ac.in / priya1234")
print("Admin    -> admin@davv.ac.in        / admin1234")
print("="*50)