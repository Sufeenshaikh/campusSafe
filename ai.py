import requests
import json
import os
import numpy as np
from textblob import TextBlob
from datetime import datetime
from database import (
    get_all_zones,
    get_recent_reports,
    get_all_reports,
    update_zone_safety
)

# ── OLLAMA SETTINGS 
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_EMBED = "http://localhost:11434/api/embeddings"
LLM_MODEL = "qwen2.5:3b" #for chat an reasoning
EMBED_MODEL = "nomic-embed-text" #converts text to vector

RAG_FILE = "rag_store.json"

def ask_ollama(prompt,system_prompt=None):
    #system_prompt = the role and rules we give AI
    #prompt        = the actual question or task

    full_prompt = (
        f"{system_prompt}\n\n{prompt}"
        if system_prompt
        else prompt
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json = {
                "model":  LLM_MODEL,
                "prompt": full_prompt,
                "stream": False      # wait for the full response
            },
            # timeout = 180            # 2 minutes — enough for CPU
        )
        return response.json()["response"].strip()

    except requests.exceptions.ConnectionError:
        return (
            "Ollama is not running. "
            "Open a terminal and run: ollama serve"
        )

    except requests.exceptions.Timeout:
        return (
            "Ollama took too long to respond. "
            "Please try again — it is faster after the first response."
        )

    except Exception as e:
        return f"AI error: {str(e)}"
    

def stream_ollama(prompt,system_prompt = None):
    full_prompt = (
        f"{system_prompt}\n\n{prompt}"
        if system_prompt
        else prompt
    )

    try:
        with requests.post(
            OLLAMA_URL,
            json = {
                "model": LLM_MODEL,
                "prompt": full_prompt,
                "stream":True
            },
            stream=True
        ) as response:
             for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if chunk.get("done",False):
                            break
                        token = chunk.get("response","")
                        if token:
                            yield token
                    except json.JSONDecodeError:
                        continue

    except requests.exceptions.ConnectionError:
        yield "Ollama is not running. Run: ollama serve in a terminal."

    except requests.exceptions.Timeout:
        yield "Ollama timed out.Please try again"

    except Exception as e:
        yield f"Error: {str(e)}"


def decide_tool_simple(question):
    q = question.lower()
    zones = get_all_zones()

    for zone in zones:
        zone_words = zone["name"].lower().split()
        if any(word in q for word in zone_words):
            return "check_zone",zone["name"]
        
    incident_keywords = [
        "happened","incident","report","recent","past","before","history","occurred","attack","complaint","case","event"]
    if any(word in q for word in incident_keywords):
        return "past_incidents",question
    
    zone_keywords = ["safe","unsafe","dangerous","avoid",
                     "area","place","zone","location","night",
                      "walk","alone","dark"]
    if any(word in q for word in zone_keywords):
        return "past_incidents",question
    
    return "general",""
    

def get_embedding(text):
    try:
        response = requests.post(
            OLLAMA_EMBED,
            json = {
                "model":  EMBED_MODEL,
                "prompt": text
            },
            timeout = 10    # shorter timeout — embedding is faster than LLM
        )
        response.raise_for_status()
        return response.json()["embedding"]

    except requests.exceptions.Timeout:
        print("Embedding timed out")
        return None
    
    except requests.exceptions.ConnectionError:
        print("cannot connect to ollama for embedding")
        return None

    except Exception as e:
        print(f"Embedding error:{e}")
        return None

    

# CONCEPT 1 — SENTIMENT ANALYSIS
#
# TextBlob reads incident report descriptions and returns
# a polarity score between -1.0 and +1.0
#
# -1.0 = very negative  (dangerous, terrifying, scary)
#  0.0 = neutral
# +1.0 = very positive  (safe, fine, good)
#
# We use this to automatically decide how severe a report is.

def analyze_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity <= -0.6:
        return 5
    elif polarity <= -0.3:
        return 4
    elif polarity <= -0.1:
        return 3
    elif polarity < 0.1:
        return 2
    else:
        return 1
    
def get_final_severity(description,user_given_severity):
    ai_severity = analyze_sentiment(description)
    return max(ai_severity, user_given_severity)


# CONCEPT 2 — RAG (Retrieval Augmented Generation)
#
# RAG means: search for relevant past information first,
# then give that information to the AI as context,
# so the AI answers using real data instead of guessing.

def load_rag_store():
    if not os.path.exists(RAG_FILE):
        return []
    try:
        with open(RAG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_rag_store(store):
     with open(RAG_FILE, "w") as f:
        json.dump(store, f)

def cosine_similarity(vec1, vec2):

     v1 = np.array(vec1, dtype=np.float32)
     v2 = np.array(vec2, dtype=np.float32)

     norm1 = np.linalg.norm(v1)
     norm2 = np.linalg.norm(v2)

    # Avoid division by zero
     if norm1 == 0 or norm2 == 0:
        return 0.0

     return float(np.dot(v1, v2) / (norm1 * norm2))

def store_incident_in_rag(report_id, location, description, severity):
    store = load_rag_store()
    existing_ids = {item["id"] for item in store}
    if str(report_id) in existing_ids:
        return
    full_text = f"{location}: {description}"

    # Convert to vector
    embedding = get_embedding(full_text)
    if embedding is None:
        print(f"RAG: embedding failed for report {report_id} — skipped")
        return

    # Add to store
    store.append({
        "id":        str(report_id),
        "text":      full_text,
        "embedding": embedding,
        "location":  location,
        "severity":  str(severity)
    })

    save_rag_store(store)
    print(f"RAG: stored report {report_id} — {location}")

def load_all_reports_into_rag():
    reports    = get_all_reports()
    store      = load_rag_store()
    stored_ids = {item["id"] for item in store}
    count      = 0

    print(f"RAG: checking {len(reports)} reports...")

    for report in reports:
        if str(report["id"]) not in stored_ids:
            store_incident_in_rag(
                report_id   = report["id"],
                location    = report["location_name"],
                description = report["description"],
                severity    = report["severity"]
            )
            count += 1

    print(f"RAG: {count} new reports added to rag_store.json")

def sql_keyword_search(query, n_results=3):
    try:
        from database import get_conn
        conn  = get_conn()

        words = [
            w.strip("?.,!") for w in query.lower().split()
            if len(w.strip("?.,!")) > 3
        ]

        if not words:
            rows = conn.execute(
                """SELECT location_name, description
                   FROM incident_reports
                   ORDER BY reported_at DESC
                   LIMIT ?""",
                (n_results,)
            ).fetchall()
            conn.close()
            return [
                f"{r['location_name']}: {r['description']}"
                for r in rows
            ]

        conditions = []
        params     = []
        for word in words:
            conditions.append(
                "(LOWER(location_name) LIKE ? "
                "OR LOWER(description) LIKE ?)"
            )
            params.extend([f"%{word}%", f"%{word}%"])

        rows = conn.execute(
            f"""SELECT location_name, description
                FROM incident_reports
                WHERE {' OR '.join(conditions)}
                ORDER BY severity DESC, reported_at DESC
                LIMIT ?""",
            params + [n_results]
        ).fetchall()
        conn.close()

        if rows:
            return [
                f"{r['location_name']}: {r['description']}"
                for r in rows
            ]

        # No keyword matches — return most recent reports
        conn = get_conn()
        rows = conn.execute(
            """SELECT location_name, description
               FROM incident_reports
               ORDER BY reported_at DESC
               LIMIT ?""",
            (n_results,)
        ).fetchall()
        conn.close()
        return [
            f"{r['location_name']}: {r['description']}"
            for r in rows
        ]

    except Exception as e:
        print(f"SQL search error: {e}")
        return []
    
def search_past_incidents(query, n_results=3):
    store = load_rag_store()

    if store:
        # Try vector search
        query_embedding = get_embedding(query)

        if query_embedding is not None:
            # Score every stored incident
            scored = []
            for item in store:
                try:
                    score = cosine_similarity(
                        query_embedding,
                        item["embedding"]
                    )
                    scored.append((score, item["text"]))
                except Exception:
                    continue

            if scored:
                # Sort highest similarity first
                scored.sort(key=lambda x: x[0], reverse=True)

                top = scored[:n_results]
                print(
                    f"RAG vector search: top scores = "
                    f"{[round(s, 3) for s, _ in top]}"
                )
                return [text for score, text in top]

    # Fallback to SQL keyword search
    print("RAG: using SQL keyword search fallback")
    return sql_keyword_search(query, n_results)

def tool_check_zone_safety(zone_name):
    
    zones = get_all_zones()

    # Find the zone whose name best matches what was asked
    for zone in zones:
        if (zone_name.lower() in zone["name"].lower() or
                zone["name"].lower() in zone_name.lower()):
            return (
                f"{zone['name']} is currently "
                f"{zone['safety_level'].upper()}. "
                f"{zone['description']}."
            )

    # No match found — list all zones
    all_names = ", ".join(
        f"{z['name']} ({z['safety_level']})" for z in zones
    )
    return f"Zone not found. All known zones: {all_names}"


def decide_tool_and_extract(question):
    system = """You are a routing agent for a campus safety app.
Read the question and respond in exactly this format with two lines:
TOOL: check_zone
VALUE: location name

Or:
TOOL: past_incidents
VALUE: search query

Or:
TOOL: general
VALUE:

Rules:
- check_zone: question is about safety of a specific place right now
- past_incidents: question is about past events or incident history
- general: safety advice or anything else

Only reply with the two lines. Nothing else."""

    response = ask_ollama(question, system)

    # Parse the two line response
    tool  = "general"
    value = ""

    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("TOOL:"):
            raw = line.replace("TOOL:", "").strip().lower()
            if "check_zone" in raw:
                tool = "check_zone"
            elif "past" in raw or "incident" in raw:
                tool = "past_incidents"
            else:
                tool = "general"
        elif line.startswith("VALUE:"):
            value = line.replace("VALUE:", "").strip()

    return tool, value

# def run_agent(user_question, chat_history=None):
   
#     if chat_history is None:
#         chat_history = []

#     # ── Step 1: One call — decide tool and extract value ──────────────────────
#     tool_choice, extracted_value = decide_tool_simple(user_question)

#     # ── Step 2: Run the chosen tool — no Ollama, runs instantly ───────────────
#     tool_result = ""

#     if tool_choice == "check_zone" and extracted_value:
#         tool_result = tool_check_zone_safety(extracted_value)

#     elif tool_choice == "past_incidents":
#         query     = extracted_value if extracted_value else user_question
#         incidents = search_past_incidents(query, n_results=3)

#         if incidents:
#             tool_result = (
#                 f"Found {len(incidents)} relevant past incidents:\n" +
#                 "\n".join(f"- {inc}" for inc in incidents)
#             )
#         else:
#             tool_result = "No past incidents found for this query."

#     # ── Step 3: Search RAG for extra context — no Ollama, runs instantly ──────
#     rag_incidents = search_past_incidents(user_question, n_results=2)
#     rag_text      = (
#         "\n".join(f"- {inc}" for inc in rag_incidents)
#         if rag_incidents
#         else "No relevant history found."
#     )

#     # ── Step 4: Build context and generate answer — 1 Ollama call ─────────────
#     zones         = get_all_zones()
#     recent        = get_recent_reports(days=7)
#     hour          = datetime.now().hour

#     unsafe_zones  = [z["name"] for z in zones
#                      if z["safety_level"] == "unsafe"]
#     caution_zones = [z["name"] for z in zones
#                      if z["safety_level"] == "caution"]

#     # Only use last 4 messages from history
#     # Using too much history makes the prompt very long and slow
#     history_text = ""
#     for msg in chat_history[-4:]:
#         role          = "Student" if msg["role"] == "user" else "Assistant"
#         history_text += f"{role}: {msg['content']}\n"

#     system = f"""You are CampusSafe, a campus safety assistant for DAVV Indore.
# Answer using the information below. Be specific and brief. 2-3 sentences only.

# Time: {hour}:00
# Unsafe zones: {', '.join(unsafe_zones) if unsafe_zones else 'none'}
# Caution zones: {', '.join(caution_zones) if caution_zones else 'none'}
# Incidents last 7 days: {len(recent)}
# Tool result: {tool_result if tool_result else 'none'}
# Past incidents from memory:
# {rag_text}
# Emergency: Police 100, Women Helpline 1090"""

#     prompt = f"{history_text}Student: {user_question}\nAssistant:"

#     yield from stream_ollama(prompt,system)


def run_agent_stream(user_question, chat_history=None):
    if chat_history is None:
        chat_history = []

    try:
        tool_choice, extracted_value = decide_tool_simple(user_question)
    except Exception:
        tool_choice, extracted_value = "general", ""

    tool_result = ""
    try:
        if tool_choice =="check_zone" and extracted_value:
            tool_result = tool_check_zone_safety(extracted_value)
        elif tool_choice == "past_incidents":
            query = extracted_value if extracted_value else user_question
            incidents = search_past_incidents(query, n_results=3)
            if incidents:
                tool_result = (
                    f"Found{len(incidents)} relevant past incidents:\n"+"\n".join(f"-{inc}" for inc in incidents)
                )
    except Exception:
        tool_result = ""

    rag_text = ""
    try:
        rag_incidents = search_past_incidents(user_question, n_results=2)
        rag_text = (
            "\n".join(f"-{inc}" for inc in rag_incidents)
            if rag_incidents
            else "No relevant history found."
        )

    except Exception:
        rag_text = "No relevant history found."

    try:
        zones = get_all_zones()
        recent = get_recent_reports()
        hour = datetime.now().hour
        unsafe_zones = [z["name"] for z in zones if z["safety_level"]== "unsafe"]
        caution_zones = [z["name"] for z in zones if z["safety_level"]=="caution"]

        history_text = ""
        for msg in chat_history[-4:]:
            role = "Student" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

        system = f"""You are CampusSafe, a campus safety assistant for DAVV Indore. 
        Answer using the information below. Be specific and brief. 2-3 sentences only.
        
        Time: {hour}:00
        Unsafe zones: {', '.join(unsafe_zones) if unsafe_zones else 'none'}
        Caution zones: {', '.join(caution_zones) if caution_zones else 'none'}
        Incidents last 7 days: {len(recent)}
        Tool result: {tool_result if tool_result else 'none'}
        Relevant past incidents: {rag_text}
        Emergency: Police 100, Women Helpline 1090"""
        
        prompt = f"{history_text}Student: {user_question}\nAssistant:"
        
    except Exception as e:
        yield f"Error building context: {str(e)}"
        return
    

    yield from stream_ollama(prompt, system)

def find_nearest_zone(lat,lon):
    zones = get_all_zones()
    if not zones:
        return None
    
    def distance(z):
        return((z["latitude"]-lat)**2 + (z["longitude"]-lon)**2)**0.5
    
    nearest = min(zones,key=distance)
    return nearest

# CONCEPT 4 — AUTO ZONE UPDATER
#
# Called after every new incident report is submitted.
# Scores every zone based on:
#   - how many recent reports mention that zone
#   - severity of those reports
#   - sentiment score of the descriptions
#
# Updates the database automatically.
# The map shows new colors on next page load.

def auto_update_zones():
    zones   = get_all_zones()
    reports = get_recent_reports(days=30)
    changes = []

    for zone in zones:
        old_level = zone["safety_level"]

        # Find reports that mention this zone
        zone_reports = [
            r for r in reports
            if zone["name"].lower() in r["location_name"].lower()
            or r["location_name"].lower() in zone["name"].lower()
        ]

        # No reports for this zone — leave it as is
        if not zone_reports:
            continue

        # Score this zone based on its reports
        total_score = 0
        for r in zone_reports:
            sentiment_score = analyze_sentiment(r["description"])
            # Add both severity and sentiment score
            # This double-weights dangerous sounding reports
            total_score += r["severity"] + sentiment_score

        # Average score across all reports for this zone
        avg_score = total_score / len(zone_reports)

        # Convert average score to safety level
        # avg_score is between 2 (both 1) and 10 (both 5)
        if avg_score >= 5.0:
            new_level = "unsafe"
        elif avg_score >= 3.5:
            new_level = "caution"
        else:
            new_level = "safe"

        # Only update if the level actually changed
        if new_level != old_level:
            update_zone_safety(zone["id"], new_level)
            changes.append(
                f"{zone['name']}: {old_level} → {new_level}"
            )

    return changes


# SAFETY SUMMARY —  on the home page

def get_safety_summary():
    zones   = get_all_zones()
    reports = get_recent_reports(days=1)
    hour    = datetime.now().hour

    unsafe_count  = sum(1 for z in zones if z["safety_level"] == "unsafe")
    caution_count = sum(1 for z in zones if z["safety_level"] == "caution")
    unsafe_names  = [z["name"] for z in zones
                     if z["safety_level"] == "unsafe"]

    system = (
        "You are a campus safety assistant. "
        "Write a short 2 sentence safety briefing for students. "
        "Be direct and practical. Do not start with a greeting."
    )

    prompt = (
        f"Time: {hour}:00 hours\n"
        f"Unsafe zones ({unsafe_count}): "
        f"{', '.join(unsafe_names) if unsafe_names else 'none'}\n"
        f"Caution zones: {caution_count}\n"
        f"Incidents in last 24 hours: {len(reports)}\n\n"
        f"Write a brief safety status update for DAVV students."
    )
    return ask_ollama(prompt,system)
