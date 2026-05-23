import streamlit as st
import pandas as pd
import plotly.express as px
from database.supabase_config import supabase


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def buscar_resumo(usuario_id, mes):

    saldo_contas = supabase.table("contas") \
        .select("saldo") \
        .eq("usuario_id", usuario_id) \
        .execute()

    saldo_total = sum(float(c["saldo"]) for c in saldo_contas.data)

    receitas = supabase.table("receitas") \
    .select("valor, recebida") \
    .eq("usuario_id", usuario_id) \
    .eq("mes", mes) \
    .execute()

    despesas = supabase.table("despesas") \
    .select("valor, paga") \
    .eq("usuario_id", usuario_id) \
    .eq("mes", mes) \
    .execute()

    compras = supabase.table("compras_cartao") \
    .select("valor_total") \
    .eq("usuario_id", usuario_id) \
    .eq("mes", mes) \
    .execute()

    faturas = supabase.table("faturas") \
    .select("valor, paga") \
    .eq("usuario_id", usuario_id) \
    .eq("mes", mes) \
    .execute()
    total_receitas = sum(
        float(r["valor"])
        for r in receitas.data
        if r["recebida"]
    )

    receitas_a_receber = sum(
        float(r["valor"])
        for r in receitas.data
        if not r["recebida"]
    )

    despesas_pagas = sum(
        float(d["valor"])
        for d in despesas.data
        if d["paga"]
    )

    despesas_pendentes = sum(
        float(d["valor"])
        for d in despesas.data
        if not d["paga"]
    )

    total_cartao = sum(
        float(c["valor_total"])
        for c in compras.data
    )

    faturas_pendentes = sum(
        float(f["valor"])
        for f in faturas.data
        if not f["paga"]
    )

    faturas_pagas = sum(
        float(f["valor"])
        for f in faturas.data
        if f["paga"]
    )

    return {
        "saldo_contas": saldo_total,
        "total_receitas": total_receitas,
        "receitas_a_receber": receitas_a_receber,
        "total_despesas_pagas": despesas_pagas,
        "total_despesas_pendentes": despesas_pendentes,
        "total_cartao_mes": total_cartao,
        "faturas_pendentes": faturas_pendentes,
        "faturas_pagas": faturas_pagas
    }


def dados_categorias(usuario_id, mes):

    despesas_resp = supabase.table("despesas") \
        .select("categoria, valor") \
        .eq("usuario_id", usuario_id) \
        .eq("mes", mes) \
        .execute()

    compras_resp = supabase.table("compras_cartao") \
        .select("categoria, valor_total") \
        .eq("usuario_id", usuario_id) \
        .eq("mes", mes) \
        .execute()

    dados = []

    for item in despesas_resp.data:
        dados.append({
            "categoria": item["categoria"],
            "valor": float(item["valor"]),
            "tipo": "Despesa"
        })

    for item in compras_resp.data:
        dados.append({
            "categoria": item["categoria"],
            "valor": float(item["valor_total"]),
            "tipo": "Cartão"
        })

    return pd.DataFrame(dados)


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
            st.plotly_chart(
                fig,
                use_container_width=True,
               key=f"grafico_fluxo_dashboard_{usuario_id}_{mes}"
            )

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
            
            st.plotly_chart(
                fig2,
                use_container_width=True,
               key=f"grafico_categorias_dashboard_{usuario_id}_{mes}"
           )
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
