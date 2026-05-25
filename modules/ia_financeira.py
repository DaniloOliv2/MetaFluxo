import streamlit as st
from database.supabase_config import supabase


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def carregar_dados(usuario_id, mes):
    receitas = supabase.table("receitas").select("*").eq("usuario_id", usuario_id).eq("mes", mes).execute().data
    despesas = supabase.table("despesas").select("*").eq("usuario_id", usuario_id).eq("mes", mes).execute().data
    faturas = supabase.table("faturas").select("*").eq("usuario_id", usuario_id).eq("mes", mes).execute().data
    metas = supabase.table("metas").select("*").eq("usuario_id", usuario_id).execute().data
    investimentos = supabase.table("investimentos").select("*").eq("usuario_id", usuario_id).execute().data

    return receitas, despesas, faturas, metas, investimentos


def gerar_insights(usuario_id, mes, renda_manual=0):
    receitas, despesas, faturas, metas, investimentos = carregar_dados(usuario_id, mes)

    total_receitas = sum(float(r["valor"]) for r in receitas if r.get("recebida"))
    receitas_a_receber = sum(float(r["valor"]) for r in receitas if not r.get("recebida"))

    despesas_pagas = sum(float(d["valor"]) for d in despesas if d.get("paga"))
    despesas_pendentes = sum(float(d["valor"]) for d in despesas if not d.get("paga"))

    faturas_pendentes = sum(float(f["valor"]) for f in faturas if not f.get("paga"))

    total_investido = sum(float(i["valor_atual"]) for i in investimentos)

    total_metas = sum(float(m["valor_meta"]) for m in metas)
    total_guardado = sum(float(m["valor_atual"]) for m in metas)

    saidas = despesas_pagas + despesas_pendentes + faturas_pendentes
    entradas = total_receitas + receitas_a_receber
    saldo_projetado = entradas - saidas

    insights = []

    if saldo_projetado < 0:
        insights.append(("🚨 Risco financeiro", "Seu saldo projetado está negativo. Revise despesas, faturas e gastos no cartão.", "crítico"))
    else:
        insights.append(("✅ Saldo saudável", "Seu saldo projetado está positivo para este mês.", "bom"))

    if entradas > 0:
        percentual_gastos = (saidas / entradas) * 100

        if percentual_gastos > 80:
            insights.append(("⚠️ Gastos elevados", f"Você já comprometeu {percentual_gastos:.1f}% das entradas do mês.", "atenção"))
        elif percentual_gastos < 50:
            insights.append(("💚 Ótimo controle", f"Você comprometeu apenas {percentual_gastos:.1f}% das entradas do mês.", "bom"))

    if faturas_pendentes > 0:
        insights.append(("💳 Faturas pendentes", f"Você possui {fmt_moeda(faturas_pendentes)} em faturas ainda não pagas.", "atenção"))

    if despesas_pendentes > 0:
        insights.append(("⏳ Despesas em aberto", f"Existem {fmt_moeda(despesas_pendentes)} em despesas pendentes.", "atenção"))

    if total_metas > 0:
        progresso_metas = (total_guardado / total_metas) * 100

        insights.append(("🎯 Progresso das metas", f"Você já alcançou {progresso_metas:.1f}% das suas metas financeiras.", "bom"))

    if total_investido > 0:
        insights.append(("📈 Patrimônio investido", f"Seu patrimônio investido atual é de {fmt_moeda(total_investido)}.", "bom"))

    if not insights:
        insights.append(("ℹ️ Sem dados suficientes", "Cadastre receitas, despesas, metas ou investimentos para gerar análises inteligentes.", "neutro"))

    return insights, {
        "entradas": entradas,
        "saidas": saidas,
        "saldo_projetado": saldo_projetado,
        "investimentos": total_investido,
        "metas": total_metas,
        "guardado": total_guardado
    }


def calcular_score(dados):
    score = 100

    if dados["saldo_projetado"] < 0:
        score -= 35

    if dados["entradas"] > 0:
        comprometimento = dados["saidas"] / dados["entradas"]

        if comprometimento > 0.8:
            score -= 25
        elif comprometimento > 0.6:
            score -= 15

    if dados["investimentos"] > 0:
        score += 10

    if dados["metas"] > 0 and dados["guardado"] > 0:
        score += 10

    score = max(0, min(score, 100))

    if score >= 85:
        status = "Excelente"
    elif score >= 70:
        status = "Bom"
    elif score >= 50:
        status = "Atenção"
    else:
        status = "Crítico"

    return score, status


def tela_ia_financeira(usuario_id, mes, renda_manual=0):
    st.subheader("🤖 IA Financeira")

    insights, dados = gerar_insights(usuario_id, mes, renda_manual)
    score, status = calcular_score(dados)

    c1, c2, c3 = st.columns(3)

    c1.metric("🧠 Score financeiro", f"{score}/100")
    c2.metric("📊 Situação", status)
    c3.metric("🔮 Saldo projetado", fmt_moeda(dados["saldo_projetado"]))

    st.progress(score / 100)

    st.divider()

    st.subheader("Insights inteligentes")

    for titulo, mensagem, nivel in insights:
        if nivel == "crítico":
            st.error(f"**{titulo}**\n\n{mensagem}")
        elif nivel == "atenção":
            st.warning(f"**{titulo}**\n\n{mensagem}")
        elif nivel == "bom":
            st.success(f"**{titulo}**\n\n{mensagem}")
        else:
            st.info(f"**{titulo}**\n\n{mensagem}")