import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="CraftCash 💎", layout="wide", page_icon="🧱")

# --- BANCO DE DADOS ---
DB_FILE = "craftcash_db.json"

def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def salvar_banco(dados):
    with open(DB_FILE, "w") as f:
        json.dump(dados, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = carregar_banco()

# --- SISTEMA DE LOGIN ---
if 'usuario' not in st.session_state:
    st.title("🧱 Bem-vindo ao CraftCash")
    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta"])
    
    with aba_login:
        user_login = st.text_input("Usuário")
        pass_login = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if user_login in st.session_state.db and st.session_state.db[user_login]['senha'] == pass_login:
                st.session_state.usuario = user_login
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

    with aba_cadastro:
        novo_user = st.text_input("Escolha um Nome de Usuário")
        nova_senha = st.text_input("Escolha uma Senha", type="password")
        if st.button("Cadastrar"):
            if novo_user in st.session_state.db:
                st.warning("Esse usuário já existe!")
            else:
                st.session_state.db[novo_user] = {"senha": nova_senha, "dados": {}}
                salvar_banco(st.session_state.db)
                st.success("Conta criada! Vá na aba Entrar.")
    st.stop()

# --- SE VOCÊ CHEGOU AQUI, ESTÁ LOGADO ---
user = st.session_state.usuario
if "dados" not in st.session_state.db[user]:
    st.session_state.db[user]["dados"] = {}

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"💎 CraftCash")
    st.write(f"Olá, **{user}**!")
    mes = st.selectbox("Escolha o Mês", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
    renda = st.number_input("Sua Renda (R$)", value=3000.0)
    meta_inv = st.number_input("Meta de Investimento (R$)", value=1000.0)
    if st.button("Sair"):
        del st.session_state.usuario
        st.rerun()

# Preparar dados do mês do usuário
if mes not in st.session_state.db[user]["dados"]:
    st.session_state.db[user]["dados"][mes] = {"gastos": [], "investido": 0.0}
dados_mes = st.session_state.db[user]["dados"][mes]

# --- CORPO DO APP (Gráficos e Gastos) ---
st.title(f"🧱 Painel de {mes}")

investido = st.number_input("Quanto guardou este mês?", min_value=0.0, value=float(dados_mes["investido"]), key=f"inv_{mes}")
dados_mes["investido"] = investido

falta = max(0.0, meta_inv - investido)
progresso = min(investido / meta_inv, 1.0) if meta_inv > 0 else 0.0
st.progress(progresso)
st.markdown(f"<p style='color: #FFD700; font-size: 20px; font-weight: bold;'>⚡ {progresso*100:.1f}% atingido! (Faltam R$ {falta:,.2f} para a meta)</p>", unsafe_allow_html=True)

st.divider()
def adicionar_gasto():
    st.session_state.db[user]["dados"][mes]["gastos"].append({"item": "Novo Gasto", "valor": 0.0, "pago": False})

st.button("➕ Adicionar Bloco", on_click=adicionar_gasto)

total_pago = 0.0
total_a_pagar = 0.0

for i, gasto in enumerate(dados_mes["gastos"]):
    c1, c2, c3, c4 = st.columns([3, 2, 1, 2])
    with c1:
        gasto["item"] = st.text_input(f"O que é?", gasto["item"], key=f"it_{mes}_{i}")
    with c2:
        gasto["valor"] = st.number_input(f"Valor (R$)", value=float(gasto["valor"]), key=f"vl_{mes}_{i}")
    with c3:
        gasto["pago"] = st.checkbox("✅", value=gasto["pago"], key=f"ck_{mes}_{i}")
    with c4:
        restante = 0.0 if gasto["pago"] else gasto["valor"]
        st.metric("A Pagar", f"R$ {restante:,.2f}")
        if gasto["pago"]: total_pago += gasto["valor"]
        else: total_a_pagar += gasto["valor"]

# --- GRÁFICO ---
st.divider()
col_res, col_graf = st.columns(2)
saldo_livre = renda - total_pago - investido

with col_res:
    st.metric("✅ Total Pago", f"R$ {total_pago:,.2f}")
    st.metric("💰 Saldo Livre", f"R$ {saldo_livre:,.2f}")

with col_graf:
    df_graf = pd.DataFrame({"Cat": ["Pago", "Pendente", "Investido", "Livre"], "Val": [total_pago, total_a_pagar, investido, max(0, saldo_livre)]})
    fig = px.pie(df_graf, values='Val', names='Cat', hole=0.5, color_discrete_sequence=["#2ecc71", "#e74c3c", "#f1c40f", "#3498db"])
    st.plotly_chart(fig, use_container_width=True)

salvar_banco(st.session_state.db)