import streamlit as st
import os
import json
import random
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Jeu", page_icon="🎮", layout="centered", initial_sidebar_state="collapsed")

# Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gcp_creds = os.getenv("GCP_SERVICE_ACCOUNT")
if gcp_creds:
    creds_json = json.loads(gcp_creds)
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("FakeNewsDB").sheet1
else:
    sheet = None

@st.cache_data(ttl=60)
def load_data(_sheet):
    return _sheet.get_all_records()

st.title("🎮 Petit jeu d'Alex le platiste")
st.divider()

tab_jeu, tab_quizz = st.tabs(["Ajouter une news", "Quizz pour un platiste"])

with tab_jeu:
    if sheet is None:
        st.warning("⚠️ Google Sheets non configuré.")
    else:
        def add_news(title, content, label):
            sheet.append_row([title, content, label, "pending"])

        st.subheader("Ajouter une news")
        title = st.text_input("Titre")
        content = st.text_area("Contenu")
        label = st.selectbox("Type", ["fake", "real"])
        if st.button("Ajouter"):
            add_news(title, content, label)
            st.success("Ajouté à Google Sheets ✅")
            st.rerun()

with tab_quizz:

    def load_facts():
        if sheet is None:
            return {}
        data = load_data(sheet)
        facts = {}
        for row in data:
            if row["status"] == "valide":
                if row["label"] == "real":
                    facts[row["content"]] = True
                elif row["label"] == "fake":
                    facts[row["content"]] = False
        return facts

    if "quiz_facts" not in st.session_state:
        all_facts = load_facts()
        st.session_state["quiz_facts"] = dict(random.sample(list(all_facts.items()), min(10, len(all_facts)))) if all_facts else {}
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "answered" not in st.session_state:
        st.session_state.answered = {}

    facts = st.session_state["quiz_facts"]

    st.subheader("Quiz Fake News")

    if not facts:
        st.warning("⚠️ Aucune news disponible pour le quiz.")
    else:
        for i, (fact, answer) in enumerate(facts.items(), 1):
            st.write(f"**{i}. {fact}**")
            col_vrai, col_faux, _ = st.columns([1, 1, 1])
            with col_vrai:
                vrai = st.button("✅ Vrai", key=f"vrai_{i}", use_container_width=True)
            with col_faux:
                faux = st.button("❌ Faux", key=f"faux_{i}", use_container_width=True)

            if (vrai or faux) and i not in st.session_state.answered:
                user_bool = vrai
                if user_bool == answer:
                    st.success("✅ Correct")
                    st.session_state.score += 1
                else:
                    st.error("❌ Faux")
                st.session_state.answered[i] = True

        st.write(f"🏁 Score final : {st.session_state.score}/{len(facts)}")

        if st.button("🔄 Nouveau quiz"):
            all_facts = load_facts()
            st.session_state["quiz_facts"] = dict(random.sample(list(all_facts.items()), min(10, len(all_facts)))) if all_facts else {}
            st.session_state.score = 0
            st.session_state.answered = {}
            st.rerun()

st.divider()
st.caption("Martin Cornud - Alex Delrieu - Charles Jégo")
st.caption("Le Wagon - #2251")
