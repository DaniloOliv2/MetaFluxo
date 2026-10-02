import streamlit as st
from contextlib import contextmanager
from sqlalchemy import create_engine, text

DATABASE_URL = st.secrets["DATABASE_URL"]

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)


@contextmanager
def transacao():
    """Executa várias operações SQL na mesma transação."""
    with engine.begin() as conexao:
        yield conexao


def executar_sql(sql, parametros=None, conexao=None):
    parametros = parametros or {}

    if conexao is not None:
        return conexao.execute(text(sql), parametros)

    with engine.begin() as nova_conexao:
        resultado = nova_conexao.execute(text(sql), parametros)
        return resultado.rowcount


def buscar_todos(sql, parametros=None, conexao=None):
    parametros = parametros or {}

    if conexao is not None:
        resultado = conexao.execute(text(sql), parametros)
        return [dict(linha._mapping) for linha in resultado]

    with engine.connect() as nova_conexao:
        resultado = nova_conexao.execute(text(sql), parametros)
        return [dict(linha._mapping) for linha in resultado]


def buscar_um(sql, parametros=None, conexao=None):
    parametros = parametros or {}

    if conexao is not None:
        resultado = conexao.execute(text(sql), parametros).fetchone()
    else:
        with engine.connect() as nova_conexao:
            resultado = nova_conexao.execute(text(sql), parametros).fetchone()

    return dict(resultado._mapping) if resultado else None
