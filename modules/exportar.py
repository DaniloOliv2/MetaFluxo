import streamlit as st
import pandas as pd
from io import BytesIO
from database.supabase_config import supabase


def gerar_excel(usuario_id, mes):
    tabelas = ["contas", "receitas", "despesas", "compras_cartao", "faturas"]
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for tabela in tabelas:
            resposta = supabase.table(tabela) \
                .select("*") \
                .eq("usuario_id", usuario_id) \
                .execute()

            df = pd.DataFrame(resposta.data)

            if not df.empty and "mes" in df.columns:
                df = df[df["mes"] == mes]

            df.to_excel(writer, sheet_name=tabela[:31], index=False)

    output.seek(0)
    return output


def tela_exportar(usuario_id, mes):
    st.subheader("📤 Exportar relatórios")

    st.info("Baixe seus dados financeiros em Excel.")

    arquivo_excel = gerar_excel(usuario_id, mes)

    st.download_button(
        label="📊 Baixar relatório Excel",
        data=arquivo_excel,
        file_name=f"relatorio_financeiro_{mes}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )