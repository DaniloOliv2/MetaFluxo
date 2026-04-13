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

# --- ESTILO CSS ULTRAPRO (LAYOUT DE CARTÃO FIXO) ---
st.markdown("""
    <style>
    /* Fundo degradê */
    .stApp { 
        background-color: #020617;
        background-image: radial-gradient(circle at top right, #1e3a8a, #020617);
    }
    
    /* Centralização Absoluta do Card */
    .main-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding-top: 50px;
    }

    .login-card {
        background-color: #1e293b;
        padding: 40px;
        border-radius: 24px;
        border: 1px solid #334155;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        width: 360px; /* Largura fixa para não esticar */
        margin: auto;
    }

    .brand-title {
        color: #60a5fa;
        font-weight: 800;
        font-size: 2rem;
        margin-bottom: 25px;
        text-align: center;
    }

    /* Inputs Slim */
    div[data-baseweb="input"] {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        min-height: 40px !important;
    }

    /* --- LINHA DE OPÇÕES (REMEMBER / FORGOT) --- */
    .options-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    
    /* Estilo dos Links Discretos */
    .stButton.discreto button {
        background: none !important;
        border: none !important;
        color: #94a3b8 !important;
        text-decoration: underline !important;
        font-size: 0.8rem !important;
        font-weight: 400 !important;
        padding: 0 !important;
        width: auto !important;
    }
    .stButton.discreto button:hover { color: #f1f5f9 !important; }

    /* --- BOTÃO LOGIN DESTACADO --- */
    .login-btn button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        height: 45px !important;
        width: 100% !important;
        border: none !important;
        margin-top: 15px;
    }

    .signup-section {
        margin-top: 25px;
        text-align: center;
        color: #94a3b8;
        font-size: 0.85rem;
    }

    .copyright { margin-top: 25px; font-size: 0.7rem; color: #475569; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_FILE = "metafluxo_db.json"
def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: pass
    return {"users": {"admin": {"password": "123", "security_answer": "Murillo"}}, "metas_sonhos": []}

def salvar_banco(dados):
    with open(DB_FILE, "w") as f: json.dump(dados, f, indent=4)

if 'db' not in st.session_state: st.session_state.db = carregar_banco()

# --- ESTADOS ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'
if 'error_msg' not in st.session_state: st.session_state['error_msg'] = False

# --- TELA DE LOGIN ---
if not st.session_state['logged_in']:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    if st.session_state['auth_mode'] == 'login':
        # Início do Card
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="brand-title">METAFLUX</div>', unsafe_allow_html=True)
        
        u = st.text_input("User", placeholder="Username", key="u_in", label_visibility="collapsed")
        p = st.text_input("Pass", type="password", placeholder="Password", key="p_in", label_visibility="collapsed")
        
        # Linha: Remember | Forgot password?
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.checkbox("Remember", key="rem_key")
        with col2:
            st.markdown('<div class="stButton discreto" style="text-align:right">', unsafe_allow_html=True)
            if st.button("Forgot password?", key="forgot_key"):
                st.session_state['auth_mode'] = 'recover'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Botão Login
        st.markdown('<div class="login-btn">', unsafe_allow_html=True)
        if st.button("Login", key="main_login"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u
                st.rerun()
            else:
                st.session_state['error_msg'] = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state['error_msg']:
            st.error("Invalid Login!")
            time.sleep(2); st.session_state['error_msg'] = False; st.rerun()

        # Rodapé: Not account? | Create an account
        st.markdown('<div class="signup-section">Not account?</div>', unsafe_allow_html=True)
        st.markdown('<div class="stButton discreto" style="text-align:center">', unsafe_allow_html=True)
        if st.button("Create an account", key="signup_key"):
            st.session_state['auth_mode'] = 'signup'; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="copyright">© 2026 MetaFlux Pro. All rights reserved.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True) # Fim do Card

    # Outros modos (Signup/Recover) seguem a mesma lógica de card
    elif st.session_state['auth_mode'] == 'signup':
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.subheader("New Account")
        nu = st.text_input("Username")
        np = st.text_input("Password", type="password")
        ns = st.text_input("Murillo?")
        if st.button("Create"):
            st.session_state.db["users"][nu] = {"password": np, "security_answer": ns}
            salvar_banco(st.session_state.db); st.session_state['auth_mode'] = 'login'; st.rerun()
        if st.button("Back"): st.session_state['auth_mode'] = 'login'; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # Fim do Container Principal

else:
    # --- APP LOGADO ---
    with st.sidebar:
        try: st.image("logo.png", use_column_width=True)
        except: st.title("📈 METAFLUX")
        if st.button("Sair"): st.session_state['logged_in'] = False; st.rerun()
    st.title(f"🚀 Dashboard {st.session_state.get('current_user')}")
