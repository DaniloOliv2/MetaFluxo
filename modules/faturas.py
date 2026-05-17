import streamlit as st
from database.supabase_config import supabase


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def listar_cartoes(usuario_id):

    response = supabase.table("cartoes") \
        .select("*, contas(nome, saldo)") \
        .eq("usuario_id", usuario_id) \
        .eq("ativo", True) \
        .order("nome") \
        .execute()

    cartoes = response.data

    for cartao in cartoes:
        conta = cartao.get("contas")

        cartao["conta_nome"] = conta["nome"] if conta else None
        cartao["conta_saldo"] = conta["saldo"] if conta else 0

    return cartoes


def total_compras_cartao_mes(usuario_id, cartao_id, mes):

    response = supabase.table("compras_cartao") \
        .select("valor_total") \
        .eq("usuario_id", usuario_id) \
        .eq("cartao_id", cartao_id) \
        .eq("mes", mes) \
        .execute()

    total = sum(float(item["valor_total"]) for item in response.data)

    return total


def buscar_fatura(usuario_id, cartao_id, mes):

    response = supabase.table("faturas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .eq("cartao_id", cartao_id) \
        .eq("mes", mes) \
        .limit(1) \
        .execute()

    if response.data:
        return response.data[0]

    return None


def gerar_ou_atualizar_fatura(usuario_id, cartao_id, mes, valor):

    fatura = buscar_fatura(usuario_id, cartao_id, mes)

    if fatura:

        if not fatura["paga"]:

            supabase.table("faturas") \
                .update({
                    "valor": float(valor)
                }) \
                .eq("id", fatura["id"]) \
                .execute()

    else:

        supabase.table("faturas") \
            .insert({
                "usuario_id": usuario_id,
                "cartao_id": cartao_id,
                "mes": mes,
                "valor": float(valor),
                "paga": False
            }) \
            .execute()


def pagar_fatura(usuario_id, cartao_id, mes):

    fatura = buscar_fatura(usuario_id, cartao_id, mes)

    if not fatura:
        return False, "Fatura não encontrada."

    if fatura["paga"]:
        return False, "Essa fatura já está paga."

    response = supabase.table("cartoes") \
        .select("*, contas(*)") \
        .eq("id", cartao_id) \
        .eq("usuario_id", usuario_id) \
        .limit(1) \
        .execute()

    if not response.data:
        return False, "Cartão não encontrado."

    cartao = response.data[0]

    conta = cartao.get("contas")

    if not conta:
        return False, "Cartão sem conta vinculada."

    valor = float(fatura["valor"])
    saldo = float(conta["saldo"])

    if saldo < valor:
        return False, "Saldo insuficiente."

    novo_saldo = saldo - valor

    supabase.table("contas") \
        .update({
            "saldo": novo_saldo
        }) \
        .eq("id", conta["id"]) \
        .execute()

    supabase.table("faturas") \
        .update({
            "paga": True
        }) \
        .eq("id", fatura["id"]) \
        .execute()

    return True, "Fatura paga com sucesso!"

   def reabrir_fatura(usuario_id, cartao_id, mes):

    fatura = buscar_fatura(usuario_id, cartao_id, mes)

    if not fatura or not fatura["paga"]:
        return False, "Não foi possível reabrir."

    response = supabase.table("cartoes") \
        .select("*, contas(*)") \
        .eq("id", cartao_id) \
        .eq("usuario_id", usuario_id) \
        .limit(1) \
        .execute()

    if not response.data:
        return False, "Cartão não encontrado."

    cartao = response.data[0]

    conta = cartao.get("contas")

    if not conta:
        return False, "Conta não encontrada."

    novo_saldo = float(conta["saldo"]) + float(fatura["valor"])

    supabase.table("contas") \
        .update({
            "saldo": novo_saldo
        }) \
        .eq("id", conta["id"]) \
        .execute()

    supabase.table("faturas") \
        .update({
            "paga": False
        }) \
        .eq("id", fatura["id"]) \
        .execute()

    return True, "Fatura reaberta!"


def listar_compras_fatura(usuario_id, cartao_id, mes):

    response = supabase.table("compras_cartao") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .eq("cartao_id", cartao_id) \
        .eq("mes", mes) \
        .order("id", desc=True) \
        .execute()

    return response.data


def tela_faturas(usuario_id, mes):

    st.subheader("🧾 Faturas do Cartão")

    cartoes = listar_cartoes(usuario_id)

    if not cartoes:
        st.warning("Antes de gerar faturas, cadastre um cartão na aba 💳 Cartões.")
        return

    total_geral = 0

    for cartao in cartoes:
        total_mes = total_compras_cartao_mes(usuario_id, cartao["id"], mes)
        gerar_ou_atualizar_fatura(usuario_id, cartao["id"], mes, total_mes)
        fatura = buscar_fatura(usuario_id, cartao["id"], mes)

        total_geral += total_mes

        status = "✅ Paga" if fatura and fatura["paga"] else "⏳ Pendente"

        with st.container(border=True):
            st.markdown(f"### 💳 {cartao['nome']}")
            st.write(f"**Mês:** {mes}")
            st.write(f"**Conta vinculada:** {cartao['conta_nome'] or 'Não vinculada'}")
            st.write(f"**Saldo da conta:** {fmt_moeda(cartao['conta_saldo'] or 0)}")
            st.write(f"**Valor da fatura:** {fmt_moeda(total_mes)}")
            st.write(f"**Status:** {status}")
            st.caption(f"Fecha dia {cartao['fechamento']} | Vence dia {cartao['vencimento']}")

            compras = listar_compras_fatura(usuario_id, cartao["id"], mes)

            with st.expander("Ver compras da fatura"):
                if not compras:
                    st.info("Nenhuma compra nesse cartão neste mês.")
                else:
                    for compra in compras:
                        parcelas = int(compra["parcelas"])
                        valor_parcela = float(compra["valor_total"]) / parcelas if parcelas > 0 else float(compra["valor_total"])
                        st.markdown(f"**{compra['descricao']}**")
                        st.write(f"Categoria: {compra['categoria']}")
                        st.write(f"Valor total: {fmt_moeda(compra['valor_total'])}")
                        st.write(f"Parcelas: {parcelas}x de {fmt_moeda(valor_parcela)}")
                        st.divider()

            col1, col2 = st.columns(2)

            if fatura and not fatura["paga"]:
                if col1.button("💰 Pagar fatura", key=f"pagar_fatura_{cartao['id']}", use_container_width=True):
                    ok, msg = pagar_fatura(usuario_id, cartao["id"], mes)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()

            if fatura and fatura["paga"]:
                if col2.button("↩️ Reabrir fatura", key=f"reabrir_fatura_{cartao['id']}", use_container_width=True):
                    ok, msg = reabrir_fatura(usuario_id, cartao["id"], mes)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()

    st.divider()
    st.metric("Total geral de faturas no mês", fmt_moeda(total_geral))
