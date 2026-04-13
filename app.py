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

# --- ESTILO CSS (FOCO NO BOTÃO DE LOGIN SLIM) ---
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

    /* BOTÃO LOGIN: DE PONTA A PONTA E FINO */
    .stButton.login-btn button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        height: 38px !important; 
        width: 100% !important; 
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

# --- BANCO DE DADOS (CONEXÃO RESTAURADA) ---
DB_FILE = "metafluxo_db.json"
def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: pass
    return {
        "users": {"admin": {"password": "123", "security_answer": "Murillo"}}, 
        "metas_sonhos": [], 
        "config": {"categorias": {"🏠 Moradia": "#3498db", "🍎 Alimentação": "#e67e22", "🚗 Transporte": "#9b59b6", "🎡 Lazer": "#f1c40f", "💊 Saúde": "#e74c3c", "🛠️ Outros": "#95a5a6"}}
    }

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
            u = st.text_input("Usuário", placeholder="Seu usuário", key="user_login", label_visibility="collapsed")
            p = st.text_input("Senha", type="password", placeholder="Sua senha", key="pass_login", label_visibility="collapsed")
            
            st.markdown('<div class="left-align">', unsafe_allow_html=True)
            st.checkbox("Remember", key="rem")
            st.markdown('<div class="stButton forgot-btn">', unsafe_allow_html=True)
            if st.button("Forgot password?", key="forgot"):
                st.session_state['auth_mode'] = 'recover'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="stButton login-btn">', unsafe_allow_html=True)
            if st.button("Login", key="main_login_btn"):
                # Verificação correta no seu banco de dados
                if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else:
                    st.session_state['error_msg'] = True; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.session_state['error_msg']:
                st.error("Dados incorretos!")
                time.sleep(2); st.session_state['error_msg'] = False; st.rerun()

            if st.button("Não tem conta? Cadastre-se"):
                st.session_state['auth_mode'] = 'signup'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'signup':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Nova Conta")
            new_u = st.text_input("Usuário")
            new_p = st.text_input("Senha", type="password")
            new_s = st.text_input("Nome do filho? (Segurança)")
            if st.button("CADASTRAR"):
                if new_u and new_p and new_s:
                    st.session_state.db["users"][new_u] = {"password": new_p, "security_answer": new_s}
                    salvar_banco(st.session_state.db); st.success("Criado!"); time.sleep(2)
                    st.session_state['auth_mode'] = 'login'; st.rerun()
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'recover':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Recuperação")
            rec_u = st.text_input("Seu usuário")
            if rec_u in st.session_state.db["users"]:
                ans = st.text_input("Resposta de segurança")
                if st.button("VER SENHA"):
                    if ans.lower() == st.session_state.db["users"][rec_u]["security_answer"].lower():
                        st.info(f"Sua senha: {st.session_state.db['users'][rec_u]['password']}")
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- DASHBOARD (RESTAURADO) ---
    with st.sidebar:
        try: st.image("logo.png", use_column_width=True)
        except: st.title("📈 METAFLUX")
        st.divider()
        if st.button("🚪 Sair"):
            st.session_state['logged_in'] = False; st.rerun()

    st.title(f"🚀 Dashboard")
    st.write("Bem-vindo de volta!")
