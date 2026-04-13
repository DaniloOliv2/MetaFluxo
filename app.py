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

# --- ESTILO CSS AVANÇADO ---
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

    /* Inputs Slim */
    div[data-baseweb="input"] {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        min-height: 40px !important;
    }
    
    input { color: #f1f5f9 !important; font-size: 0.95rem !important; }

    /* Estilo para o botão discreto de 'Forgot password' */
    .stButton.forgot-btn button {
        background-color: transparent !important;
        color: #94a3b8 !important;
        border: 1px solid transparent !important;
        font-size: 0.85rem !important;
        font-weight: 400 !important;
        padding: 0px 5px !important;
        width: auto !important;
        text-decoration: underline !important;
    }
    
    .stButton.forgot-btn button:hover, .stButton.forgot-btn button:active {
        color: #60a5fa !important;
        background-color: rgba(96, 165, 250, 0.1) !important;
        border: 1px solid rgba(96, 165, 250, 0.2) !important;
        text-decoration: none !important;
    }

    /* Botão Principal Login */
    .stButton.login-btn button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        height: 45px !important;
        width: 100% !important;
        border: none !important;
        margin-top: 20px;
    }
    
    .stButton.login-btn button:hover {
        background-color: #3b82f6 !important;
    }

    .copyright { margin-top: 20px; font-size: 0.7rem; color: #475569; }
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
    with open(DB_FILE, "w") as f:
        json.dump(dados, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = carregar_banco()

# --- ESTADOS DE SESSÃO ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'
if 'error_msg' not in st.session_state: st.session_state['error_msg'] = False

# --- TELA DE LOGIN ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        st.write("")
        if st.session_state['auth_mode'] == 'login':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            
            # Inputs
            u = st.text_input("Usuário", placeholder="Seu usuário", key="user_login", label_visibility="collapsed")
            p = st.text_input("Senha", type="password", placeholder="Sua senha", key="pass_login", label_visibility="collapsed")
            
            # --- LINHA DE OPÇÕES: REMEMBER (ESQ) | FORGOT PASSWORD (DIR) ---
            c1, c2 = st.columns([1, 1.2])
            with c1:
                st.checkbox("Remember", key="rem")
            with c2:
                # Alinhado à direita e com estilo discreto
                st.markdown('<div class="stButton forgot-btn" style="text-align:right">', unsafe_allow_html=True)
                if st.button("Forgot password?", key="forgot"):
                    st.session_state['auth_mode'] = 'recover'; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            # ------------------------------------------------------

            st.markdown('<div class="stButton login-btn">', unsafe_allow_html=True)
            if st.button("ACESSAR PAINEL"):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else:
                    st.session_state['error_msg'] = True; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.session_state['error_msg']:
                st.error("Dados incorretos!")
                time.sleep(3); st.session_state['error_msg'] = False; st.rerun()

            if st.button("Não tem conta? Cadastre-se"):
                st.session_state['auth_mode'] = 'signup'; st.rerun()

            st.markdown('<div class="copyright">© 2026 MetaFlux. Direitos reservados.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'signup':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Nova Conta")
            # ... campos de cadastro ...
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'recover':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Recuperação")
            # ... campos de recuperação ...
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- APP LOGADO ---
    with st.sidebar:
        if st.button("Sair"): st.session_state['logged_in'] = False; st.rerun()
    st.title("🚀 Dashboard")
