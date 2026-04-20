import streamlit as st
import requests
import os
import random


# params

if "url_count" not in st.session_state:
    st.session_state["url_count"] = 0

if "clear_count" not in st.session_state:
    st.session_state["clear_count"] = 0

images = ["streamlit/chuck_norris.jpg", "streamlit/donald_trump.png"]

predict_label = None
predict_score = None
predict_langue = None

# API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

API_READY = False #true quand c'est good

st.set_page_config(
    page_title="Fake News Detector",
    page_icon="📰",
    layout="centered"
)

# css pour real/fake
    # a voir a la fin

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
                from newspaper import Article
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
    col_img, col_metrics = st.columns([1, 2])
    with col_img:
        st.image(random.choice(images), use_container_width=True)
    with col_metrics:
        st.metric("Verdict :", random.choice(["FAKE NEWS", "REAL NEWS"]))
        st.metric("Indice de confiance :", f"{round(random.uniform(0.65, 0.98), 2):.0%}")
        st.metric("Langue :", random.choice(["Français", "Anglais"]))


# feedback



#footer
st.divider()
st.caption("Martin Cornud - Alex Delrieu - Charles Jégo")
st.caption("Le Wagon - #2251")