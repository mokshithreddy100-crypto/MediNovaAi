
import os
import sqlite3
from datetime import date
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "medinova.db"

st.set_page_config(page_title="MediNova AI", page_icon="🧬", layout="wide")

AI_INSTRUCTIONS = """
You are MediNova AI, an educational health-science assistant.
Explain general health, biology, biotechnology, and pharmacy concepts in clear language.
Do not diagnose, triage, prescribe, recommend medicine doses, or tell users to start,
stop, or change treatment. Do not interpret an individual's lab values as a diagnosis.
Encourage a qualified healthcare professional for personal medical decisions.
For urgent or severe symptoms, advise contacting local emergency services or a clinician.
Do not request names, addresses, phone numbers, ID numbers, or other identifying details.
If asked for personalized treatment, explain this limitation and redirect to general education.
Clearly distinguish established facts from uncertainty. Never invent references or citations.
"""

def db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with db() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS health_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT NOT NULL,
            metric TEXT NOT NULL,
            value TEXT NOT NULL,
            unit TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )""")
        con.execute("""
        CREATE TABLE IF NOT EXISTS medicine_reference (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            general_use TEXT NOT NULL,
            safety_note TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            reviewed_on TEXT NOT NULL,
            review_status TEXT NOT NULL DEFAULT 'Needs professional review'
        )""")
        con.execute("""
        CREATE TABLE IF NOT EXISTS learning_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")

def ask_ai(question: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "AI is not connected yet. Add OPENAI_API_KEY as an environment variable "
            "on your own computer, then restart the app."
        )
    try:
        from openai import OpenAI
        client = openai(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-5.5")
        response = client.responses.create(
            model=model,
            instructions=AI_INSTRUCTIONS,
            input=question,
            store=False
        )
        return response.output_text
    except ImportError as e:
        raise RuntimeError(f"The OpenAI import is missing. Install it with: pip install openai")
    except Exception as exc:
        raise RuntimeError(f"AI request failed. Check your connection and API configuration. Details: {exc}")

init_db()

st.markdown("""
<style>
.main {background:#f4f8fc;}
.hero {padding:1.5rem;border-radius:18px;color:white;
background:linear-gradient(120deg,#064e78,#2563eb);}
div[data-testid="stMetric"] {background:white;padding:12px;border-radius:12px;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🧬 MediNova AI")
    st.caption("Smart healthcare • AI • Biotechnology")
    page = st.radio("Modules", [
        "Dashboard", "AI Health Education", "Health Monitor",
        "Biotechnology Hub", "Medicine Reference", "Lab Test Learning",
        "About & Safety"
    ])
    st.divider()
    ai_ready = bool(os.getenv("OPENAI_API_KEY", "").strip())
    st.caption("AI connection: " + ("Configured" if ai_ready else "Not configured"))

st.markdown('<div class="hero"><h1>🧬 MediNova AI</h1><p>Healthcare knowledge powered by modern science</p></div>', unsafe_allow_html=True)
st.warning("Educational software prototype, not a medical device. Do not enter personal identifiers or private medical records. It cannot diagnose or prescribe.")

if page == "Dashboard":
    st.subheader("Your healthcare science workspace")
    c1, c2, c3 = st.columns(3)
    c1.metric("Modules", "6")
    c2.metric("Local database", "SQLite")
    c3.metric("AI assistant", "Ready" if ai_ready else "Setup needed")
    st.markdown("### Development status")
    st.write("- AI assistant: optional API connection included.")
    st.write("- Health log: local prototype storage.")
    st.write("- Biotechnology learning: built-in topic library.")
    st.write("- Medicine reference: source-tracking structure; entries need professional verification.")
    st.write("- Lab tests: general educational explanations.")
    st.info("No clinical decision support is provided. A qualified team must review any real-world healthcare release.")

elif page == "AI Health Education":
    st.subheader("🤖 AI Health Education")
    st.write("Ask general questions about biology, health science, biotechnology, or pharmacy.")
    st.caption("Do not submit symptoms, personal lab reports, medication decisions, or identifying information.")
    with st.form("ai_form"):
        q = st.text_area("Your general science question", placeholder="Example: How does PCR amplify DNA?")
        send = st.form_submit_button("Ask MediNova AI")
    if send:
        if len(q.strip()) < 4:
            st.error("Please enter a little more detail.")
        elif len(q) > 1500:
            st.error("Please keep the question under 1,500 characters.")
        else:
            with st.spinner("Preparing an educational explanation..."):
                try:
                    st.markdown(ask_ai(q.strip()))
                except RuntimeError as e:
                    st.error(str(e))
    if not ai_ready:
        st.info("To enable AI, install the optional OpenAI package and configure an API key outside the app. Never paste an API key into this chat or a public code file.")

elif page == "Health Monitor":
    st.subheader("❤️ Personal measurement notebook")
    st.caption("Prototype only. Measurements are stored in a local SQLite file on this computer. Do not use this as a medical record.")
    with st.form("log_form"):
        d = st.date_input("Date", value=date.today())
        metric = st.selectbox("Measurement type", ["Heart rate", "Blood pressure", "Temperature", "Oxygen saturation", "Blood glucose", "Sleep duration", "Other"])
        value = st.text_input("Value as displayed by your device")
        unit = st.text_input("Unit (optional)")
        note = st.text_area("Non-identifying note (optional)")
        save = st.form_submit_button("Save locally")
    if save:
        if not value.strip():
            st.error("Enter a value first.")
        else:
            with db() as con:
                con.execute("INSERT INTO health_log (log_date, metric, value, unit, notes) VALUES (?, ?, ?, ?, ?)",
                            (str(d), metric, value.strip(), unit.strip(), note.strip()))
            st.success("Saved locally.")
    with db() as con:
        data = con.execute("SELECT log_date, metric, value, unit, notes FROM health_log ORDER BY log_date DESC, id DESC LIMIT 50").fetchall()
    if data:
        st.dataframe([{"Date":x[0],"Metric":x[1],"Value":x[2],"Unit":x[3],"Note":x[4]} for x in data], use_container_width=True)
    else:
        st.caption("No entries yet.")

elif page == "Biotechnology Hub":
    st.subheader("🧬 Biotechnology learning hub")
    topics = {
        "PCR": "Polymerase chain reaction (PCR) is a laboratory method used to make many copies of a selected DNA segment.",
        "Genomics": "Genomics studies the complete DNA content of an organism, including how genes interact.",
        "Bioinformatics": "Bioinformatics combines biology, computing, and statistics to analyze biological data.",
        "Pharmacogenomics": "Pharmacogenomics studies how genetic variation can influence responses to medicines. Clinical use needs validated tests and professional interpretation.",
        "Biomarkers": "A biomarker is a measurable biological characteristic that can indicate a biological process or response.",
        "Drug discovery": "Drug discovery involves target research, screening, chemistry, preclinical evaluation, and clinical studies."
    }
    selected = st.selectbox("Choose a topic", list(topics))
    st.info(topics[selected])
    note = st.text_area("Add your own study note")
    if st.button("Save study note"):
        if note.strip():
            with db() as con:
                con.execute("INSERT INTO learning_notes (topic, note, created_at) VALUES (?, ?, datetime('now'))", (selected, note.strip()))
            st.success("Study note saved locally.")
    with db() as con:
        notes = con.execute("SELECT topic, note, created_at FROM learning_notes ORDER BY id DESC LIMIT 10").fetchall()
    if notes:
        st.markdown("### Recent study notes")
        for t, n, dt in notes:
            with st.expander(f"{t} — {dt}"):
                st.write(n)

elif page == "Medicine Reference":
    st.subheader("💊 Medicine information framework")
    st.write("This version intentionally does not provide doses, treatment instructions, or self-medication advice.")
    st.info("The database includes fields for source name, source URL, review date, and professional review status. No medicine is marked verified by this prototype.")
    st.markdown("### Suggested data-review workflow")
    st.write("1. Obtain current official product information from an authorized source.")
    st.write("2. Have a registered pharmacist or qualified clinician review each entry.")
    st.write("3. Record the source, review date, and reviewer approval in a controlled database.")
    st.write("4. Recheck entries when official product information changes.")
    with db() as con:
        rows = con.execute("SELECT name, category, source_name, reviewed_on, review_status FROM medicine_reference ORDER BY name").fetchall()
    if rows:
        st.dataframe([{"Medicine":r[0],"Category":r[1],"Source":r[2],"Reviewed":r[3],"Status":r[4]} for r in rows], use_container_width=True)
    else:
        st.caption("No reviewed medicine records have been added yet.")
    st.caption("Do not treat search results or AI-generated text as verified prescribing information.")

elif page == "Lab Test Learning":
    st.subheader("🧪 Lab test learning")
    tests = {
        "Haemoglobin": "Haemoglobin is the oxygen-carrying protein in red blood cells.",
        "Fasting blood glucose": "This test measures blood glucose after a specified fasting period.",
        "Creatinine": "Creatinine is a waste product measured in blood and used with other information to assess kidney function.",
        "TSH": "Thyroid-stimulating hormone is involved in regulation of thyroid activity.",
        "Lipid profile": "A lipid profile measures blood fats such as cholesterol and triglycerides."
    }
    test = st.selectbox("Select a test", list(tests))
    st.info(tests[test])
    st.write("Reference intervals vary by laboratory and method. This module explains test concepts only; it does not interpret individual results.")

else:
    st.subheader("About & safety")
    st.markdown("""
    **Current status:** learning and software prototype.

    - No diagnosis, treatment recommendation, or medicine dosing.
    - No user account or cloud health-record storage.
    - Local SQLite records are not encrypted in this prototype.
    - AI calls, when enabled, send the question to the configured AI provider; only ask general educational questions.
    - Do not use real patient data for testing.

    Before any public release, the project needs clinical review, security testing, privacy assessment, accessibility testing, and regulatory review appropriate to its intended use in India.
    """)

st.divider()
st.caption("MediNova AI • Version 2 • Educational prototype")
