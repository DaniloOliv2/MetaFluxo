import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="MetaFluxo 📈", layout="wide", page_icon="📈")

# --- BANCO DE DADOS ---
DB_FILE = "metafluxo_db.json"

def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"users": {"admin": {"password": "123", "security_answer": "Murillo"}}}

def salvar_banco(dados):
    with open(DB_FILE, "w") as f:
        json.dump(dados, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = carregar_banco()

# --- LÓGICA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'login_error' not in st.session_state:
    st.session_state['login_error'] = False

if not st.session_state['logged_in']:
    st.title("📈 MetaFluxo")
    aba_login, aba_criar = st.tabs(["Acessar Login", "Criar Nova Conta"])
    
    with aba_login:
        user = st.text_input("Usuário", key="u_log")
        passw = st.text_input("Senha", type="password", key="p_log")
        if st.button("Entrar"):
            if user in st.session_state.db["users"] and st.session_state.db["users"][user]["password"] == passw:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = user
                st.rerun()
            else:
                st.session_state['login_error'] = True
                st.error("Usuário ou senha incorretos.")

        if st.session_state['login_error']:
            if st.button("Redefinir a senha"):
                st.session_state['show_reset'] = True
        
        if st.session_state.get('show_reset'):
            st.divider()
            u_res = st.text_input("Usuário para recuperar")
            resp = st.text_input("Pergunta: Qual o nome do seu filho?")
            nova_s = st.text_input("Nova Senha", type="password")
            if st.button("Salvar Nova Senha"):
                if u_res in st.session_state.db["users"] and resp.lower() == st.session_state.db["users"][u_res]["security_answer"].lower():
                    st.session_state.db["users"][u_res]["password"] = nova_s
                    salvar_banco(st.session_state.db)
                    st.success("Senha alterada! Tente logar.")
                    st.session_state['show_reset'] = False
                else:
                    st.error("Resposta incorreta.")

    with aba_criar:
        n_user = st.text_input("Novo Usuário")
        n_pass = st.text_input("Nova Senha", type="password")
        n_resp = st.text_input("Pergunta de Segurança: Nome do seu filho?")
        if st.button("Cadastrar"):
            if n_user and n_pass:
                if "users" not in st.session_state.db: st.session_state.db["users"] = {}
                st.session_state.db["users"][n_user] = {"password": n_pass, "security_answer": n_resp}
                salvar_banco(st.session_state.db)
                st.success("Conta criada!")
else:
    # --- PAINEL PRINCIPAL ---
    user_atual = st.session_state['current_user']
    
    with st.sidebar:
        st.title("📈 MetaFluxo")
        st.write(f"Usuário: **{user_atual}**")
        mes = st.selectbox("Escolha o Mês", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        renda = st.number_input("Sua Renda (R$)", value=3000.0)
        meta_inv = st.number_input("Meta de Investimento (R$)", value=1000.0)
        st.divider()
        if st.button("🚪 Sair"):
            st.session_state['logged_in'] = False
            st.rerun()

    if mes not in st.session_state.db:
        st.session_state.db[mes] = {"gastos": [], "investido": 0.0}
    dados_mes = st.session_state.db[mes]

    st.title(f"📈 Painel de {mes}")

    investido = st.number_input("Quanto guardou este mês?", min_value=0.0, value=float(dados_mes["investido"]), key=f"inv_{mes}")
    dados_mes["investido"] = investido

    st.subheader("🎯 Progresso da Meta")
    falta = max(0.0, meta_inv - investido)
    progresso = min(investido / meta_inv, 1.0) if meta_inv > 0 else 0.0
    st.progress(progresso)
    
    if falta > 0:
        st.markdown(f"<p style='color: #FFD700; font-size: 20px; font-weight: bold;'>⚡ {progresso*100:.1f}% atingido! (Faltam R$ {falta:,.2f})</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color: #2ecc71; font-size: 20px; font-weight: bold;'>🏆 META ATINGIDA!</p>", unsafe_allow_html=True)

    st.divider()

    # --- NOVA ESTRUTURA PARA EVITAR ROLAGEM INFINITA ---
    col_gastos, col_graficos = st.columns([1.5, 1])

    with col_gastos:
        st.subheader("📝 Seus Blocos de Gastos")
        if st.button("➕ Adicionar Bloco"):
            st.session_state.db[mes]["gastos"].append({"item": "Novo Gasto", "valor": 0.0, "pago": False})

        total_pago = 0.0
        total_a_pagar = 0.0

        # CRIANDO A JANELA DE ROLAGEM (Scroll)
        # O height=450 define a altura da caixa. Se passar disso, surge a barra de rolagem.
        scroll_container = st.container(height=450)
        
        with scroll_container:
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

    with col_graficos:
        st.subheader("📊 Resumo e Gráfico")
        saldo_livre = renda - total_pago - investido

        st.metric("✅ Total Pago", f"R$ {total_pago:,.2f}")
        st.metric("💰 Saldo Livre", f"R$ {saldo_livre:,.2f}")
        st.metric("⏳ Pendente", f"R$ {total_a_pagar:,.2f}")

        df_graf = pd.DataFrame({
            "Categoria": ["Pago", "Pendente", "Investido", "Livre"],
            "Valores": [total_pago, total_a_pagar, investido, max(0, saldo_livre)]
        })
        fig = px.pie(df_graf, values='Valores', names='Categoria', hole=0.5,
                     color_discrete_sequence=["#2ecc71", "#e74c3c", "#f1c40f", "#3498db"])
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    salvar_banco(st.session_state.db)
