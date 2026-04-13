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
        padding: 40px; border-radius: 24px; border: 1px solid #334155;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6); text-align: center;
        max-width: 380px; margin: auto;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #020617 100%);
    }
    .status-card {
        background: rgba(30, 41, 59, 0.7);
        padding: 20px; border-radius: 15px; border: 1px solid #334155;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b; border-radius: 10px 10px 0 0;
        color: white; padding: 10px 20px;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #3b82f6 , #10b981);
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTES E BANCO DE DADOS ---
DB_FILE = "metafluxo_db_v2.json"
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
                # Garantir chaves básicas
                if "users" not in data: data["users"] = {"admin": {"password": "123", "security_answer": "Murillo"}}
                if "recorrentes" not in data: data["recorrentes"] = []
                if "metas_sonhos" not in data: data["metas_sonhos"] = []
                return data
            except: pass
    return {
        "users": {"admin": {"password": "123", "security_answer": "Murillo"}},
        "recorrentes": [],
        "metas_sonhos": [],
        "config": {"taxa_juros": 0.08, "reserva_meses": 6}
    }

def salvar_banco(dados):
    with open(DB_FILE, "w") as f:
        json.dump(dados, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = carregar_banco()

# --- ESTADOS DE SESSÃO ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

# --- TELA DE ACESSO ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        st.write("")
        if st.session_state['auth_mode'] == 'login':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown("<h1 style='color: #60a5fa; font-weight: 800;'>METAFLUX</h1>", unsafe_allow_html=True)
            u = st.text_input("Usuário", key="user_login")
            p = st.text_input("Senha", type="password", key="pass_login")
            if st.button("ACESSAR PAINEL"):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else: st.error("Dados incorretos")
            if st.button("Criar Conta"): st.session_state['auth_mode'] = 'signup'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state['auth_mode'] == 'signup':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Novo Cadastro")
            nu = st.text_input("Usuário")
            np = st.text_input("Senha", type="password")
            ns = st.text_input("Pergunta de Segurança (Nome do Filho?)")
            if st.button("CADASTRAR"):
                if nu and np and ns:
                    st.session_state.db["users"][nu] = {"password": np, "security_answer": ns}
                    salvar_banco(st.session_state.db)
                    st.success("Conta criada!"); time.sleep(1); st.session_state['auth_mode'] = 'login'; st.rerun()
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- INTERFACE PRINCIPAL ---
    with st.sidebar:
        st.title("📈 METAFLUX PRO")
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        
        with st.expander("⚙️ Gastos Recorrentes (Fixos)"):
            item_rec = st.text_input("Nome (ex: Netflix)")
            valor_rec = st.number_input("Valor R$", min_value=0.0)
            dia_rec = st.number_input("Dia Vencimento", 1, 31, 10)
            if st.button("Salvar Recorrente"):
                st.session_state.db["recorrentes"].append({"item": item_rec, "valor": valor_rec, "vencimento": dia_rec})
                salvar_banco(st.session_state.db); st.rerun()
            
            for i, r in enumerate(st.session_state.db["recorrentes"]):
                st.caption(f"{r['item']} (Dia {r['vencimento']})")
                if st.button(f"Remover {i}", key=f"rem_rec_{i}"):
                    st.session_state.db["recorrentes"].pop(i)
                    salvar_banco(st.session_state.db); st.rerun()

        st.divider()
        renda_fixa = st.number_input("Renda Mensal (R$)", value=3000.0)
        mes_ref = st.selectbox("Mês de Referência", MESES, index=3)
        if st.button("🚪 Sair"): st.session_state['logged_in'] = False; st.rerun()

    # Inicialização do Mês
    if mes_ref not in st.session_state.db:
        # Puxa recorrentes automaticamente ao criar o mês
        st.session_state.db[mes_ref] = {
            "gastos": [g.copy() for g in
