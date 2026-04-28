import streamlit as st
import os
import json
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Admin", page_icon="🔒", layout="wide")

# Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
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

# auth
if "admin_unlocked" not in st.session_state:
    st.session_state["admin_unlocked"] = False

col_title, col_logout = st.columns([8, 1])
with col_title:
    st.title("🔒 Admin")
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state["admin_unlocked"]:
        if st.button("🔒 Déconnexion", type="secondary", use_container_width=True):
            st.session_state["admin_unlocked"] = False
            st.rerun()

if not st.session_state["admin_unlocked"]:
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if pwd == os.getenv("ADMIN_PASSWORD", "admin"):
            st.session_state["admin_unlocked"] = True
            st.rerun()
        else:
            st.error("❌ Mot de passe incorrect")
    st.stop()

if sheet is None:
    st.warning("⚠️ Google Sheets non configuré.")
    st.stop()

# ── DONNÉES ─────────────────────────────────────────────────
all_rows = sheet.get_all_records()
df = pd.DataFrame(all_rows)

history = sheet2.get_all_records() if sheet2 else []
df_history = pd.DataFrame(history)

# ── LIGNE 1 : SUBHEADERS ────────────────────────────────────
col_left, col_right = st.columns(2)
with col_left:
    st.subheader("📋 Historique des analyses")
with col_right:
    st.subheader("📊 Petit jeu d'Alex le platiste")

# ── LIGNE 2 : KPIs + KPIs + PIE | KPIs + VALIDATION ─────────
col_kpi_h1, col_kpi_h2, col_pie_h, col_kpi_n, col_action_n = st.columns([1, 1, 1, 1, 2])

with col_kpi_h1:
    if not df_history.empty:
        total = len(df_history)
        pct_fake = len(df_history[df_history["verdict"] == "FAKE"]) / total * 100
        non_concluant = len(df_history[df_history["verdict"] == "NON CONCLUANT"])
        conf_moyenne = df_history["confiance"].mean() * 100
        st.metric("Total analyses", total)
        st.metric("Non concluant", non_concluant)
        st.metric("% FAKE", f"{pct_fake:.1f}%")
        st.metric("Confiance moyenne", f"{conf_moyenne:.1f}%")
    else:
        st.info("Aucune analyse.")

with col_kpi_h2:
    if not df_history.empty:
        total_feedbacks = df_history["feedback"].replace("", pd.NA).dropna().shape[0]
        sans_feedbacks = df_history["feedback"].replace("", pd.NA).isna().sum()
        pct_positifs = (len(df_history[df_history["feedback"] == "good"]) / total_feedbacks * 100) if total_feedbacks > 0 else 0
        fact_checks = df_history["fact_check"].apply(lambda x: str(x).upper() == "TRUE").sum()
        st.metric("Total feedbacks", total_feedbacks)
        st.metric("Sans feedback", sans_feedbacks)
        st.metric("% positifs", f"{pct_positifs:.1f}%")
        st.metric("Fact checks", fact_checks)

with col_pie_h:
    if not df_history.empty:
        source_counts = df_history["source"].value_counts().reset_index()
        source_counts.columns = ["source", "count"]
        fig = px.pie(source_counts, values="count", names="source", title="Répartition par source")
        fig.update_traces(textfont_size=16, textinfo="percent")
        fig.update_layout(
            height=320,
            legend=dict(font=dict(size=13), orientation="h", y=-0.15, x=0.5, xanchor="center"),
            margin=dict(t=40, b=40, l=20, r=20),
            title=dict(x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)

with col_kpi_n:
    if not df.empty:
        st.metric("Total", len(df))
        st.metric("Fake", len(df[df["label"] == "fake"]))
        st.metric("Real", len(df[df["label"] == "real"]))
        st.metric("En attente", len(df[df["status"] == "pending"]))

with col_action_n:
    if not df.empty:
        st.markdown("""
        <div style="border:1px solid rgba(33,195,84,0.4); border-radius:8px; padding:16px; text-align:center; margin-bottom:12px;">
            <p style="color:#21c354; font-weight:bold; font-size:1.2rem; margin:0;">✅ Valider une news</p>
        </div>
        """, unsafe_allow_html=True)
        pending_titles = [row["title"] for row in all_rows if row["status"] == "pending"]
        if pending_titles:
            selected_validate = st.selectbox("", pending_titles, key="select_validate", label_visibility="collapsed")
            if st.button("✅ Valider", use_container_width=True, key="valider_news"):
                for i, row in enumerate(all_rows, start=2):
                    if row["title"] == selected_validate:
                        sheet.update_cell(i, 4, "valide")
                        break
                st.success("News validée ✅")
                st.rerun()
        else:
            st.info("Aucune news en attente")

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="border:1px solid rgba(255,75,75,0.4); border-radius:8px; padding:16px; text-align:center; margin-bottom:12px;">
            <p style="color:#ff4b4b; font-weight:bold; font-size:1.2rem; margin:0;">🗑️ Supprimer une news</p>
        </div>
        """, unsafe_allow_html=True)
        all_titles = [row["title"] for row in all_rows]
        selected_delete = st.selectbox("", all_titles, key="select_delete", label_visibility="collapsed")
        if st.button("🗑️ Supprimer", use_container_width=True, key="supprimer_news"):
            for i, row in enumerate(all_rows, start=2):
                if row["title"] == selected_delete:
                    sheet.delete_rows(i)
                    break
            st.success("News supprimée ✅")
            st.rerun()

# ── SÉPARATEUR ───────────────────────────────────────────────
st.divider()

# ── LIGNE 3 : FILTRES + TABLEAUX ────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Historique")
    col_fh1, col_fh2, col_fh3, col_fh4 = st.columns(4)
    with col_fh1:
        filter_verdict = st.selectbox("Verdict", ["Tous", "FAKE", "REAL", "NON CONCLUANT"], key="filter_verdict")
    with col_fh2:
        sources = ["Tous"] + sorted(df_history["source"].dropna().unique().tolist()) if not df_history.empty else ["Tous"]
        filter_source = st.selectbox("Source", sources, key="filter_source")
    with col_fh3:
        filter_feedback = st.selectbox("Feedback", ["Tous", "good", "bad", "Sans feedback"], key="filter_feedback")
    with col_fh4:
        filter_factcheck = st.selectbox("Fact check", ["Tous", "True", "False"], key="filter_factcheck")

    filtered_history = df_history.copy()
    if filter_verdict != "Tous":
        filtered_history = filtered_history[filtered_history["verdict"] == filter_verdict]
    if filter_source != "Tous":
        filtered_history = filtered_history[filtered_history["source"] == filter_source]
    if filter_feedback == "Sans feedback":
        filtered_history = filtered_history[filtered_history["feedback"].replace("", pd.NA).isna()]
    elif filter_feedback != "Tous":
        filtered_history = filtered_history[filtered_history["feedback"] == filter_feedback]
    if filter_factcheck != "Tous":
        filtered_history = filtered_history[
            filtered_history["fact_check"].apply(lambda x: str(x).upper() == "TRUE") == (filter_factcheck == "True")
        ]

    col_width = 150
    column_config = {col: st.column_config.Column(width=col_width) for col in filtered_history.columns}
    st.dataframe(filtered_history, use_container_width=True, height=300, column_config=column_config)

with col_right:
    st.subheader("News")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_label = st.selectbox("Label", ["Tous", "fake", "real"])
    with col_f2:
        filter_status = st.selectbox("Statut", ["Tous", "pending", "valide"])

    filtered = df.copy()
    if filter_label != "Tous":
        filtered = filtered[filtered["label"] == filter_label]
    if filter_status != "Tous":
        filtered = filtered[filtered["status"] == filter_status]

    st.dataframe(filtered, use_container_width=True, height=300)
