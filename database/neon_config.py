import streamlit as st
from sqlalchemy import create_engine, text

DATABASE_URL = st.secrets["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

def testar_conexao():
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("SELECT current_database(), current_user")
            ).fetchone()

            return {
                "sucesso": True,
                "banco": resultado[0],
                "usuario": resultado[1]
            }

    except Exception as erro:
        return {
            "sucesso": False,
            "erro": str(erro)
        }
