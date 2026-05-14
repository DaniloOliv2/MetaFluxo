import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import conectar


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabelas_dashboard():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            conta_id INTEGER,
            valor REAL NOT NULL DEFAULT 0,
            recebida INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            conta_id INTEGER,
            valor REAL NOT NULL DEFAULT 0,
            paga INTEGER NOT NULL DEFAULT 0,
            vencimento TEXT,
            recorrente INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras_cartao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            cartao_id INTEGER NOT NULL,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor_total REAL NOT NULL DEFAULT 0,
            parcelas INTEGER NOT NULL DEFAULT 1,
            paga INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            cartao_id INTEGER NOT NULL,
            mes TEXT NOT NULL,
            valor REAL NOT NULL DEFAULT 0,
            paga INTEGER NOT NULL DEFAULT 0,
            data_pagamento TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(usuario_id, cartao_id, mes)
        )
    """)

    conn.commit()
    conn.close()


def buscar_resumo(usuario_id, mes):
    garantir_tabelas_dashboard()

    conn = conectar()
    cursor = conn.cursor()

    saldo_contas = cursor.execute("""
        SELECT COALESCE(SUM(saldo), 0) AS total
        FROM contas
        WHERE usuario_id = ?
    """, (usuario_id,)).fetchone()["total"]

    total_receitas = cursor.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM receitas
        WHERE usuario_id = ? AND mes = ? AND recebida = 1
    """, (usuario_id, mes)).fetchone()["total"]

    receitas_a_receber = cursor.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM receitas
        WHERE usuario_id = ? AND mes = ? AND recebida = 0
    """, (usuario_id, mes)).fetchone()["total"]

    total_despesas_pagas = cursor.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM despesas
        WHERE usuario_id = ? AND mes = ? AND paga = 1
    """, (usuario_id, mes)).fetchone()["total"]

    total_despesas_pendentes = cursor.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM despesas
        WHERE usuario_id = ? AND mes = ? AND paga = 0
    """, (usuario_id, mes)).fetchone()["total"]

    total_cartao_mes = cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0) AS total
        FROM compras_cartao
        WHERE usuario_id = ? AND mes = ?
    """, (usuario_id, mes)).fetchone()["total"]

    faturas_pendentes = cursor.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM faturas
        WHERE usuario_id = ? AND mes = ? AND paga = 0
    """, (usuario_id, mes)).fetchone()["total"]

    faturas_pagas = cursor.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM faturas
        WHERE usuario_id = ? AND mes = ? AND paga = 1
    """, (usuario_id, mes)).fetchone()["total"]

    conn.close()

    return {
        "saldo_contas": float(saldo_contas or 0),
        "total_receitas": float(total_receitas or 0),
        "receitas_a_receber": float(receitas_a_receber or 0),
        "total_despesas_pagas": float(total_despesas_pagas or 0),
        "total_despesas_pendentes": float(total_despesas_pendentes or 0),
        "total_cartao_mes": float(total_cartao_mes or 0),
        "faturas_pendentes": float(faturas_pendentes or 0),
        "faturas_pagas": float(faturas_pagas or 0),
    }


def dados_categorias(usuario_id, mes):
    conn = conectar()

    despesas = pd.read_sql_query(
        """
        SELECT categoria, valor, 'Despesa' AS tipo
        FROM despesas
        WHERE usuario_id = ? AND mes = ?
        """,
        conn,
        params=(usuario_id, mes)
    )

    compras = pd.read_sql_query(
        """
        SELECT categoria, valor_total AS valor, 'Cartão' AS tipo
        FROM compras_cartao
        WHERE usuario_id = ? AND mes = ?
        """,
        conn,
        params=(usuario_id, mes)
    )

    conn.close()

    return pd.concat([despesas, compras], ignore_index=True)


def dados_fluxo(usuario_id, mes):
    resumo = buscar_resumo(usuario_id, mes)

    return pd.DataFrame({
        "Tipo": [
            "Receitas recebidas",
            "Despesas pagas",
            "Despesas pendentes",
            "Compras no cartão",
            "Faturas pendentes"
        ],
        "Valor": [
            resumo["total_receitas"],
            resumo["total_despesas_pagas"],
            resumo["total_despesas_pendentes"],
            resumo["total_cartao_mes"],
            resumo["faturas_pendentes"]
        ]
    })


def tela_dashboard_profissional(usuario_id, mes, renda_manual=0, investido=0, privacidade=False):
    st.subheader("📈 Dashboard Profissional")

    resumo = buscar_resumo(usuario_id, mes)

    saldo_projetado = (
        resumo["saldo_contas"]
        + resumo["receitas_a_receber"]
        - resumo["total_despesas_pendentes"]
        - resumo["faturas_pendentes"]
    )

    resultado_mes = (
        resumo["total_receitas"]
        - resumo["total_despesas_pagas"]
        - resumo["faturas_pagas"]
        - float(investido or 0)
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏦 Saldo em contas", "R$ *****" if privacidade else fmt_moeda(resumo["saldo_contas"]))
    c2.metric("💵 Receitas recebidas", "R$ *****" if privacidade else fmt_moeda(resumo["total_receitas"]))
    c3.metric("💳 Cartão no mês", "R$ *****" if privacidade else fmt_moeda(resumo["total_cartao_mes"]))
    c4.metric("🧾 Faturas pendentes", "R$ *****" if privacidade else fmt_moeda(resumo["faturas_pendentes"]))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("✅ Despesas pagas", "R$ *****" if privacidade else fmt_moeda(resumo["total_despesas_pagas"]))
    c6.metric("⏳ Despesas pendentes", "R$ *****" if privacidade else fmt_moeda(resumo["total_despesas_pendentes"]))
    c7.metric("📊 Resultado do mês", "R$ *****" if privacidade else fmt_moeda(resultado_mes))
    c8.metric("🔮 Saldo projetado", "R$ *****" if privacidade else fmt_moeda(saldo_projetado))

    if resultado_mes < 0:
        st.error("⚠️ Atenção: seu resultado do mês está negativo.")
    elif resultado_mes == 0:
        st.warning("⚠️ Seu mês está no zero a zero. Cuidado com novas despesas.")
    else:
        st.success("✅ Seu resultado do mês está positivo.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fluxo do mês")
        df_fluxo = dados_fluxo(usuario_id, mes)
        df_fluxo = df_fluxo[df_fluxo["Valor"] > 0]

        if df_fluxo.empty or privacidade:
            st.info("Sem dados suficientes para gerar gráfico ou modo privacidade ativo.")
        else:
            fig = px.bar(df_fluxo, x="Tipo", y="Valor", text_auto=".2s")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                xaxis_title="",
                yaxis_title="Valor"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Gastos por categoria")
        df_cat = dados_categorias(usuario_id, mes)

        if df_cat.empty or privacidade:
            st.info("Sem dados suficientes para gerar gráfico ou modo privacidade ativo.")
        else:
            cat = df_cat.groupby("categoria", as_index=False)["valor"].sum()
            fig2 = px.pie(cat, values="valor", names="categoria", hole=0.45)
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    st.subheader("Resumo inteligente")

    if resumo["faturas_pendentes"] > 0:
        st.warning(f"Você tem {fmt_moeda(resumo['faturas_pendentes'])} em faturas pendentes neste mês.")

    if resumo["total_despesas_pendentes"] > 0:
        st.warning(f"Você tem {fmt_moeda(resumo['total_despesas_pendentes'])} em despesas pendentes.")

    if resumo["receitas_a_receber"] > 0:
        st.info(f"Você ainda tem {fmt_moeda(resumo['receitas_a_receber'])} para receber neste mês.")

    if saldo_projetado < 0:
        st.error("Seu saldo projetado está negativo. Revise despesas, faturas e gastos no cartão.")
    else:
        st.success("Seu saldo projetado está positivo considerando pendências e valores a receber.")
