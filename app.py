import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MetaFluxo - Controle Financeiro", page_icon="📈")

# --- BANCO DE DADOS SIMULADO (Sessão) ---
if 'user_db' not in st.session_state:
    # Usuário: admin | senha: 123 | Resposta: Murillo
    st.session_state['user_db'] = {"admin": {"password": "123", "security_answer": "Murillo"}}

# --- FUNÇÕES ---
def login_user(username, password):
    if username in st.session_state['user_db'] and st.session_state['user_db'][username]['password'] == password:
        return True
    return False

def reset_password(username, answer, new_password):
    if username in st.session_state['user_db']:
        if st.session_state['user_db'][username]['security_answer'].lower() == answer.lower():
            st.session_state['user_db'][username]['password'] = new_password
            return True
    return False

# --- LOGIN E REDEFINIÇÃO ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("📈 MetaFluxo")
    tab1, tab2 = st.tabs(["Login", "Esqueci a Senha"])
    
    with tab1:
        user = st.text_input("Usuário")
        passw = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if login_user(user, passw):
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
                
    with tab2:
        st.write("Redefina sua senha respondendo à pergunta de segurança.")
        user_reset = st.text_input("Seu usuário para recuperar")
        answer = st.text_input("Pergunta: Qual o nome do seu filho?")
        new_pass = st.text_input("Nova Senha", type="password")
        if st.button("Confirmar Nova Senha"):
            if reset_password(user_reset, answer, new_pass):
                st.success("Senha alterada com sucesso! Volte para a aba Login.")
            else:
                st.error("Usuário ou resposta incorretos.")

# --- PAINEL PRINCIPAL ---
else:
    st.title("📈 MetaFluxo - Painel")
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.write("### Olá! O seu app está pronto para as próximas funções.")
