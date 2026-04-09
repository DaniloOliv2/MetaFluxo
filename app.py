import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MetaFluxo - Controle Financeiro", page_icon="📈")

# --- BANCO DE DADOS EM MEMÓRIA ---
if 'user_db' not in st.session_state:
    st.session_state['user_db'] = {"admin": {"password": "123", "security_answer": "Murillo"}}
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'login_error' not in st.session_state:
    st.session_state['login_error'] = False

# --- INTERFACE DE ACESSO (LOGIN / CRIAR CONTA) ---
if not st.session_state['logged_in']:
    st.title("📈 MetaFluxo")
    
    aba_login, aba_criar = st.tabs(["Acessar Login", "Criar Nova Conta"])
    
    with aba_login:
        user = st.text_input("Usuário", key="user_login")
        passw = st.text_input("Senha", type="password", key="pass_login")
        
        if st.button("Entrar"):
            if user in st.session_state['user_db'] and st.session_state['user_db'][user]['password'] == passw:
                st.session_state['logged_in'] = True
                st.session_state['login_error'] = False
                st.rerun()
            else:
                st.session_state['login_error'] = True
                st.error("Usuário ou senha incorretos.")

        # SÓ APARECE SE ERRAR O LOGIN
        if st.session_state['login_error']:
            st.warning("Esqueceu seus dados?")
            if st.button("Redefinir a senha"):
                st.session_state['show_reset'] = True

        # ÁREA DE REDEFINIÇÃO (ABRE EMBAIXO SE CLICAR)
        if st.session_state.get('show_reset'):
            st.divider()
            st.subheader("Recuperação de Acesso")
            user_res = st.text_input("Usuário para recuperar")
            resp = st.text_input("Pergunta: Qual o nome do seu filho?")
            nova_s = st.text_input("Nova Senha desejada", type="password")
            if st.button("Salvar Nova Senha"):
                if user_res in st.session_state['user_db'] and resp.lower() == st.session_state['user_db'][user_res]['security_answer'].lower():
                    st.session_state['user_db'][user_res]['password'] = nova_s
                    st.success("Senha alterada! Tente logar novamente.")
                    st.session_state['show_reset'] = False
                else:
                    st.error("Resposta ou usuário incorretos.")

    with aba_criar:
        novo_user = st.text_input("Escolha um Usuário")
        nova_senha = st.text_input("Escolha uma Senha", type="password")
        pergunta = st.text_input("Pergunta de Segurança: Nome do seu filho?")
        if st.button("Cadastrar Conta"):
            if novo_user and nova_senha:
                st.session_state['user_db'][novo_user] = {"password": nova_senha, "security_answer": pergunta}
                st.success("Conta criada com sucesso! Vá para a aba Login.")
            else:
                st.error("Preencha todos os campos.")

# --- PAINEL DO APLICATIVO (APÓS LOGIN) ---
else:
    st.title("📈 MetaFluxo - Dashboard")
    st.sidebar.header(f"Bem-vindo!")
    
    # Menu lateral para navegação
    menu = st.sidebar.selectbox("Menu", ["Resumo Geral", "Lançar Gastos/Ganhos", "Configurações"])
    
    if menu == "Resumo Geral":
        st.subheader("Seu Saldo Atual")
        col1, col2, col3 = st.columns(3)
        col1.metric("Entradas", "R$ 0,00")
        col2.metric("Saídas", "R$ 0,00", delta_color="inverse")
        col3.metric("Saldo", "R$ 0,00")
        st.info("Aqui aparecerão seus gráficos em breve!")

    elif menu == "Lançar Gastos/Ganhos":
        st.subheader("Novo Lançamento")
        tipo = st.radio("Tipo", ["Entrada", "Saída"])
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        desc = st.text_input("Descrição (Ex: Aluguel, Salário)")
        if st.button("Salvar Lançamento"):
            st.success(f"{tipo} de R$ {valor} salva com sucesso!")

    st.sidebar.divider()
    if st.sidebar.button("Sair do App"):
        st.session_state['logged_in'] = False
        st.rerun()
