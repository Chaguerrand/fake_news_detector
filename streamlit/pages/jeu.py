import streamlit as st
import os
import json
import random
from collections import defaultdict
from datetime import date, datetime
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Jeu", page_icon="🎮", layout="centered", initial_sidebar_state="collapsed")

# ── GOOGLE SHEETS ─────────────────────────────────────────────
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gcp_creds = os.getenv("GCP_SERVICE_ACCOUNT")
if gcp_creds:
    creds_json = json.loads(gcp_creds)
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("FakeNewsDB").sheet1
    sheet3 = client.open("FakeNewsDB").worksheet("Sheet3")
else:
    sheet = None
    sheet3 = None

@st.cache_data(ttl=60)
def load_data(_sheet):
    return _sheet.get_all_records()

@st.cache_data(ttl=30)
def load_leaderboard(_sheet3):
    if _sheet3 is None:
        return [], []
    data = _sheet3.get_all_records()
    today = date.today().strftime("%Y-%m-%d")

    all_time = defaultdict(list)
    today_scores = defaultdict(list)

    for row in data:
        name = str(row.get("name", "")).strip()
        score = row.get("score", 0)
        date_str = str(row.get("date", "")).strip()
        if not name:
            continue
        all_time[name].append(score)
        if date_str == today:
            today_scores[name].append(score)

    all_time_top = sorted(
        [{"name": k, "score": round(sum(v) / len(v), 1)} for k, v in all_time.items()],
        key=lambda x: x["score"], reverse=True
    )[:5]

    today_top = sorted(
        [{"name": k, "score": round(sum(v) / len(v), 1)} for k, v in today_scores.items()],
        key=lambda x: x["score"], reverse=True
    )[:5]

    return today_top, all_time_top

# ── SESSION STATE ─────────────────────────────────────────────
if "quiz_facts" not in st.session_state:
    st.session_state["quiz_facts"] = []
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = {}
if "score_saved" not in st.session_state:
    st.session_state["score_saved"] = False

# ── PAGE ──────────────────────────────────────────────────────
st.title("🎮 Petit jeu d'Alex le platiste")
st.divider()

tab_quizz, tab_jeu = st.tabs(["Quizz pour un platiste", "Ajouter une news"])

with tab_quizz:

    def load_facts():
        if sheet is None:
            return []
        data = load_data(sheet)
        facts = []
        for row in data:
            if row.get("status") == "valide" and row.get("label") in ("real", "fake"):
                facts.append({
                    "title": str(row.get("title", "Sans titre")).strip(),
                    "content": str(row.get("content", "")).strip(),
                    "answer": row.get("label") == "real"
                })
        return facts

    if not st.session_state["quiz_facts"]:
        all_facts = load_facts()
        st.session_state["quiz_facts"] = random.sample(all_facts, min(10, len(all_facts))) if all_facts else []

    facts = st.session_state["quiz_facts"]

    st.subheader("Quiz Fake News")

    if not facts:
        st.warning("⚠️ Aucune news disponible pour le quiz.")
    else:
        for i, item in enumerate(facts, 1):
            title_safe = item["title"].replace("*", "\\*").replace("_", "\\_")
            st.markdown(f"**{i}. {title_safe}**")
            st.caption(item["content"])
            col_vrai, col_faux, _ = st.columns([1, 1, 1])
            with col_vrai:
                vrai = st.button("✅ Vrai", key=f"vrai_{i}", use_container_width=True)
            with col_faux:
                faux = st.button("❌ Faux", key=f"faux_{i}", use_container_width=True)

            if (vrai or faux) and i not in st.session_state.answered:
                user_bool = vrai
                if user_bool == item["answer"]:
                    st.success("✅ Correct")
                    st.session_state.score += 1
                else:
                    st.error("❌ Faux")
                st.session_state.answered[i] = True

        st.divider()
        quiz_complete = len(st.session_state.answered) == len(facts)
        st.markdown(f"### 🏁 Score : {st.session_state.score}/{len(facts)}")

        if quiz_complete and sheet3:
            if not st.session_state["score_saved"]:
                st.markdown("**Enregistre ton score sur le leaderboard !**")
                player_name = st.text_input("Ton prénom", key="player_name")
                if st.button("💾 Enregistrer", type="primary") and player_name.strip():
                    sheet3.append_row([
                        datetime.now().strftime("%Y-%m-%d"),
                        player_name.strip(),
                        st.session_state.score
                    ])
                    st.session_state["score_saved"] = True
                    load_leaderboard.clear()
                    st.rerun()
            else:
                st.success("✅ Score enregistré !")

        if st.button("🔄 Nouveau quiz"):
            all_facts = load_facts()
            st.session_state["quiz_facts"] = random.sample(all_facts, min(10, len(all_facts))) if all_facts else []
            st.session_state.score = 0
            st.session_state.answered = {}
            st.session_state["score_saved"] = False
            st.rerun()


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


# ── LEADERBOARD ───────────────────────────────────────────────
st.divider()
st.markdown("### 🏆 Leaderboard")

today_top, all_time_top = load_leaderboard(sheet3)

col_today, col_alltime = st.columns(2)

medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

with col_today:
    st.markdown("**📅 Top 5 aujourd'hui**")
    if today_top:
        for i, entry in enumerate(today_top):
            st.markdown(f"{medals[i]} **{entry['name']}** — {entry['score']}/10")
    else:
        st.caption("Aucun score aujourd'hui")

with col_alltime:
    st.markdown("**🌍 Top 5 all time**")
    if all_time_top:
        for i, entry in enumerate(all_time_top):
            st.markdown(f"{medals[i]} **{entry['name']}** — {entry['score']}/10")
    else:
        st.caption("Aucun score enregistré")

# ── FOOTER ────────────────────────────────────────────────────
st.divider()
st.caption("Martin Cornud - Alex Delrieu - Charles Jégo")
st.caption("Le Wagon - #2251")
