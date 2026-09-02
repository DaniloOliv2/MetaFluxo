from modules.ia_financeira import tela_ia_financeira
from modules.metas import tela_metas
from modules.investimentos import tela_investimentos
from modules.exportar import tela_exportar
from modules.recorrencias import tela_recorrencias
from modules.dashboard import tela_dashboard_profissional
from modules.faturas import tela_faturas
from modules.contas import tela_contas
from modules.receitas import tela_receitas
from modules.despesas import tela_despesas
from modules.cartoes import tela_cartoes
from database.neon_config import executar_sql, buscar_todos, buscar_um

import base64
import hashlib
import hmac
import os
import time
from datetime import datetime

import streamlit as st


APP_NAME = "MetaFlux Pro"
LOGO_FILE = "logo.png"

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

CATEGORIAS = [
    "🏠 Moradia",
    "🍎 Alimentação",
    "🚗 Transporte",
    "🎡 Lazer",
    "💊 Saúde",
    "📚 Estudos",
    "🛠️ Outros"
]


st.set_page_config(
    page_title=f"{APP_NAME} 📈",
    layout="wide",
    page_icon="📈"
)


# =========================================================
# ESTILO
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #020617;
        background-image: radial-gradient(
            circle at top right,
            rgba(37,99,235,0.35),
            #020617 42%
        );
        color: #f8fafc;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #0f172a 0%,
            #020617 100%
        );
        border-right: 1px solid #1e293b;
    }

    .main-card {
        background: rgba(15, 23, 42, 0.92);
        padding: 28px;
        border-radius: 24px;
        border: 1px solid #334155;
        box-shadow: 0 18px 45px rgba(0,0,0,0.35);
    }

    .login-title {
        text-align: center;
        color: #60a5fa;
        font-weight: 900;
        margin-bottom: 8px;
    }

    .login-subtitle {
        text-align: center;
        color: #94a3b8;
        margin-bottom: 25px;
    }

    .stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        border: none !important;
        min-height: 42px;
    }

    .stButton > button:hover {
        background-color: #1d4ed8 !important;
    }

    .stMetric {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid #334155;
        border-radius: 18px;
        padding: 16px;
    }

    div[data-baseweb="input"],
    div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        border-color: #334155 !important;
        border-radius: 12px !important;
    }

    input,
    textarea {
        color: #f8fafc !important;
    }

    .small-muted {
        color: #94a3b8;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# BANCO PRINCIPAL DO APP - NEON POSTGRESQL
# =========================================================

def garantir_tabelas_app():
    executar_sql("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            security_hash TEXT NOT NULL,
            security_salt TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    executar_sql("""
        CREATE TABLE IF NOT EXISTS month_config (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            mes TEXT NOT NULL,
            renda NUMERIC(15,2) NOT NULL DEFAULT 3000,
            meta_investimento NUMERIC(15,2) NOT NULL DEFAULT 1000,
            investido NUMERIC(15,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_month_config_user_mes
                UNIQUE (user_id, mes),
            CONSTRAINT fk_month_config_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    executar_sql("""
        CREATE TABLE IF NOT EXISTS gastos (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            mes TEXT NOT NULL,
            item TEXT NOT NULL,
            categoria TEXT NOT NULL DEFAULT '🛠️ Outros',
            valor NUMERIC(15,2) NOT NULL DEFAULT 0,
            pago BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_gastos_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)


# =========================================================
# SEGURANÇA / LOGIN
# =========================================================

def hash_texto(texto: str, salt: str | None = None):
    if salt is None:
        salt = base64.b64encode(
            os.urandom(16)
        ).decode("utf-8")

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        texto.encode("utf-8"),
        salt.encode("utf-8"),
        120_000
    )

    return (
        base64.b64encode(digest).decode("utf-8"),
        salt
    )


def verificar(texto: str, digest_salvo: str, salt: str):
    digest, _ = hash_texto(
        texto,
        salt
    )

    return hmac.compare_digest(
        digest,
        digest_salvo
    )


def criar_usuario(username, senha, resposta):
    username = username.strip().lower()
    resposta = resposta.strip().lower()

    if buscar_usuario(username):
        return False, "Esse usuário já existe."

    senha_hash, salt = hash_texto(
        senha
    )

    resp_hash, resp_salt = hash_texto(
        resposta
    )

    try:
        executar_sql("""
            INSERT INTO users (
                username,
                password_hash,
                salt,
                security_hash,
                security_salt
            )
            VALUES (
                :username,
                :password_hash,
                :salt,
                :security_hash,
                :security_salt
            )
        """, {
            "username": username,
            "password_hash": senha_hash,
            "salt": salt,
            "security_hash": resp_hash,
            "security_salt": resp_salt
        })

        return True, "Conta criada com sucesso."

    except Exception:
        return False, "Não foi possível criar a conta."


def buscar_usuario(username):
    username = username.strip().lower()

    if not username:
        return None

    return buscar_um("""
        SELECT *
        FROM users
        WHERE username = :username
        LIMIT 1
    """, {
        "username": username
    })


def login(username, senha):
    user = buscar_usuario(
        username
    )

    if not user:
        return None

    if verificar(
        senha,
        user["password_hash"],
        user["salt"]
    ):
        return user

    return None


def redefinir_senha(username, resposta, nova_senha):
    user = buscar_usuario(
        username
    )

    if not user:
        return False

    if not verificar(
        resposta.strip().lower(),
        user["security_hash"],
        user["security_salt"]
    ):
        return False

    senha_hash, salt = hash_texto(
        nova_senha
    )

    executar_sql("""
        UPDATE users
        SET
            password_hash = :password_hash,
            salt = :salt
        WHERE id = :user_id
    """, {
        "password_hash": senha_hash,
        "salt": salt,
        "user_id": user["id"]
    })

    return True


def migrar_admin_padrao():
    if not buscar_usuario("admin"):
        criar_usuario(
            "admin",
            "123",
            "Murillo"
        )


# =========================================================
# CONFIGURAÇÃO MENSAL
# =========================================================

def garantir_config_mes(user_id, mes):
    executar_sql("""
        INSERT INTO month_config (
            user_id,
            mes
        )
        VALUES (
            :user_id,
            :mes
        )
        ON CONFLICT (user_id, mes)
        DO NOTHING
    """, {
        "user_id": user_id,
        "mes": mes
    })

    return buscar_um("""
        SELECT *
        FROM month_config
        WHERE user_id = :user_id
          AND mes = :mes
        LIMIT 1
    """, {
        "user_id": user_id,
        "mes": mes
    })


def atualizar_config(
    user_id,
    mes,
    renda,
    meta,
    investido
):
    executar_sql("""
        INSERT INTO month_config (
            user_id,
            mes,
            renda,
            meta_investimento,
            investido
        )
        VALUES (
            :user_id,
            :mes,
            :renda,
            :meta,
            :investido
        )
        ON CONFLICT (user_id, mes)
        DO UPDATE SET
            renda = EXCLUDED.renda,
            meta_investimento = EXCLUDED.meta_investimento,
            investido = EXCLUDED.investido
    """, {
        "user_id": user_id,
        "mes": mes,
        "renda": float(renda),
        "meta": float(meta),
        "investido": float(investido)
    })


# =========================================================
# LANÇAMENTOS / GASTOS
# =========================================================

def listar_gastos(user_id, mes):
    return buscar_todos("""
        SELECT *
        FROM gastos
        WHERE user_id = :user_id
          AND mes = :mes
        ORDER BY id DESC
    """, {
        "user_id": user_id,
        "mes": mes
    })


def adicionar_gasto(user_id, mes):
    executar_sql("""
        INSERT INTO gastos (
            user_id,
            mes,
            item,
            categoria,
            valor,
            pago
        )
        VALUES (
            :user_id,
            :mes,
            'Novo gasto',
            '🛠️ Outros',
            0,
            FALSE
        )
    """, {
        "user_id": user_id,
        "mes": mes
    })


def atualizar_gasto(
    gasto_id,
    user_id,
    item,
    categoria,
    valor,
    pago
):
    executar_sql("""
        UPDATE gastos
        SET
            item = :item,
            categoria = :categoria,
            valor = :valor,
            pago = :pago
        WHERE id = :gasto_id
          AND user_id = :user_id
    """, {
        "item": item,
        "categoria": categoria,
        "valor": float(valor),
        "pago": bool(pago),
        "gasto_id": gasto_id,
        "user_id": user_id
    })


def deletar_gasto(
    gasto_id,
    user_id
):
    executar_sql("""
        DELETE FROM gastos
        WHERE id = :gasto_id
          AND user_id = :user_id
    """, {
        "gasto_id": gasto_id,
        "user_id": user_id
    })


# =========================================================
# FORMATAÇÃO
# =========================================================

def fmt(
    valor,
    privacidade=False
):
    if privacidade:
        return "R$ *****"

    try:
        return (
            f"R$ {float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except Exception:
        return "R$ 0,00"


# =========================================================
# INICIALIZAÇÃO DO BANCO
# =========================================================

garantir_tabelas_app()
migrar_admin_padrao()


# =========================================================
# SESSÃO
# =========================================================

for chave, padrao in {
    "logged_in": False,
    "auth_mode": "login",
    "current_user": None,
    "current_user_id": None,
}.items():
    if chave not in st.session_state:
        st.session_state[chave] = padrao


# =========================================================
# LOGIN
# =========================================================

if not st.session_state.logged_in:
    _, col, _ = st.columns(
        [1, 1.25, 1]
    )

    with col:
        st.markdown(
            '<div class="main-card">',
            unsafe_allow_html=True
        )

        st.markdown(
            f"<h1 class='login-title'>{APP_NAME}</h1>",
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <p class='login-subtitle'>
                Controle financeiro simples, seguro e organizado.
            </p>
            """,
            unsafe_allow_html=True
        )

        if st.session_state.auth_mode == "login":
            usuario_input = st.text_input(
                "Usuário",
                placeholder="Digite seu usuário",
                key="login_usuario"
            )

            senha_input = st.text_input(
                "Senha",
                type="password",
                placeholder="Digite sua senha",
                key="login_senha"
            )

            if st.button(
                "ACESSAR PAINEL",
                use_container_width=True,
                key="login_acessar"
            ):
                user = login(
                    usuario_input,
                    senha_input
                )

                if user:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user["username"]
                    st.session_state.current_user_id = user["id"]

                    st.rerun()

                else:
                    st.error(
                        "Usuário ou senha incorretos."
                    )

            c1, c2 = st.columns(2)

            if c1.button(
                "Criar conta",
                use_container_width=True,
                key="login_criar_conta"
            ):
                st.session_state.auth_mode = "signup"
                st.rerun()

            if c2.button(
                "Esqueci a senha",
                use_container_width=True,
                key="login_esqueci"
            ):
                st.session_state.auth_mode = "recover"
                st.rerun()

            st.caption(
                "Usuário inicial para teste: admin | senha: 123"
            )

        elif st.session_state.auth_mode == "signup":
            usuario_novo = st.text_input(
                "Novo usuário",
                key="signup_usuario"
            )

            senha_nova = st.text_input(
                "Senha",
                type="password",
                key="signup_senha"
            )

            resposta = st.text_input(
                "Resposta de segurança: nome do filho ou palavra-chave",
                key="signup_resposta"
            )

            if st.button(
                "CADASTRAR",
                use_container_width=True,
                key="signup_cadastrar"
            ):
                if (
                    len(usuario_novo.strip()) < 3
                    or len(senha_nova) < 3
                    or not resposta.strip()
                ):
                    st.warning(
                        "Preencha usuário, senha e resposta de segurança."
                    )

                else:
                    ok, msg = criar_usuario(
                        usuario_novo,
                        senha_nova,
                        resposta
                    )

                    if ok:
                        st.success(msg)
                        time.sleep(1)

                        st.session_state.auth_mode = "login"
                        st.rerun()

                    else:
                        st.error(msg)

            if st.button(
                "Voltar",
                use_container_width=True,
                key="signup_voltar"
            ):
                st.session_state.auth_mode = "login"
                st.rerun()

        elif st.session_state.auth_mode == "recover":
            usuario_recuperar = st.text_input(
                "Seu usuário",
                key="recover_usuario"
            )

            resposta_recuperar = st.text_input(
                "Resposta de segurança",
                key="recover_resposta"
            )

            nova_senha = st.text_input(
                "Nova senha",
                type="password",
                key="recover_nova_senha"
            )

            if st.button(
                "SALVAR NOVA SENHA",
                use_container_width=True,
                key="recover_salvar"
            ):
                if (
                    usuario_recuperar
                    and resposta_recuperar
                    and nova_senha
                    and redefinir_senha(
                        usuario_recuperar,
                        resposta_recuperar,
                        nova_senha
                    )
                ):
                    st.success(
                        "Senha alterada. Faça login novamente."
                    )

                    time.sleep(1)

                    st.session_state.auth_mode = "login"
                    st.rerun()

                else:
                    st.error(
                        "Dados incorretos."
                    )

            if st.button(
                "Voltar",
                use_container_width=True,
                key="recover_voltar"
            ):
                st.session_state.auth_mode = "login"
                st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    st.stop()


# =========================================================
# APP
# =========================================================

user_id = st.session_state.current_user_id
usuario = st.session_state.current_user


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    try:
        st.image(
            LOGO_FILE,
            use_container_width=True
        )

    except Exception:
        st.title(
            f"📈 {APP_NAME}"
        )

    st.caption(
        f"Usuário: **{usuario}**"
    )

    st.divider()

    privacidade = st.toggle(
        "👁️ Modo privacidade",
        value=False,
        key="sidebar_privacidade"
    )

    mes = st.selectbox(
        "Mês",
        MESES,
        index=datetime.now().month - 1,
        key="sidebar_mes"
    )

    config = garantir_config_mes(
        user_id,
        mes
    )

    renda = st.number_input(
        "Renda do mês (R$)",
        min_value=0.0,
        value=float(config["renda"]),
        step=100.0,
        format="%.2f",
        disabled=privacidade,
        key=f"sidebar_renda_{user_id}_{mes}"
    )

    meta_inv = st.number_input(
        "Meta de investimento (R$)",
        min_value=0.0,
        value=float(config["meta_investimento"]),
        step=50.0,
        format="%.2f",
        disabled=privacidade,
        key=f"sidebar_meta_{user_id}_{mes}"
    )

    investido = st.number_input(
        "Investido no mês (R$)",
        min_value=0.0,
        value=float(config["investido"]),
        step=50.0,
        format="%.2f",
        disabled=privacidade,
        key=f"sidebar_investido_{user_id}_{mes}"
    )

    atualizar_config(
        user_id,
        mes,
        renda,
        meta_inv,
        investido
    )

    st.divider()

    if st.button(
        "🚪 Sair",
        use_container_width=True,
        key="sidebar_sair"
    ):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.current_user_id = None
        st.session_state.auth_mode = "login"

        st.rerun()


# =========================================================
# DASHBOARD SUPERIOR
# =========================================================

st.title(
    f"🚀 Dashboard financeiro - {mes}"
)

gastos = listar_gastos(
    user_id,
    mes
)

total_pago = sum(
    float(g["valor"])
    for g in gastos
    if bool(g["pago"])
)

total_pendente = sum(
    float(g["valor"])
    for g in gastos
    if not bool(g["pago"])
)

saldo_livre = (
    float(renda)
    - total_pago
    - total_pendente
    - float(investido)
)

progresso_inv = (
    min(
        float(investido) / float(meta_inv),
        1.0
    )
    if float(meta_inv) > 0
    else 0
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "✅ Pagos",
    fmt(
        total_pago,
        privacidade
    )
)

c2.metric(
    "⏳ Pendentes",
    fmt(
        total_pendente,
        privacidade
    )
)

c3.metric(
    "💹 Investido no mês",
    fmt(
        investido,
        privacidade
    )
)

c4.metric(
    "💰 Saldo livre",
    fmt(
        saldo_livre,
        privacidade
    )
)

st.markdown(
    f"**Meta de investimento: {progresso_inv * 100:.1f}%**"
)

st.progress(
    progresso_inv
)

st.caption(
    f"Faltam {fmt(max(0, float(meta_inv) - float(investido)), privacidade)} "
    "para bater a meta do mês."
)

st.divider()


# =========================================================
# ABAS
# =========================================================

(
    aba1,
    aba2,
    aba3,
    aba4,
    aba5,
    aba6,
    aba7,
    aba8,
    aba9,
    aba10,
    aba11,
    aba12
) = st.tabs([
    "📝 Lançamentos",
    "🏦 Contas",
    "💵 Receitas",
    "💳 Despesas",
    "📅 Recorrências",
    "💳 Cartões",
    "🧾 Faturas",
    "📊 Análises",
    "🎯 Metas",
    "💹 Investimentos",
    "🤖 IA Financeira",
    "📤 Exportar"
])


# =========================================================
# LANÇAMENTOS
# =========================================================

with aba1:
    col_add, col_info = st.columns(
        [1, 3]
    )

    if col_add.button(
        "➕ Novo gasto",
        use_container_width=True,
        key=f"lancamentos_novo_{user_id}_{mes}"
    ):
        adicionar_gasto(
            user_id,
            mes
        )

        st.rerun()

    col_info.caption(
        "Edite os campos e marque como pago. "
        "As alterações são salvas automaticamente."
    )

    if not gastos:
        st.info(
            "Nenhum gasto cadastrado neste mês."
        )

    for gasto in gastos:
        gasto_id = gasto["id"]

        with st.expander(
            f"📦 {gasto['item']} - "
            f"{fmt(gasto['valor'], privacidade)}",
            expanded=False
        ):
            a, b, c, d, e = st.columns(
                [2.2, 1.5, 1.3, 0.8, 0.7]
            )

            item = a.text_input(
                "Item",
                value=gasto["item"],
                key=f"lanc_item_{user_id}_{mes}_{gasto_id}"
            )

            categoria = b.selectbox(
                "Categoria",
                CATEGORIAS,
                index=(
                    CATEGORIAS.index(gasto["categoria"])
                    if gasto["categoria"] in CATEGORIAS
                    else len(CATEGORIAS) - 1
                ),
                key=f"lanc_categoria_{user_id}_{mes}_{gasto_id}"
            )

            valor = c.number_input(
                "Valor",
                min_value=0.0,
                value=float(gasto["valor"]),
                step=10.0,
                format="%.2f",
                key=f"lanc_valor_{user_id}_{mes}_{gasto_id}",
                disabled=privacidade
            )

            pago = d.checkbox(
                "Pago",
                value=bool(gasto["pago"]),
                key=f"lanc_pago_{user_id}_{mes}_{gasto_id}"
            )

            atualizar_gasto(
                gasto_id=gasto_id,
                user_id=user_id,
                item=item,
                categoria=categoria,
                valor=valor,
                pago=pago
            )

            if e.button(
                "🗑️",
                key=f"lanc_excluir_{user_id}_{mes}_{gasto_id}"
            ):
                deletar_gasto(
                    gasto_id,
                    user_id
                )

                st.rerun()


# =========================================================
# CONTAS
# =========================================================

with aba2:
    tela_contas(
        user_id
    )


# =========================================================
# RECEITAS
# =========================================================

with aba3:
    tela_receitas(
        user_id,
        mes
    )


# =========================================================
# DESPESAS
# =========================================================

with aba4:
    tela_despesas(
        user_id,
        mes
    )


# =========================================================
# RECORRÊNCIAS
# =========================================================

with aba5:
    tela_recorrencias(
        user_id,
        mes
    )


# =========================================================
# CARTÕES
# =========================================================

with aba6:
    tela_cartoes(
        user_id,
        mes
    )


# =========================================================
# FATURAS
# =========================================================

with aba7:
    tela_faturas(
        user_id,
        mes
    )


# =========================================================
# ANÁLISES
# =========================================================

with aba8:
    tela_dashboard_profissional(
        user_id,
        mes,
        renda_manual=renda,
        investido=investido,
        privacidade=privacidade
    )


# =========================================================
# METAS
# =========================================================

with aba9:
    tela_metas(
        user_id
    )


# =========================================================
# INVESTIMENTOS
# =========================================================

with aba10:
    tela_investimentos(
        user_id
    )


# =========================================================
# IA FINANCEIRA
# =========================================================

with aba11:
    tela_ia_financeira(
        user_id,
        mes,
        renda_manual=renda
    )


# =========================================================
# EXPORTAR
# =========================================================

with aba12:
    tela_exportar(
        user_id,
        mes
    )
