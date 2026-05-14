import streamlit as st
from database.supabase_config import conectar_supabase

def testar_supabase():

    try:
        supabase = conectar_supabase()

        st.success("✅ Conexão com Supabase realizada com sucesso!")

        resposta = supabase.table("usuarios").select("*").limit(1).execute()

        st.info("Supabase conectado e tabela acessada.")

    except Exception as erro:
        st.error(f"Erro ao conectar no Supabase: {erro}")