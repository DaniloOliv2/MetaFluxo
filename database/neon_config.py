import streamlit as st
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


def executar_sql(sql, parametros=None):
    parametros = parametros or {}

    with engine.begin() as conexao:
        resultado = conexao.execute(
            text(sql),
            parametros
        )

        return resultado


def buscar_todos(sql, parametros=None):
    parametros = parametros or {}

    with engine.connect() as conexao:
        resultado = conexao.execute(
            text(sql),
            parametros
        )

        return [dict(linha._mapping) for linha in resultado]


def buscar_um(sql, parametros=None):
    parametros = parametros or {}

    with engine.connect() as conexao:
        resultado = conexao.execute(
            text(sql),
            parametros
        ).fetchone()

        if resultado:
            return dict(resultado._mapping)

        return None
