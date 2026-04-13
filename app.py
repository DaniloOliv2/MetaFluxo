
import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd
from PIL import Image
import time

# ---------------------------------------------------
# CONFIGURAÇÃO VISUAL
# ---------------------------------------------------
try:
    img_favicon = Image.open("favicon.jpg")
    st.set_page_config(
        page_title="MetaFlux Pro 📈",
        layout="wide",
        page_icon=img_favicon
    )
except:
    st.set_page_config(
        page_title="MetaFlux Pro 📈",
        layout="wide",
        page_icon="📈"
    )

# ---------------------------------------------------
# CSS VISUAL
# ---------------------------------------------------
st.markdown("""
<style>

/* FUNDO */
.stApp{
    background-color:#020617;
    background-image: radial-gradient(circle at top right, #1e3a8a, #020617);
}

/* REMOVE TOPO BRANCO / ESPAÇOS */
.block-container{
    padding-top:2rem;
}

/* CARD LOGIN */
.login-card{
    max-width:460px;
    margin:auto;
    padding:25px 15px;
}

/* INPUTS */
div[data-baseweb="input"]{
    background:#0f172a !important;
    border:1px solid #334155 !important;
    border-radius:10px !important;
    min-height:48px !important;
}

/* TEXTO INPUT */
input{
    color:#f8fafc !important;
}

/* LABELS */
label{
    color:white !important;
    font-weight:600 !important;
}

/* BOTÕES */
.stButton > button{
    width:100%;
    height:48px;
    border:none;
    border-radius:10px;
    background:#2563eb;
    color:white;
    font-weight:700;
    font-size:16px;
}

/* BOTÃO SECUNDÁRIO */
.secundario button{
    background:transparent !important;
    border:1px solid #60a5fa !important;
    color:#60a5fa !important;
}

/* SIDEBAR */
[data-testid="stSidebar"]{
    background: linear-gradient(180deg,#1e3a8a 0%, #020617 100%);
}

/* BARRA PROGRESSO */
.stProgress > div > div > div > div{
    background-image: linear-gradient(to right,#3b82f6,#10b981);
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# BANCO
# ---------------------------------------------------
DB_FILE = "metafluxo_db.json"

def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                pass

    return {
        "users": {
            "admin": {
                "password": "123",
                "security_answer": "Murillo"
            }
        },
        "metas_sonhos": []
    }

def salvar_banco(dados):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

if "db" not in st.session_state:
    st.session_state.db = carregar_banco()

# ---------------------------------------------------
# STATES
# ---------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------
if not st.session_state.logged_in:

    _, col, _ = st.columns([1,1,1])

    with col:

        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        st.markdown("""
        <h1 style='text-align:center;
        color:#60a5fa;
        font-size:58px;
        font-weight:900;
        margin-bottom:35px;'>
        METAFLUX
        </h1>
        """, unsafe_allow_html=True)

        # LOGIN
        if st.session_state.auth_mode == "login":

            usuario = st.text_input(
                "Usuário",
                placeholder="👤 Seu usuário"
            )

            senha = st.text_input(
                "Senha",
                type="password",
                placeholder="🔒 Sua senha"
            )

            c1, c2 = st.columns([1,1])

            with c1:
                lembrar = st.checkbox("Lembrar")

            with c2:
                if st.button("Esqueci a senha"):
                    st.session_state.auth_mode = "recover"
                    st.rerun()

            st.write("")

            if st.button("ACESSAR PAINEL"):

                if usuario in st.session_state.db["users"]:
                    if st.session_state.db["users"][usuario]["password"] == senha:
                        st.session_state.logged_in = True
                        st.session_state.current_user = usuario
                        st.rerun()

                st.error("Usuário ou senha incorretos")

            st.write("")

            if st.button("Criar uma conta"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        # CADASTRO
        elif st.session_state.auth_mode == "signup":

            st.subheader("Criar Conta")

            novo_user = st.text_input("Usuário")
            nova_senha = st.text_input("Senha", type="password")
            pergunta = st.text_input("Nome do filho?")

            if st.button("CADASTRAR"):
                if novo_user and nova_senha and pergunta:
                    st.session_state.db["users"][novo_user] = {
                        "password": nova_senha,
                        "security_answer": pergunta
                    }

                    salvar_banco(st.session_state.db)
                    st.success("Conta criada!")

            if st.button("Voltar"):
                st.session_state.auth_mode = "login"
                st.rerun()

        # RECUPERAR
        elif st.session_state.auth_mode == "recover":

            st.subheader("Recuperar Senha")

            user = st.text_input("Usuário")

            if user in st.session_state.db["users"]:

                resposta = st.text_input("Resposta")

                if st.button("VER SENHA"):

                    real = st.session_state.db["users"][user]["security_answer"]

                    if resposta.lower() == real.lower():
                        senha = st.session_state.db["users"][user]["password"]
                        st.success(f"Sua senha é: {senha}")
                    else:
                        st.error("Resposta incorreta")

            if st.button("Voltar"):
                st.session_state.auth_mode = "login"
                st.rerun()

        st.markdown("""
        <p style='text-align:center;
        color:#64748b;
        font-size:12px;
        margin-top:25px;'>
        © 2026 MetaFlux. Direitos reservados.
        </p>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# APP LOGADO
# ---------------------------------------------------
else:

    with st.sidebar:

        try:
            st.image("logo.png", use_column_width=True)
        except:
            st.title("📈 METAFLUX")

        st.divider()

        privacidade = st.toggle("👁️ Modo Privacidade")

        st.divider()

        mes = st.selectbox(
            "Mês",
            [
                "Janeiro","Fevereiro","Março","Abril",
                "Maio","Junho","Julho","Agosto",
                "Setembro","Outubro","Novembro","Dezembro"
            ],
            index=3
        )

        if privacidade:
            renda = 3000.0
            meta_inv = 1000.0
        else:
            renda = st.number_input("Sua Renda", value=3000.0)
            meta_inv = st.number_input("Meta Investimento", value=1000.0)

        if st.button("🚪 Sair"):
            st.session_state.logged_in = False
            st.rerun()

    def fmt(v):
        if privacidade:
            return "R$ *****"
        return f"R$ {v:,.2f}"

    if mes not in st.session_state.db:
        st.session_state.db[mes] = {
            "gastos": [],
            "investido": 0
        }

    dados = st.session_state.db[mes]

    t_pago = sum(float(x["valor"]) for x in dados["gastos"] if x["pago"])
    t_pend = sum(float(x["valor"]) for x in dados["gastos"] if not x["pago"])
    investido = float(dados["investido"])
    sonhos = sum(float(x["acumulado"]) for x in st.session_state.db["metas_sonhos"])
    saldo = renda - t_pago - t_pend - investido

    st.title(f"🚀 Dashboard {mes}")

    a,b,c,d = st.columns(4)

    a.metric("✅ Pagos", fmt(t_pago))
    b.metric("⏳ Pendentes", fmt(t_pend))
    c.metric("🚀 Sonhos", fmt(sonhos))
    d.metric("💰 Saldo", fmt(saldo))

    progresso = min(investido/meta_inv,1.0) if meta_inv > 0 else 0
    st.progress(progresso)

    # GRAFICO
    st.subheader("📊 Gráfico")

    df = pd.DataFrame({
        "Tipo":["Pago","Pendente","Investido","Sonhos","Saldo"],
        "Valor":[t_pago,t_pend,investido,sonhos,max(0,saldo)]
    })

    df = df[df["Valor"] > 0]

    if not df.empty:
        fig = px.pie(df, values="Valor", names="Tipo", hole=0.5)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)

    salvar_banco(st.session_state.db)

