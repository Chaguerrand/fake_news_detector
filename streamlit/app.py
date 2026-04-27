import streamlit as st
import requests
import os
import time
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
<<<<<<< HEAD

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "/Users/alexdelrieu/code/Chaguerrand/fake_news_detector/streamlit/service_account.json",
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open("FakeNewsDB").sheet1
=======
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
else:
    sheet = None
>>>>>>> ff09da04bcd49256198fb792355aaa6dc5dad587


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

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Fake News Detector",
    page_icon="📰",
    layout="centered"
)

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

st.title("📰 Fake News Detector 📰")
st.caption("Détection et catégorisation de Fake News")
st.divider()

tab_url, tab_text, tab_jeu = st.tabs([
    "Analyser depuis une URL",
    "Analyser depuis du texte brut",
    "Petit jeu d'Alex"
])
with tab_url:

    col_url, col_open = st.columns([5, 1])

    url_input = st.text_input(
        "URL de l'article",
        placeholder="https://www.reuters.com/...",
        key=f"url_input_{st.session_state['url_count']}",
    )

    analyze_url = st.button(
        "🔍 Lancer l'analyse",
        type="primary",
        key="analyze_url"
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
            st.session_state["show_cleared"] = True
            st.rerun()
    if st.session_state.get("show_cleared"):
        st.success("🗑️ Champs effacés")
        st.session_state["show_cleared"] = False

<<<<<<< HEAD
    analyze_text = st.button(
        "🔍 Lancer l'analyse",
        type="primary",
        key="analyze_text"
    )

with tab_jeu:

    menu = st.radio("Choisir une action", ["Ajouter une news", "Voir les news"])

    def load_data():
        return sheet.get_all_records()

    def add_news(title, content, label):
        sheet.append_row(["", title, content, label, "pending"])

    def delete_news(title):
        rows = sheet.get_all_records()
        for i, row in enumerate(rows, start=2):
            if row["title"] == title:
                sheet.delete_rows(i)
                break

    df = load_data()

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

            selected = st.selectbox(
                "Valider une news",
                [row["title"] for row in df]
            )

            if st.button("Valider"):
                for i, row in enumerate(sheet.get_all_records(), start=2):
                    if row["title"] == selected:
                        sheet.update_cell(i, 5, "valide")
                        break
                st.success("News validée ✅")

            selected_del = st.selectbox(
                "Supprimer une news",
                [row["title"] for row in df]
            )

            if st.button("🗑️ Supprimer"):
                delete_news(selected_del)
                st.success("News supprimée ✅")
                st.rerun()

analyze = analyze_url or analyze_text

=======
with tab_jeu:

    if sheet is None:
        st.warning("⚠️ Google Sheets non configuré.")
    else:
        menu = st.radio("Choisir une action", ["Ajouter une news", "Voir les news"])

        @st.cache_data(ttl=60)
        def load_data(_sheet):
            return _sheet.get_all_records()

        def add_news(title, content, label):
            sheet.append_row(["", title, content, label, "pending"])

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

                selected = st.selectbox(
                    "Valider une news",
                    [row["title"] for row in df]
                )

                if st.button("Valider"):
                    for i, row in enumerate(sheet.get_all_records(), start=2):
                        if row["title"] == selected:
                            sheet.update_cell(i, 5, "valide")
                            break
                    st.success("News validée ✅")

                selected_del = st.selectbox(
                    "Supprimer une news",
                    [row["title"] for row in df]
                )

                if st.button("🗑️ Supprimer"):
                    delete_news(selected_del)
                    st.success("News supprimée ✅")
                    st.rerun()

# analyse
analyze = st.session_state.get("analyze_url") or st.session_state.get("analyze_text")

>>>>>>> ff09da04bcd49256198fb792355aaa6dc5dad587
if analyze:

    if analyze_url and analyze_text:
        st.error("❌ Choisis soit URL soit texte, pas les deux.")
        st.stop()

    if analyze_url:
        try:
            response_url = requests.get(url_input)
            soup = BeautifulSoup(response_url.content, "lxml")
            text_to_analyze = " ".join([p.text for p in soup.find_all("p")])
        except Exception as e:
            st.error(f"❌ Extraction impossible : {e}")
            st.stop()

    elif analyze_text:
        text_to_analyze = text_input

    if len(text_to_analyze.strip()) < 200:
        st.error("❌ Texte trop court")
        st.stop()

    with st.spinner("Analyse..."):
        try:
            start = time.time()

            response = requests.post(
                f"{API_URL}/predict",
                json={"text_to_analyze": text_to_analyze},
                timeout=60
            )

            response.raise_for_status()

            st.session_state["result"] = response.json()
            st.session_state["text_to_analyze"] = text_to_analyze
            st.session_state["elapsed"] = round(time.time() - start, 2)

        except Exception as e:
            st.error(f"❌ API error : {e}")
            st.stop()

if st.session_state["result"]:

    result = st.session_state["result"]
    elapsed = st.session_state["elapsed"]

    st.divider()
    st.subheader("Résultat")

    if result["Verdict"] == "FAKE":
        st.markdown(
            f'<div class="verdict-fake">🚨 FAKE NEWS<br>{result["Indice de confiance"]:.1%}</div>',
            unsafe_allow_html=True
        )

    elif result["Verdict"] == "REAL":
        st.markdown(
            f'<div class="verdict-real">✅ FIABLE<br>{result["Indice de confiance"]:.1%}</div>',
            unsafe_allow_html=True
        )

    else:
        st.markdown(
            f'<div class="verdict-inconclusive">⚠️ NON CONCLUANT<br>{result["Indice de confiance"]:.1%}</div>',
            unsafe_allow_html=True
        )

    st.caption(f"⏱️ Analyse en {elapsed}s")


st.divider()
st.caption("Martin Cornud - Alex Delrieu - Charles Jégo")
st.caption("Le Wagon - #2251")
