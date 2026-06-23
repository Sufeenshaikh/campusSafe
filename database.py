import sqlite3
from datetime import datetime,timedelta
import hashlib
from dotenv import load_dotenv

load_dotenv()
DB ="campussafe.db"

#CONNECTION
def get_conn():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row # with Row , result comes like dictionary and can directly access with row name
    return conn

#PASSWORD HASHING
def hash_password(password): #converts plain pw into hash
    return hashlib.sha256(password.encode()).hexdigest()

#TABLE CREATION
def init_db():
    conn = get_conn()

    # conn.execute("DROP TABLE IF EXISTS zones;")
    # conn.commit()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL,
            email          TEXT    UNIQUE NOT NULL,
            password_hash  TEXT    NOT NULL,
            guardian_email TEXT,
            role           TEXT    DEFAULT 'student',
            created_at     TEXT    DEFAULT (datetime('now'))
        );
                       
    CREATE TABLE IF NOT EXISTS sos_alerts(
                       id  INTEGER  PRIMARY KEY AUTOINCREMENT,
                       user_id  INTEGER  NOT NULL,
                       user_name  TEXT,
                       latitude  REAL,
                       longitude  REAL,
                       status  TEXT  DEFAULT 'active',
                       triggered_at  TEXT  DEFAULT (datetime('now'))
                       );

    CREATE TABLE IF NOT EXISTS incident_reports(
                       id  INTEGER  PRIMARY KEY AUTOINCREMENT,
                       user_id  INTEGER  NOT NULL,
                       user_name  TEXT,
                       location_name  TEXT,
                       description  TEXT,
                       severity  INTEGER  DEFAULT 1,
                       reported_at  TEXT  DEFAULT (datetime('now'))
                       );

    CREATE TABLE IF NOT EXISTS zones(
                       id  INTEGER  PRIMARY KEY AUTOINCREMENT,
                       name  TEXT,
                       latitude  REAL,
                       longitude  REAL,
                       safety_level  TEXT  DEFAULT 'safe',
                       description  TEXT,
                       ai_updated_at  TEXT
                       );
                       """)
    
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM zones").fetchone()[0]
    if count == 0:
        zones = [
            ("IET Main Gate", 22.680, 75.8800, "safe", "Security guard present, well lit"),
            ("DAVV Takshashila Main Entrance", 22.6885, 75.8732, "safe", "Active security checkpoint near Ring Road square, brightly lit entry"),
            ("IMS (Institute of Management Studies)", 22.6898, 75.8720, "safe", "High student density, continuous foot traffic between classes"),
            ("SCSIT (School of Computer Science)", 22.6912, 75.8741, "safe", "Equipped with operational CCTV frameworks, indoor lighting constant"),
            ("IIPS (International Inst. of Professional Studies)", 22.6905, 75.8715, "safe", "Central student activity plaza, well-maintained paths"),
            ("DAVV Central Library", 22.6923, 75.8735, "safe", "Core study zone, well illuminated with nearby night patrol guards"),
            ("Vigyan Bhawan & Botanical Gardens", 22.6935, 75.8748, "warning", "Dense tree foliage creating visual blind spots; streetlights dim after 9 PM"),
            ("Indian Coffee House (ICH Campus Canteen)", 22.6890, 75.8725, "safe", "Highly populated gathering point for students during day hours"),
            ("Jawaharlal Nehru Boys Hostel Complex", 22.6945, 75.8710, "safe", "Hostel boundary secure, steady movement of residential students"),
            ("Girls Hostel Pathway Alleys", 22.6938, 75.8752, "warning", "Isolated corridor behind sports fields; extra caution advised after dark"),
            ("DAVV Cricket & Football Grounds", 22.6950, 75.8730, "danger", "Unlit and isolated open fields at night; avoid walking alone past 8 PM")
        ]

        conn.executemany(
            """INSERT INTO zones
            (name, latitude, longitude, safety_level,description)
            VALUES(?,?,?,?,?)""",
            zones
        )
        conn.commit()
        print("Default DAVV zones added.")

    conn.close()
    print("DATABASE READY")


#USER FUNCTIONS

def register_user(name,email,password,guardian_email,role="student"):
    conn = get_conn()
    try:
        conn.execute("""INSERT INTO users
                     (name,email,password_hash, guardian_email,role)
                     VALUES(?,?,?,?,?)""",
                     (name,email,hash_password(password),guardian_email,role)
        )
        conn.commit()
        return True
    
    except sqlite3.IntegrityError:
        #unique contraint on email - this emal is already registered
        return False
    
    finally:
        conn.close()

def login_user(email,password):
    conn = get_conn()
    user = conn.execute(
        """SELECT * from users
           WHERE email = ? AND password_hash = ?""",
        (email, hash_password(password))
    ).fetchone()
    conn.close()

    return dict(user) if user else None
                        

def update_guardian_email(user_id,new_email):
    conn = get_conn()
    conn.execute(
        (new_email, user_id)
    )
    conn.commit()
    conn.close()


#SOS FUNCTIONS
def save_sos(user_id,user_name,latitude,longitude):
    conn = get_conn()
    cursor = conn.execute(
        """INSERT INTO sos_alerts
        (user_id,user_name,latitude,longitude)
        VALUES(?,?,?,?)""",
    (user_id, user_name, latitude, longitude)
    )

    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return alert_id

def get_all_sos():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sos_alerts ORDER BY triggered_at DESC"
    ).fetchall()
    conn.close()

    return[dict(r) for r in rows]

def get_user_sos(user_id):
    """Returns all SOS alerts for one specific user."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT * FROM sos_alerts
           WHERE user_id = ?
           ORDER BY triggered_at DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_sos(alert_id):
    """Marks an SOS alert as resolved."""
    conn = get_conn()
    conn.execute(
        "UPDATE sos_alerts SET status = 'resolved' WHERE id = ?",
        (alert_id,)
    )
    conn.commit()
    conn.close()


#INCIDENT REPORT FUNCTIONS
def save_report(user_id, user_name, location_name, description, severity):
    """Saves a new incident report submitted by a student."""
    conn = get_conn()
    conn.execute(
        """INSERT INTO incident_reports
           (user_id, user_name, location_name, description, severity)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, user_name, location_name, description, severity)
    )
    conn.commit()
    conn.close()


def get_recent_reports(days=7):
    """
    Returns incident reports from the last N days.
    This is what gets sent to the AI for zone analysis.
    Fewer days = AI reacts faster to changes.
    More days = AI has more context.
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    conn = get_conn()
    rows = conn.execute(
        """SELECT * FROM incident_reports
           WHERE reported_at >= ?
           ORDER BY reported_at DESC""",
        (cutoff,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_reports():
    """Returns every report ever. Used in admin dashboard and RAG loading."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM incident_reports ORDER BY reported_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_reports(user_id):
    """Returns all reports submitted by one specific user."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT * FROM incident_reports
           WHERE user_id = ?
           ORDER BY reported_at DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

#ZONE FUNCTIONS
def get_all_zones():
    """Returns all campus safety zones. Used to draw the map."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM zones").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_zone_safety(zone_id, new_level):
    """
    Updates the safety level of one zone.
    Called automatically by the AI after new reports come in.
    new_level must be exactly: 'safe', 'caution', or 'unsafe'
    """
    conn = get_conn()
    conn.execute(
        """UPDATE zones
           SET safety_level = ?, ai_updated_at = ?
           WHERE id = ?""",
        (new_level, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), zone_id)
    )
    conn.commit()
    conn.close()
