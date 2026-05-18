from modules.exportar import tela_exportar
from modules.teste_supabase import testar_supabase
from modules.recorrencias import tela_recorrencias
from modules.dashboard import tela_dashboard_profissional
from modules.faturas import tela_faturas
from modules.contas import tela_contas
from modules.receitas import tela_receitas
from modules.despesas import tela_despesas
from modules.cartoes import tela_cartoes
from utils.database import criar_tabelas

import base64
import hashlib
import hmac
from modules.exportar import tela_exportar
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP_NAME = "MetaFlux Pro"
DB_FILE = "metafluxo.sqlite3"
LOGO_FILE = "logo.png"
MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
CATEGORIAS = ["🏠 Moradia", "🍎 Alimentação", "🚗 Transporte", "🎡 Lazer", "💊 Saúde", "📚 Estudos", "🛠️ Outros"]

st.set_page_config(page_title=f"{APP_NAME} 📈", layout="wide", page_icon="📈")

criar_tabelas()

# ------------------------- ESTILO -------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #020617;
        background-image: radial-gradient(circle at top right, rgba(37,99,235,0.35), #020617 42%);
        color: #f8fafc;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
        border-right: 1px solid #1e293b;
    }
    .main-card {
        background: rgba(15, 23, 42, 0.92);
        padding: 28px;
        border-radius: 24px;
        border: 1px solid #334155;
        box-shadow: 0 18px 45px rgba(0,0,0,0.35);
    }
    .login-title {text-align:center; color:#60a5fa; font-weight:900; margin-bottom:8px;}
    .login-subtitle {text-align:center; color:#94a3b8; margin-bottom:25px;}
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        border: none !important;
        min-height: 42px;
    }
    .stButton>button:hover {background-color:#1d4ed8 !important;}
    .stMetric {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid #334155;
        border-radius: 18px;
        padding: 16px;
    }
    div[data-baseweb="input"], div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        border-color: #334155 !important;
        border-radius: 12px !important;
    }
    input, textarea { color: #f8fafc !important; }
    .small-muted {color:#94a3b8; font-size:0.85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------- BANCO SQLITE -------------------------
def conectar():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

conn = conectar()


def init_db():
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            security_hash TEXT NOT NULL,
            security_salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS month_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mes TEXT NOT NULL,
            renda REAL NOT NULL DEFAULT 3000,
            meta_investimento REAL NOT NULL DEFAULT 1000,
            investido REAL NOT NULL DEFAULT 0,
            UNIQUE(user_id, mes),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mes TEXT NOT NULL,
            item TEXT NOT NULL,
            categoria TEXT NOT NULL DEFAULT '🛠️ Outros',
            valor REAL NOT NULL DEFAULT 0,
            pago INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sonhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            alvo REAL NOT NULL DEFAULT 0,
            acumulado REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()


def hash_texto(texto: str, salt: str | None = None):
    if salt is None:
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
    digest = hashlib.pbkdf2_hmac("sha256", texto.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return base64.b64encode(digest).decode("utf-8"), salt


def verificar(texto: str, digest_salvo: str, salt: str):
    digest, _ = hash_texto(texto, salt)
    return hmac.compare_digest(digest, digest_salvo)


def criar_usuario(username, senha, resposta):
    username = username.strip().lower()
    senha_hash, salt = hash_texto(senha)
    resp_hash, resp_salt = hash_texto(resposta.strip().lower())
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, security_hash, security_salt, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, senha_hash, salt, resp_hash, resp_salt, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        return True, "Conta criada com sucesso."
    except sqlite3.IntegrityError:
        return False, "Esse usuário já existe."


def buscar_usuario(username):
    return conn.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),)).fetchone()


def login(username, senha):
    user = buscar_usuario(username)
    if not user:
        return None
    if verificar(senha, user["password_hash"], user["salt"]):
        return dict(user)
    return None


def redefinir_senha(username, resposta, nova_senha):
    user = buscar_usuario(username)
    if not user:
        return False
    if not verificar(resposta.strip().lower(), user["security_hash"], user["security_salt"]):
        return False
    senha_hash, salt = hash_texto(nova_senha)
    conn.execute("UPDATE users SET password_hash=?, salt=? WHERE id=?", (senha_hash, salt, user["id"]))
    conn.commit()
    return True


def garantir_config_mes(user_id, mes):
    conn.execute("INSERT OR IGNORE INTO month_config (user_id, mes) VALUES (?, ?)", (user_id, mes))
    conn.commit()
    return conn.execute("SELECT * FROM month_config WHERE user_id=? AND mes=?", (user_id, mes)).fetchone()


def atualizar_config(user_id, mes, renda, meta, investido):
    conn.execute(
        "UPDATE month_config SET renda=?, meta_investimento=?, investido=? WHERE user_id=? AND mes=?",
        (float(renda), float(meta), float(investido), user_id, mes),
    )
    conn.commit()


def listar_gastos(user_id, mes):
    return conn.execute("SELECT * FROM gastos WHERE user_id=? AND mes=? ORDER BY id DESC", (user_id, mes)).fetchall()


def adicionar_gasto(user_id, mes):
    conn.execute(
        "INSERT INTO gastos (user_id, mes, item, categoria, valor, pago, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, mes, "Novo gasto", "🛠️ Outros", 0.0, 0, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()


def atualizar_gasto(gasto_id, item, categoria, valor, pago):
    conn.execute("UPDATE gastos SET item=?, categoria=?, valor=?, pago=? WHERE id=?", (item, categoria, float(valor), int(pago), gasto_id))
    conn.commit()


def deletar_gasto(gasto_id):
    conn.execute("DELETE FROM gastos WHERE id=?", (gasto_id,))
    conn.commit()


def listar_sonhos(user_id):
    return conn.execute("SELECT * FROM sonhos WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()


def criar_sonho(user_id, nome, alvo):
    conn.execute(
        "INSERT INTO sonhos (user_id, nome, alvo, acumulado, created_at) VALUES (?, ?, ?, 0, ?)",
        (user_id, nome, float(alvo), datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()


def atualizar_sonho(sonho_id, acumulado):
    conn.execute("UPDATE sonhos SET acumulado=? WHERE id=?", (float(acumulado), sonho_id))
    conn.commit()


def deletar_sonho(sonho_id):
    conn.execute("DELETE FROM sonhos WHERE id=?", (sonho_id,))
    conn.commit()


def fmt(valor, privacidade=False):
    return "R$ *****" if privacidade else f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def migrar_admin_padrao():
    if not buscar_usuario("admin"):
        criar_usuario("admin", "123", "Murillo")

init_db()
migrar_admin_padrao()

# ------------------------- SESSÃO -------------------------
for chave, padrao in {
    "logged_in": False,
    "auth_mode": "login",
    "current_user": None,
    "current_user_id": None,
}.items():
    if chave not in st.session_state:
        st.session_state[chave] = padrao

# ------------------------- LOGIN -------------------------
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.25, 1])
    with col:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown(f"<h1 class='login-title'>{APP_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p class='login-subtitle'>Controle financeiro simples, seguro e organizado.</p>", unsafe_allow_html=True)

        if st.session_state.auth_mode == "login":
            usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            if st.button("ACESSAR PAINEL", use_container_width=True):
                user = login(usuario, senha)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user["username"]
                    st.session_state.current_user_id = user["id"]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
            c1, c2 = st.columns(2)
            if c1.button("Criar conta", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()
            if c2.button("Esqueci a senha", use_container_width=True):
                st.session_state.auth_mode = "recover"
                st.rerun()
            st.caption("Usuário inicial para teste: admin | senha: 123")

        elif st.session_state.auth_mode == "signup":
            usuario = st.text_input("Novo usuário")
            senha = st.text_input("Senha", type="password")
            resposta = st.text_input("Resposta de segurança: nome do filho ou palavra-chave")
            if st.button("CADASTRAR", use_container_width=True):
                if len(usuario.strip()) < 3 or len(senha) < 3 or not resposta.strip():
                    st.warning("Preencha usuário, senha e resposta de segurança.")
                else:
                    ok, msg = criar_usuario(usuario, senha, resposta)
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        time.sleep(1)
                        st.session_state.auth_mode = "login"
                        st.rerun()
            if st.button("Voltar", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

        elif st.session_state.auth_mode == "recover":
            usuario = st.text_input("Seu usuário")
            resposta = st.text_input("Resposta de segurança")
            nova = st.text_input("Nova senha", type="password")
            if st.button("SALVAR NOVA SENHA", use_container_width=True):
                if usuario and resposta and nova and redefinir_senha(usuario, resposta, nova):
                    st.success("Senha alterada. Faça login novamente.")
                    time.sleep(1)
                    st.session_state.auth_mode = "login"
                    st.rerun()
                else:
                    st.error("Dados incorretos.")
            if st.button("Voltar", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------- APP -------------------------
user_id = st.session_state.current_user_id
usuario = st.session_state.current_user

with st.sidebar:
    try:
        st.image(LOGO_FILE, use_container_width=True)
    except:
        st.title(f"📈 {APP_NAME}")

    st.caption(f"Usuário: **{usuario}**")
    st.divider()
    privacidade = st.toggle("👁️ Modo privacidade", value=False)
    mes = st.selectbox("Mês", MESES, index=datetime.now().month - 1)
    config = garantir_config_mes(user_id, mes)
    renda = st.number_input("Renda do mês (R$)", min_value=0.0, value=float(config["renda"]), step=100.0, format="%.2f", disabled=privacidade)
    meta_inv = st.number_input("Meta de investimento (R$)", min_value=0.0, value=float(config["meta_investimento"]), step=50.0, format="%.2f", disabled=privacidade)
    investido = st.number_input("Investido no mês (R$)", min_value=0.0, value=float(config["investido"]), step=50.0, format="%.2f", disabled=privacidade)
    atualizar_config(user_id, mes, renda, meta_inv, investido)
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.current_user_id = None
        st.rerun()

st.title(f"🚀 Dashboard financeiro - {mes}")

# Dados
gastos = listar_gastos(user_id, mes)
sonhos = listar_sonhos(user_id)
total_pago = sum(float(g["valor"]) for g in gastos if g["pago"])
total_pendente = sum(float(g["valor"]) for g in gastos if not g["pago"])
total_sonhos = sum(float(s["acumulado"]) for s in sonhos)
saldo_livre = float(renda) - total_pago - total_pendente - float(investido)
progresso_inv = min(float(investido) / float(meta_inv), 1.0) if float(meta_inv) > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("✅ Pagos", fmt(total_pago, privacidade))
c2.metric("⏳ Pendentes", fmt(total_pendente, privacidade))
c3.metric("🚀 Sonhos", fmt(total_sonhos, privacidade))
c4.metric("💰 Saldo livre", fmt(saldo_livre, privacidade))

st.markdown(f"**Meta de investimento: {progresso_inv * 100:.1f}%**")
st.progress(progresso_inv)
st.caption(f"Faltam {fmt(max(0, float(meta_inv) - float(investido)), privacidade)} para bater a meta do mês.")
st.divider()

aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9, aba10 = st.tabs([
    "📝 Lançamentos",
    "🏦 Contas",
    "💵 Receitas",
    "💳 Despesas",
    "📅 Recorrências",
    "💳 Cartões",
    "🧾 Faturas",
    "📊 Análises",
    "🚀 Meus sonhos",
    "📤 Exportar"
])

with aba1:
    col_add, col_info = st.columns([1, 3])
    if col_add.button("➕ Novo gasto", use_container_width=True):
        adicionar_gasto(user_id, mes)
        st.rerun()
    col_info.caption("Edite os campos e marque como pago. As alterações são salvas automaticamente.")

    if not gastos:
        st.info("Nenhum gasto cadastrado neste mês.")
    for gasto in gastos:
        with st.expander(f"📦 {gasto['item']} - {fmt(gasto['valor'], privacidade)}", expanded=False):
            a, b, c, d, e = st.columns([2.2, 1.5, 1.3, 0.8, 0.7])
            item = a.text_input("Item", value=gasto["item"], key=f"item_{gasto['id']}")
            categoria = b.selectbox("Categoria", CATEGORIAS, index=CATEGORIAS.index(gasto["categoria"]) if gasto["categoria"] in CATEGORIAS else len(CATEGORIAS)-1, key=f"cat_{gasto['id']}")
            valor = c.number_input("Valor", min_value=0.0, value=float(gasto["valor"]), step=10.0, format="%.2f", key=f"valor_{gasto['id']}", disabled=privacidade)
            pago = d.checkbox("Pago", value=bool(gasto["pago"]), key=f"pago_{gasto['id']}")
            atualizar_gasto(gasto["id"], item, categoria, valor, pago)
            if e.button("🗑️", key=f"del_{gasto['id']}"):
                deletar_gasto(gasto["id"])
                st.rerun()

with aba2:

    tela_contas(user_id)

with aba3:

    tela_receitas(user_id, mes)

with aba4:

    tela_despesas(user_id, mes)

with aba5:
    tela_recorrencias(user_id, mes)

with aba6:

    tela_cartoes(user_id, mes)

with aba7:
    tela_faturas(user_id, mes)

with aba8:

    tela_dashboard_profissional(
        user_id,
        mes,
        renda_manual=renda,
        investido=investido,
        privacidade=privacidade
    )

with aba9:
    s1, s2 = st.columns([1, 2])
    with s1:
        with st.form("novo_sonho"):
            nome = st.text_input("Nome do objetivo")
            alvo = st.number_input("Valor da meta (R$)", min_value=0.0, step=100.0, format="%.2f")
            enviado = st.form_submit_button("Criar objetivo")
            if enviado:
                if nome.strip() and alvo > 0:
                    criar_sonho(user_id, nome.strip(), alvo)
                    st.rerun()
                else:
                    st.warning("Informe nome e valor da meta.")
    with s2:
        if not sonhos:
            st.info("Nenhum sonho cadastrado.")
        for sonho in sonhos:
            alvo = float(sonho["alvo"])
            acumulado = float(sonho["acumulado"])
            prog = min(acumulado / alvo, 1.0) if alvo > 0 else 0
            with st.expander(f"⭐ {sonho['nome']} - {prog*100:.1f}%"):
                st.write(f"Guardado: **{fmt(acumulado, privacidade)}** de **{fmt(alvo, privacidade)}**")
                st.progress(prog)
                a, b = st.columns([2, 1])
                novo_acumulado = a.number_input("Valor acumulado", min_value=0.0, value=acumulado, step=50.0, format="%.2f", key=f"sonho_{sonho['id']}", disabled=privacidade)
                atualizar_sonho(sonho["id"], novo_acumulado)
                if b.button("🗑️ Excluir", key=f"del_sonho_{sonho['id']}"):
                    deletar_sonho(sonho["id"])
                    st.rerun()

with aba10:
    tela_exportar(user_id, mes)

testar_supabase()
