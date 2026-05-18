import streamlit as st
import pandas as pd
from io import BytesIO
from database.supabase_config import supabase

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

import matplotlib.pyplot as plt


def gerar_excel(usuario_id, mes):

    tabelas = [
        "contas",
        "receitas",
        "despesas",
        "compras_cartao",
        "faturas"
    ]

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

            df.to_excel(
                writer,
                sheet_name=tabela[:31],
                index=False
            )

    output.seek(0)

    return output


def buscar_dados(usuario_id, mes):

    receitas = supabase.table("receitas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .eq("mes", mes) \
        .execute()

    despesas = supabase.table("despesas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .eq("mes", mes) \
        .execute()

    faturas = supabase.table("faturas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .eq("mes", mes) \
        .execute()

    total_receitas = sum(
        float(r["valor"])
        for r in receitas.data
    )

    total_despesas = sum(
        float(d["valor"])
        for d in despesas.data
    )

    total_faturas = sum(
        float(f["valor"])
        for f in faturas.data
    )

    saldo = total_receitas - total_despesas - total_faturas

    return {
        "receitas": total_receitas,
        "despesas": total_despesas,
        "faturas": total_faturas,
        "saldo": saldo
    }


def gerar_grafico(dados):

    fig, ax = plt.subplots(figsize=(6, 4))

    categorias = [
        "Receitas",
        "Despesas",
        "Faturas"
    ]

    valores = [
        dados["receitas"],
        dados["despesas"],
        dados["faturas"]
    ]

    ax.bar(categorias, valores)

    ax.set_title("Resumo Financeiro")

    img = BytesIO()

    plt.savefig(img, format="png", bbox_inches="tight")

    img.seek(0)

    return img


def gerar_pdf(usuario_id, mes):

    dados = buscar_dados(usuario_id, mes)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    elementos = []

    titulo = Paragraph(
        f"<b>RELATÓRIO FINANCEIRO - {mes}</b>",
        styles["Title"]
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    resumo = [
        ["Indicador", "Valor"],
        ["Receitas", f"R$ {dados['receitas']:,.2f}"],
        ["Despesas", f"R$ {dados['despesas']:,.2f}"],
        ["Faturas", f"R$ {dados['faturas']:,.2f}"],
        ["Saldo Final", f"R$ {dados['saldo']:,.2f}"]
    ]

    tabela = Table(resumo, colWidths=[220, 220])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc"))
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 30))

    grafico = gerar_grafico(dados)

    from reportlab.platypus import Image

    elementos.append(Image(grafico, width=420, height=280))

    elementos.append(Spacer(1, 30))

    rodape = Paragraph(
        "MetaFlux Pro • Relatório Financeiro Premium",
        styles["Italic"]
    )

    elementos.append(rodape)

    doc.build(elementos)

    buffer.seek(0)

    return buffer


def tela_exportar(usuario_id, mes):

    st.subheader("📤 Exportar relatórios")

    st.info(
        "Baixe relatórios financeiros profissionais em Excel ou PDF."
    )

    col1, col2 = st.columns(2)

    with col1:

        arquivo_excel = gerar_excel(usuario_id, mes)

        st.download_button(
            label="📊 Baixar Excel",
            data=arquivo_excel,
            file_name=f"relatorio_financeiro_{mes}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col2:

        arquivo_pdf = gerar_pdf(usuario_id, mes)

        st.download_button(
            label="📄 Baixar PDF Executivo",
            data=arquivo_pdf,
            file_name=f"relatorio_financeiro_{mes}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
