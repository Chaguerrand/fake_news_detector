import streamlit as st
import requests
import os
import time
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
import json
from dotenv import load_dotenv
import re

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

# ── TABS ─────────────────────────────────────────────────────
tab_url, tab_text = st.tabs([
    "Analyser depuis une URL",
    "Analyser depuis du texte brut",
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
            st.session_state["url_count"] += 1
            st.session_state["clear_count"] += 1
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
            st.session_state["url_count"] += 1
            st.session_state["clear_count"] += 1
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

# ── ANALYSE ──────────────────────────────────────────────────
analyze = st.session_state.get("analyze_url") or st.session_state.get("analyze_text")

if analyze:
    st.session_state["feedback_given"] = False
    st.session_state["row_index"] = None

    if st.session_state.get("analyze_url") and url_input:
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

    if result["Verdict"] == "FAKE":
        st.markdown(f'<div class="verdict-fake"><span style="font-size: 2rem;">🚨 FAKE NEWS</span><br>{result["Indice de confiance"]:.1%}</div>', unsafe_allow_html=True)
    elif result["Verdict"] == "REAL":
        st.markdown(f'<div class="verdict-real"><span style="font-size: 2rem;">✅ ARTICLE FIABLE</span><br>{result["Indice de confiance"]:.1%}</div>', unsafe_allow_html=True)
    else:
        label_hint = "Relativement fiable" if result["Label"] == "REAL" else "Relativement fake"
        st.markdown(f'<div class="verdict-inconclusive"><span style="font-size: 2rem;">⚠️ NON CONCLUANT</span><br>{label_hint}<br>{result["Indice de confiance"]:.1%}</div>', unsafe_allow_html=True)

    st.caption(f"⏱️ Analyse effectuée en {elapsed}s")

    if result["Verdict"] == "FAKE" and result["Indice de confiance"] >= 0.92:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Chercher des sources vérifiées", type="primary", use_container_width=True):
            with st.spinner("Recherche de sources en cours..."):
                try:
                    response_fc = requests.post(
                        f"{API_URL}/fact_check",
                        json={"text_to_analyze": text_to_analyze, "row_index": st.session_state["row_index"]},
                        timeout=60,
                    )
                    response_fc.raise_for_status()
                    result_fc = response_fc.json()
                    lines = [line.lstrip() for line in result_fc["result"].split("\n")]
                    result_text = ""
                    first_claim = True
                    for line in lines:
                        if re.match(r'^\d+\.', line):
                            if not first_claim:
                                result_text += '\n\n<hr style="border:none;border-top:1px solid #555;width:40%;margin:20px 0;">\n\n'
                            first_claim = False
                        result_text += line + "\n\n"
                    st.markdown(result_text, unsafe_allow_html=True)
                    st.divider()
                    st.markdown("""
<div style="font-size: 0.85rem; color: #aaa; padding-top: 4px;">
<strong>Légende :</strong><br>
🔵 <strong>FACTUEL</strong> : claim vérifiable par des faits<br>
🟣 <strong>INTERPRÉTATIF</strong> : claim subjectif ou ambigu<br>
✅ <strong>CONFIRMÉ</strong> : les sources valident le claim<br>
❌ <strong>CONTREDIT</strong> : les sources réfutent le claim<br>
⚪ <strong>NON ÉTABLI</strong> : aucune source fiable ne permet de trancher<br>
⚠️ <strong>TROMPEUR</strong> : le claim est factuellement incomplet ou décontextualisé
</div>
""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Erreur fact-check : {e}")

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
