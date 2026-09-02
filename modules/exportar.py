import streamlit as st
import pandas as pd
from io import BytesIO
from database.neon_config import buscar_todos

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
    consultas = {
        "contas": """
            SELECT *
            FROM contas
            WHERE usuario_id = :usuario_id
        """,
        "receitas": """
            SELECT *
            FROM receitas
            WHERE usuario_id = :usuario_id
              AND mes = :mes
        """,
        "despesas": """
            SELECT *
            FROM despesas
            WHERE usuario_id = :usuario_id
              AND mes = :mes
        """,
        "compras_cartao": """
            SELECT *
            FROM compras_cartao
            WHERE usuario_id = :usuario_id
              AND mes = :mes
        """,
        "faturas": """
            SELECT *
            FROM faturas
            WHERE usuario_id = :usuario_id
              AND mes = :mes
        """
    }

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for tabela, sql in consultas.items():
            parametros = {"usuario_id": usuario_id}

            if ":mes" in sql:
                parametros["mes"] = mes

            dados = buscar_todos(sql, parametros)
            df = pd.DataFrame(dados)

            df.to_excel(
                writer,
                sheet_name=tabela[:31],
                index=False
            )

    output.seek(0)
    return output


def buscar_dados(usuario_id, mes):
    receitas = buscar_todos("""
        SELECT valor
        FROM receitas
        WHERE usuario_id = :usuario_id
          AND mes = :mes
    """, {"usuario_id": usuario_id, "mes": mes})

    despesas = buscar_todos("""
        SELECT valor
        FROM despesas
        WHERE usuario_id = :usuario_id
          AND mes = :mes
    """, {"usuario_id": usuario_id, "mes": mes})

    faturas = buscar_todos("""
        SELECT valor
        FROM faturas
        WHERE usuario_id = :usuario_id
          AND mes = :mes
    """, {"usuario_id": usuario_id, "mes": mes})

    total_receitas = sum(float(r["valor"]) for r in receitas)
    total_despesas = sum(float(d["valor"]) for d in despesas)
    total_faturas = sum(float(f["valor"]) for f in faturas)

    saldo = total_receitas - total_despesas - total_faturas

    return {
        "receitas": total_receitas,
        "despesas": total_despesas,
        "faturas": total_faturas,
        "saldo": saldo
    }


def gerar_grafico(dados):
    fig, ax = plt.subplots(figsize=(7, 4))

    categorias = [
        "Receitas",
        "Despesas",
        "Faturas"
    ]

    valores = [
        max(float(dados["receitas"]), 0),
        max(float(dados["despesas"]), 0),
        max(float(dados["faturas"]), 0)
    ]

    cores = [
        "#22c55e",
        "#ef4444",
        "#3b82f6"
    ]

    if sum(valores) <= 0:
        categorias = ["Sem dados"]
        valores = [1]
        cores = ["#94a3b8"]

    ax.pie(
        valores,
        labels=categorias,
        autopct="%1.1f%%",
        startangle=90,
        colors=cores,
        wedgeprops={"width": 0.45}
    )

    ax.set_title(
        "Distribuição Financeira",
        fontsize=16,
        fontweight="bold"
    )

    plt.tight_layout()

    img = BytesIO()

    plt.savefig(
        img,
        format="png",
        bbox_inches="tight",
        transparent=True
    )

    plt.close(fig)
    img.seek(0)

    return img


def gerar_pdf(usuario_id, mes):
    from reportlab.platypus import Image
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle

    dados = buscar_dados(usuario_id, mes)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "TituloPremium",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=20
    )

    subtitulo_style = ParagraphStyle(
        "SubtituloPremium",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=11,
        textColor=colors.HexColor("#475569"),
        spaceAfter=25
    )

    elementos = []

    elementos.append(Paragraph("🚀 MetaFlux Pro", titulo_style))
    elementos.append(Paragraph(f"Relatório Executivo Financeiro • {mes}", subtitulo_style))

    saldo_cor = "#16a34a" if dados["saldo"] >= 0 else "#dc2626"
    saldo_texto = "Positivo" if dados["saldo"] >= 0 else "Negativo"

    cards = [
        ["Receitas", f"R$ {dados['receitas']:,.2f}", "Despesas", f"R$ {dados['despesas']:,.2f}"],
        ["Faturas", f"R$ {dados['faturas']:,.2f}", "Saldo Final", f"R$ {dados['saldo']:,.2f}"],
    ]

    tabela_cards = Table(cards, colWidths=[120, 120, 120, 120], rowHeights=42)

    tabela_cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
    ]))

    elementos.append(tabela_cards)
    elementos.append(Spacer(1, 25))

    resumo = Paragraph(
        f"""
        <b>Resumo inteligente:</b><br/>
        No mês de <b>{mes}</b>, o saldo final ficou <font color="{saldo_cor}"><b>{saldo_texto}</b></font>.
        Receitas totalizaram <b>R$ {dados['receitas']:,.2f}</b>, enquanto despesas e faturas somaram
        <b>R$ {(dados['despesas'] + dados['faturas']):,.2f}</b>.
        """,
        styles["BodyText"]
    )

    elementos.append(resumo)
    elementos.append(Spacer(1, 25))

    grafico = gerar_grafico(dados)
    elementos.append(Image(grafico, width=430, height=280))

    elementos.append(Spacer(1, 25))

    tabela_detalhe = [
        ["Categoria", "Valor"],
        ["Receitas", f"R$ {dados['receitas']:,.2f}"],
        ["Despesas", f"R$ {dados['despesas']:,.2f}"],
        ["Faturas", f"R$ {dados['faturas']:,.2f}"],
        ["Saldo Final", f"R$ {dados['saldo']:,.2f}"],
    ]

    tabela = Table(tabela_detalhe, colWidths=[250, 200])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))

    elementos.append(tabela)

    elementos.append(Spacer(1, 35))

    elementos.append(Paragraph(
        "MetaFlux Pro • Relatório Financeiro Executivo Premium",
        styles["Italic"]
    ))

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
