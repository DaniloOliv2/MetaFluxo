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

# --- ESTILO CSS ULTRAPRO (LOGIN DE MERCADO) ---
st.markdown("""
    <style>
    .stApp { 
        background-color: #020617;
        background-image: radial-gradient(circle at top right, #1e3a8a, #020617);
    }
    
    /* Cartão de Login */
    .login-card {
        background-color: #1e293b;
        padding: 40px;
        border-radius: 24px;
        border: 1px solid #334155;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        max-width: 380px;
        margin: auto;
    }

    /* Título MetaFlux */
    .brand-title {
        color: #60a5fa;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 30px;
        text-align: center;
    }

    /* Inputs Slim */
    div[data-baseweb="input"] {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        min-height: 40px !important;
    }
    input { color: #f1f5f9 !important; }

    /* --- O ÚNICO BOTÃO DESTACADO: LOGIN --- */
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        height: 48px !important;
        width: 100% !important;
        border: none !important;
        margin-top: 20px;
    }
    .stButton>button:hover { background-color: #3b82f6 !important; }

    /* --- ESTILO PARA LINKS DISCRETOS (FORGOT E CREATE) --- */
    .link-wrapper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: -15px; /* Ajuste para subir os links */
    }
    
    /* Remove o visual de botão dos links secundários */
    .stButton.discreto button {
        background: none !important;
        border: none !important;
        color: #94a3b8 !important;
        text-decoration: underline !important;
        font-size: 0.85rem !important;
        font-weight: 400 !important;
        padding: 0 !important;
        width: auto !important;
        box-shadow: none !important;
    }
    .stButton.discreto button:hover {
        color: #f1f5f9 !important;
    }

    .signup-text {
        margin-top: 30px;
        color: #94a3b8;
        font-size: 0.9rem;
        text-align: center;
    }

    .copyright { margin-top: 20px; font-size: 0.7rem; color: #475569; text-align: center; }
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
    _, center_col, _ = st.columns([1, 1.6, 1])
    with center_col:
        st.write("")
        if st.session_state['auth_mode'] == 'login':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown('<div class="brand-title">METAFLUX</div>', unsafe_allow_html=True)
            
            u = st.text_input("Usuário", placeholder="Seu usuário", key="user_login", label_visibility="collapsed")
            st.write("") # Espaçador slim
            p = st.text_input("Senha", type="password", placeholder="Sua senha", key="pass_login", label_visibility="collapsed")
            
            # Linha de Opções: Remember e Forgot password?
            col_l1, col_l2 = st.columns([1, 1])
            with col_l1:
                st.checkbox("Remember", key="rem_ch")
            with col_l2:
                # Botão Discreto
                st.markdown('<div class="stButton discreto" style="text-align:right">', unsafe_allow_html=True)
                if st.button("Forgot password?", key="btn_forgot"):
                    st.session_state['auth_mode'] = 'recover'; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # Botão Login Destacado
            if st.button("Login"):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else:
                    st.session_state['error_msg'] = True; st.rerun()
            
            if st.session_state['error_msg']:
                st.error("Invalid credentials!")
                time.sleep(3); st.session_state['error_msg'] = False; st.rerun()

            # Seção Not account?
            st.markdown('<div class="signup-text">Not account?</div>', unsafe_allow_html=True)
            st.markdown('<div class="stButton discreto" style="text-align:center">', unsafe_allow_html=True)
            if st.button("Create an account", key="btn_create"):
                st.session_state['auth_mode'] = 'signup'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="copyright">© 2026 MetaFlux Pro. All rights reserved.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'signup':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("New Account")
            new_u = st.text_input("Username")
            new_p = st.text_input("Password", type="password")
            new_s = st.text_input("Security answer")
            if st.button("CREATE"):
                if new_u and new_p and new_s:
                    st.session_state.db["users"][new_u] = {"password": new_p, "security_answer": new_s}
                    salvar_banco(st.session_state.db); st.success("Account created!"); time.sleep(2)
                    st.session_state['auth_mode'] = 'login'; st.rerun()
            if st.button("Back"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'recover':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Recovery")
            rec_u = st.text_input("Username")
            if rec_u in st.session_state.db["users"]:
                ans = st.text_input("Security answer")
                if st.button("SHOW PASSWORD"):
                    if ans.lower() == st.session_state.db["users"][rec_u]["security_answer"].lower():
                        st.info(f"Password: {st.session_state.db['users'][rec_u]['password']}")
            if st.button("Back"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- INTERFACE LOGADA ---
    with st.sidebar:
        try: st.image("logo.png", use_column_width=True)
        except: st.title("📈 METAFLUX")
        st.divider()
        privacidade = st.toggle("Modo Privacidade")
        st.divider()
        mes = st.selectbox("Mês", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        if st.button("🚪 Sair"): st.session_state['logged_in'] = False; st.rerun()

    st.title(f"🚀 Dashboard {mes}")
    # ... Restante do código do Dashboard e Meus Sonhos continua aqui igual ao anterior ...
