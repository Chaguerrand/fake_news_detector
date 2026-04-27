import streamlit as st
import requests
import os
import time
import random
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
import json
from dotenv import load_dotenv

load_dotenv()

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"]

gcp_creds = os.getenv("GCP_SERVICE_ACCOUNT")
if gcp_creds:
    creds_json = json.loads(gcp_creds)
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("FakeNewsDB").sheet1
    sheet2 = client.open("FakeNewsDB").worksheet("Sheet2")
else:
    sheet = None
    sheet2 = None

# ── SESSION STATE ────────────────────────────────────────────
if "url_count" not in st.session_state:
    st.session_state["url_count"] = 0
if "clear_count" not in st.session_state:
    st.session_state["clear_count"] = 0
if "result" not in st.session_state:
    st.session_state["result"] = None
if "text_to_analyze" not in st.session_state:
    st.session_state["text_to_analyze"] = ""
if "elapsed" not in st.session_state:
    st.session_state["elapsed"] = 0
if "feedback_given" not in st.session_state:
    st.session_state["feedback_given"] = False
if "row_index" not in st.session_state:
    st.session_state["row_index"] = None

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_READY = True

st.set_page_config(
    page_title="Fake News Detector",
    page_icon="📰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .verdict-fake {
        background-color: #ff4b4b22;
        border: 1px solid #ff4b4b;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: bold;
        color: #ff4b4b;
    }
    .verdict-real {
        background-color: #21c35422;
        border: 1px solid #21c354;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: bold;
        color: #21c354;
    }
    .verdict-inconclusive {
        background-color: #ffd70022;
        border: 1px solid #ffd700;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: bold;
        color: #ffd700;
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────────
st.title("📰 Fake News Detector 📰")
st.caption("Détection et catégorisation de Fake News")
st.divider()

# ── LOAD DATA (définie une seule fois) ───────────────────────
@st.cache_data(ttl=60)
def load_data(_sheet):
    return _sheet.get_all_records()

# ── TABS ─────────────────────────────────────────────────────
tab_url, tab_text, tab_jeu, tab_quizz = st.tabs([
    "Analyser depuis une URL",
    "Analyser depuis du texte brut",
    "Petit jeu d'Alex",
    "Quizz pour un platiste"
])

with tab_url:
    col_url, col_open = st.columns([5, 1])
    with col_url:
        url_input = st.text_input(
            "URL de l'article",
            placeholder="https://www.reuters.com/...",
            key=f"url_input_{st.session_state['url_count']}",
        )
    with col_open:
        st.markdown("<br>", unsafe_allow_html=True)
        if url_input:
            st.link_button("🔗 Ouvrir", url_input, use_container_width=True)
        else:
            st.button("🔗 Ouvrir", disabled=True, use_container_width=True)
    st.divider()
    col_btn, col_clear = st.columns([5, 1])
    with col_btn:
        st.button("🔍 Lancer l'analyse", type="primary", use_container_width=True, key="analyze_url")
    with col_clear:
        if st.button("🗑️ Effacer", use_container_width=True, key="clear_url"):
            st.session_state["clear_count"] += 1
            st.session_state["url_count"] += 1
            st.session_state["result"] = None
            st.session_state["text_to_analyze"] = ""
            st.session_state["elapsed"] = 0
            st.session_state["feedback_given"] = False
            st.session_state["row_index"] = None
            st.session_state["show_cleared"] = True
            st.rerun()
    if st.session_state.get("show_cleared"):
        st.success("🗑️ Champs effacés")
        st.session_state["show_cleared"] = False

with tab_text:
    text_input = st.text_area(
        "Collez ici le contenu de l'article",
        height=200,
        placeholder="Entrez le texte de l'article à analyser...",
        key=f"input_text_{st.session_state['clear_count']}",
    )
    st.divider()
    col_btn, col_clear = st.columns([5, 1])
    with col_btn:
        st.button("🔍 Lancer l'analyse", type="primary", use_container_width=True, key="analyze_text")
    with col_clear:
        if st.button("🗑️ Effacer", use_container_width=True, key="clear_text"):
            st.session_state["clear_count"] += 1
            st.session_state["url_count"] += 1
            st.session_state["result"] = None
            st.session_state["text_to_analyze"] = ""
            st.session_state["elapsed"] = 0
            st.session_state["feedback_given"] = False
            st.session_state["row_index"] = None
            st.session_state["show_cleared"] = True
            st.rerun()
    if st.session_state.get("show_cleared"):
        st.success("🗑️ Champs effacés")
        st.session_state["show_cleared"] = False

with tab_jeu:
    if sheet is None:
        st.warning("⚠️ Google Sheets non configuré.")
    else:
        menu = st.radio("Choisir une action", ["Ajouter une news", "Voir les news"])

        def add_news(title, content, label):
            sheet.append_row([title, content, label, "pending"])

        def delete_news(title):
            rows = sheet.get_all_records()
            for i, row in enumerate(rows, start=2):
                if row["title"] == title:
                    sheet.delete_rows(i)
                    break

        df = load_data(sheet)

        if menu == "Ajouter une news":
            title = st.text_input("Titre")
            content = st.text_area("Contenu")
            label = st.selectbox("Type", ["fake", "real"])
            if st.button("Ajouter"):
                add_news(title, content, label)
                st.success("Ajouté à Google Sheets ✅")
                st.rerun()

        elif menu == "Voir les news":
            if len(df) > 0:
                st.dataframe(df)
                selected = st.selectbox("Valider une news", [row["title"] for row in df])
                if st.button("Valider"):
                    for i, row in enumerate(sheet.get_all_records(), start=2):
                        if row["title"] == selected:
                            sheet.update_cell(i, 4, "valide")
                            break
                    st.success("News validée ✅")
                selected_del = st.selectbox("Supprimer une news", [row["title"] for row in df])
                if st.button("🗑️ Supprimer"):
                    delete_news(selected_del)
                    st.success("News supprimée ✅")
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

    # stocker les questions en session_state pour éviter le re-sample
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
            user_choice = st.radio("Votre réponse :", ["Vrai", "Faux"], key=f"quiz_{i}")
            if st.button("Valider", key=f"btn_{i}"):
                user_bool = user_choice == "Vrai"
                if i not in st.session_state.answered:
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

# ── ANALYSE ──────────────────────────────────────────────────
analyze = st.session_state.get("analyze_url") or st.session_state.get("analyze_text")

if analyze:
    st.session_state["feedback_given"] = False
    st.session_state["row_index"] = None

    if url_input:
        source = "streamlit_url"
        with st.spinner("Extraction en cours..."):
            try:
                response_url = requests.get(
                    url_input,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                )
                soup = BeautifulSoup(response_url.content, "lxml")
                text_to_analyze = " ".join([p.text for p in soup.find_all("p")])
                st.success(f"Le texte analysé fait {len(text_to_analyze)} caractères")
            except Exception as e:
                st.error(f"❌ Impossible d'extraire le texte : {e}")
                st.stop()

    elif text_input:
        source = "streamlit_txt"
        text_to_analyze = text_input
        st.success(f"Le texte analysé fait {len(text_to_analyze)} caractères")

    else:
        st.error("❌ Aucun texte à analyser. Collez du texte ou entrez une URL.")
        st.stop()

    if len(text_to_analyze.strip()) < 200:
        st.error("❌ Texte trop court. Veuillez saisir au moins 200 caractères.")
        st.stop()

    with st.spinner("Analyse en cours..."):
        if API_READY:
            try:
                start = time.time()
                response = requests.post(
                    f"{API_URL}/predict",
                    json={"text_to_analyze": text_to_analyze, "source": source},
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                st.session_state["result"] = data
                st.session_state["text_to_analyze"] = text_to_analyze
                st.session_state["elapsed"] = round(time.time() - start, 2)
                st.session_state["row_index"] = data.get("row_index")
            except requests.exceptions.ConnectionError:
                st.error(f"❌ API non joignable sur {API_URL}")
                st.stop()
            except Exception as e:
                st.error(f"❌ Erreur API : {e}")
                st.stop()

# ── RÉSULTAT ─────────────────────────────────────────────────
if st.session_state["result"]:
    result = st.session_state["result"]
    text_to_analyze = st.session_state["text_to_analyze"]
    elapsed = st.session_state["elapsed"]

    st.divider()
    st.subheader("Résultat")

    if result["Verdict"] == "FAKE":
        st.markdown(f'<div class="verdict-fake"><span style="font-size: 2rem;">🚨 FAKE NEWS</span><br>{result["Indice de confiance"]:.1%}</div>', unsafe_allow_html=True)
        if result["Indice de confiance"] >= 0.92:
            if st.button("🔍 Chercher des sources vérifiées", use_container_width=True):
                with st.spinner("Recherche de sources en cours..."):
                    try:
                        response_fc = requests.post(
                            f"{API_URL}/fact_check",
                            json={"text_to_analyze": text_to_analyze, "row_index": st.session_state["row_index"]},
                            timeout=60,
                        )
                        response_fc.raise_for_status()
                        result_fc = response_fc.json()
                        st.markdown(result_fc["result"])
                    except Exception as e:
                        st.error(f"❌ Erreur fact-check : {e}")

    elif result["Verdict"] == "REAL":
        st.markdown(f'<div class="verdict-real"><span style="font-size: 2rem;">✅ ARTICLE FIABLE</span><br>{result["Indice de confiance"]:.1%}</div>', unsafe_allow_html=True)

    else:
        label_hint = "Relativement fiable" if result["Label"] == "REAL" else "Relativement fake"
        st.markdown(f'<div class="verdict-inconclusive"><span style="font-size: 2rem;">⚠️ NON CONCLUANT</span><br>{label_hint}<br>{result["Indice de confiance"]:.1%}</div>', unsafe_allow_html=True)

    st.caption(f"⏱️ Analyse effectuée en {elapsed}s")

    # ── FEEDBACK ─────────────────────────────────────────────
    if sheet2 and st.session_state["row_index"]:
        st.markdown("<br>", unsafe_allow_html=True)
        if not st.session_state["feedback_given"]:
            st.markdown("**Ce résultat vous semble correct ?**")
            col_up, col_down = st.columns(2)
            with col_up:
                if st.button("👍", use_container_width=True, key="feedback_good"):
                    sheet2.update_cell(st.session_state["row_index"], 7, "good")
                    st.session_state["feedback_given"] = True
                    st.rerun()
            with col_down:
                if st.button("👎", use_container_width=True, key="feedback_bad"):
                    sheet2.update_cell(st.session_state["row_index"], 7, "bad")
                    st.session_state["feedback_given"] = True
                    st.rerun()
        else:
            st.success("Merci pour votre retour !")

# ── FOOTER ───────────────────────────────────────────────────
st.divider()
st.caption("Martin Cornud - Alex Delrieu - Charles Jégo")
st.caption("Le Wagon - #2251")
