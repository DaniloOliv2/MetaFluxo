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

    /* Alinhamento dos elementos à esquerda dentro do card */
    .left-align {
        text-align: left !important;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }

    /* Botão Esqueci a Senha - Menor e no Canto Esquerdo */
    .stButton.forgot-btn button {
        background-color: transparent !important;
        color: #64748b !important;
        border: none !important;
        font-size: 0.75rem !important; /* Tamanho menor que o padrão */
        font-weight: 400 !important;
        padding: 0px !important;
        margin-top: -10px !important; /* Aproxima do checkbox */
        width: auto !important;
        text-decoration: none !important;
    }
    
    .stButton.forgot-btn button:hover {
        color: #60a5fa !important;
        background-color: transparent !important;
        text-decoration: underline !important;
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

    .copyright { margin-top: 20px; font-size: 0.7rem; color: #475569; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE BANCO DE DADOS ---
DB_FILE = "metafluxo_db.json"
def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: pass
    return {"users": {"admin": {"password": "123", "security_answer": "Murillo"}}, "metas_sonhos": []}

if 'db' not in st.session_state:
    st.session_state.db = carregar_banco()

# --- ESTADOS DE SESSÃO ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

# --- TELA DE LOGIN ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        if st.session_state['auth_mode'] == 'login':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            
            # Inputs de texto
            u = st.text_input("Usuário", placeholder="Seu usuário", key="user_login", label_visibility="collapsed")
            p = st.text_input("Senha", type="password", placeholder="Sua senha", key="pass_login", label_visibility="collapsed")
            
            # Container para alinhar Checkbox e Botão de recuperar à esquerda
            st.markdown('<div class="left-align">', unsafe_allow_html=True)
            st.checkbox("Remember", key="rem")
            
            st.markdown('<div class="stButton forgot-btn">', unsafe_allow_html=True)
            if st.button("Forgot password?", key="forgot"):
                st.session_state['auth_mode'] = 'recover'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Botão de Acesso
            st.markdown('<div class="stButton login-btn">', unsafe_allow_html=True)
            if st.button("ACESSAR PAINEL"):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Dados incorretos!")
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("Não tem conta? Cadastre-se"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

            st.markdown('<div class="copyright">© 2026 MetaFlux. Direitos reservados.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'recover':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Recuperação")
            if st.button("Voltar"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.write("Você está logado!")
