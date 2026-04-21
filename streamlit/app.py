import streamlit as st
import requests
import os
import random
from newspaper import Article


# params

if "url_count" not in st.session_state:
    st.session_state["url_count"] = 0

if "clear_count" not in st.session_state:
    st.session_state["clear_count"] = 0

images = ["streamlit/chuck_norris.jpg", "streamlit/donald_trump.png"]

predict_label = None
predict_score = None
predict_langue = None

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

API_READY = True #true quand c'est good

st.set_page_config(
    page_title="Fake News Detector",
    page_icon="📰",
    layout="centered"
)

# css pour real/fake
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
</style>
""", unsafe_allow_html=True)

# header
st.title("📰 Fake News Detector 📰")
st.caption("Détection et catégorisation de Fake News")
st.divider()

# saisie
tab_url, tab_text = st.tabs(["Analyser depuis une URL", "Analyser depuis du texte brut"])

url_input = ""
text_input = ""

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

with tab_text:
    text_input = st.text_area(
        "Collez ici le contenu de l'article",
        height=200,
        placeholder="Entrez le texte de l'article à analyser...",
        key=f"input_text_{st.session_state['clear_count']}",
    )

# bouton
st.divider()
col_btn, col_clear = st.columns([5, 1])
with col_btn:
    analyze = st.button("🔍 Lancer l'analyse", type="primary", use_container_width=True)
with col_clear:
    if st.button("🗑️ Effacer", use_container_width=True):
        st.session_state["clear_count"] += 1
        st.session_state["url_count"] += 1
        st.session_state["show_cleared"] = True
        st.rerun()

if st.session_state.get("show_cleared"):
    st.success("🗑️ Champs effacés")
    st.session_state["show_cleared"] = False

# analyse
if analyze:

    # cas 1 : url
    if url_input:
        with st.spinner("Extraction en cours..."):
            try:
                art = Article(url_input)
                art.download()
                art.parse()
                text_to_analyze = art.text
                st.success(f"Texte extrait ({len(text_to_analyze)} caractères)")

            except Exception as e:
                st.error(f"❌ Impossible d'extraire le texte : {e}")
                st.stop()

    # cas 2 : texte brut
    elif text_input:
        text_to_analyze = text_input

    # cas 3 : rien
    else:
        st.error("❌ Aucun texte à analyser. Collez du texte ou entrez une URL.")
        st.stop()

    # validation longueur
    if len(text_to_analyze.strip()) < 500:
        st.error("❌ Texte trop court. Veuillez saisir au moins 500 caractères.")
        st.stop()

    # prédiction
    with st.spinner("Analyse en cours..."):
        if API_READY:
            try:
                response = requests.post(
                    f"{API_URL}/predict",
                    json={"text": text_to_analyze},
                    timeout=10,
                )
                response.raise_for_status()
                result = response.json()
                predict_label  = result["Verdict"]
                predict_score  = result["Indice de confiance"]
                predict_langue = result["Langue"]
            except requests.exceptions.ConnectionError:
                st.error(f"❌ API non joignable sur {API_URL}")
                st.stop()
            except Exception as e:
                st.error(f"❌ Erreur API : {e}")
                st.stop()
        else:
            import time
            time.sleep(1)
            predict_label  = random.choice(["FAKE", "REAL"])
            predict_score  = round(random.uniform(0.65, 0.98), 4)
            predict_langue = "fr" if any(w in text_to_analyze.lower()
                                         for w in ["le", "la", "les", "est", "un", "une"]) else "en"

    # résultat
    st.divider()
    st.subheader("Résultat")

    if predict_label == "FAKE":
        st.markdown('<div class="verdict-fake">🚨 FAKE NEWS</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="verdict-real">✅ ARTICLE FIABLE</div>', unsafe_allow_html=True)

    st.markdown("")
    col1, col2, col3 = st.columns(3)
    col1.metric("Verdict",             predict_label)
    col2.metric("Indice de confiance", f"{predict_score:.1%}")
    col3.metric("Langue",              "🇫🇷 Français" if predict_langue == "fr" else "🇬🇧 Anglais")

    st.progress(predict_score, text=f"Indice de confiance : {predict_score:.1%}")



# feedback



#footer
st.divider()
st.caption("Martin Cornud - Alex Delrieu - Charles Jégo")
st.caption("Le Wagon - #2251")
