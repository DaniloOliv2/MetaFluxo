import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd
from PIL import Image
import time

# --- CONFIGURAÇÃO VISUAL ---
try:
    img_favicon = Image.open("favicon.jpg")
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon=img_favicon)
except:
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon="📈")

# --- ESTILO CSS (FOCO NO BOTÃO DE LOGIN) ---
st.markdown("""
    <style>
    .stApp { 
        background-color: #020617;
        background-image: radial-gradient(circle at top right, #1e3a8a, #020617);
    }
    
    .login-card {
        background-color: #1e293b;
        padding: 40px;
        border-radius: 24px;
        border: 1px solid #334155;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        text-align: center;
        max-width: 380px;
        margin: auto;
    }

    div[data-baseweb="input"] {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        min-height: 40px !important;
    }
    
    input { color: #f1f5f9 !important; font-size: 0.95rem !important; }

    .left-align {
        text-align: left !important;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }

    /* Botão Esqueci a Senha - Discreto */
    .stButton.forgot-btn button {
        background-color: transparent !important;
        color: #64748b !important;
        border: none !important;
        font-size: 0.75rem !important;
        padding: 0px !important;
        margin-top: -10px !important;
        width: auto !important;
    }

    /* --- AJUSTE: BOTÃO LOGIN DE PONTA A PONTA, FINO E DISCRETO --- */
    .stButton.login-btn button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        height: 38px !important; /* Mais fino */
        width: 100% !important; /* De ponta a ponta */
        border: none !important;
        margin-top: 20px;
        font-size: 0.9rem !important;
    }
    .stButton.login-btn button:hover {
        background-color: #3b82f6 !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #020617 100%);
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        if st.session_state['auth_mode'] == 'login':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            u = st.text_input("Usuário", placeholder="Seu usuário", key="user_login", label_visibility="collapsed")
            p = st.text_input("Senha", type="password", placeholder="Sua senha", key="pass_login", label_visibility="collapsed")
            
            st.markdown('<div class="left-align">', unsafe_allow_html=True)
            st.checkbox("Remember", key="rem")
            st.markdown('<div class="stButton forgot-btn">', unsafe_allow_html=True)
            if st.button("Forgot password?", key="forgot"):
                st.session_state['auth_mode'] = 'recover'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Botão Login com a nova classe CSS
            st.markdown('<div class="stButton login-btn">', unsafe_allow_html=True)
            if st.button("ACESSAR PAINEL"):
                # Lógica de login mantida
                if u == "admin" and p == "123": # Exemplo simples para teste
                    st.session_state['logged_in'] = True; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

else:
    st.title("🚀 Dashboard")
    if st.button("Sair"): st.session_state['logged_in'] = False; st.rerun()
