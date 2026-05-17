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
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO faturas (usuario_id, cartao_id, mes, valor, paga)
        VALUES (?, ?, ?, ?, 0)
        ON CONFLICT(usuario_id, cartao_id, mes)
        DO UPDATE SET valor = excluded.valor
        WHERE faturas.paga = 0
    """, (usuario_id, cartao_id, mes, float(valor)))

    conn.commit()
    conn.close()


def pagar_fatura(usuario_id, cartao_id, mes):
    conn = conectar()
    cursor = conn.cursor()

    fatura = cursor.execute("""
        SELECT *
        FROM faturas
        WHERE usuario_id = ? AND cartao_id = ? AND mes = ?
    """, (usuario_id, cartao_id, mes)).fetchone()

    cartao = cursor.execute("""
        SELECT *
        FROM cartoes
        WHERE id = ? AND usuario_id = ?
    """, (cartao_id, usuario_id)).fetchone()

    if not fatura or not cartao:
        conn.close()
        return False, "Fatura ou cartão não encontrado."

    if fatura["paga"]:
        conn.close()
        return False, "Essa fatura já está paga."

    conta_id = cartao["conta_id"]

    if not conta_id:
        conn.close()
        return False, "Cartão sem conta vinculada para pagamento."

    conta = cursor.execute("""
        SELECT *
        FROM contas
        WHERE id = ? AND usuario_id = ?
    """, (conta_id, usuario_id)).fetchone()

    if not conta:
        conn.close()
        return False, "Conta vinculada não encontrada."

    valor = float(fatura["valor"])
    saldo = float(conta["saldo"])

    if saldo < valor:
        conn.close()
        return False, "Saldo insuficiente na conta vinculada."

    cursor.execute("""
        UPDATE contas
        SET saldo = saldo - ?
        WHERE id = ? AND usuario_id = ?
    """, (valor, conta_id, usuario_id))

    cursor.execute("""
        UPDATE faturas
        SET paga = 1, data_pagamento = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (fatura["id"],))

    conn.commit()
    conn.close()

    return True, "Fatura paga com sucesso!"


def reabrir_fatura(usuario_id, cartao_id, mes):
    conn = conectar()
    cursor = conn.cursor()

    fatura = cursor.execute("""
        SELECT *
        FROM faturas
        WHERE usuario_id = ? AND cartao_id = ? AND mes = ?
    """, (usuario_id, cartao_id, mes)).fetchone()

    cartao = cursor.execute("""
        SELECT *
        FROM cartoes
        WHERE id = ? AND usuario_id = ?
    """, (cartao_id, usuario_id)).fetchone()

    if not fatura or not cartao or not fatura["paga"]:
        conn.close()
        return False, "Não foi possível reabrir a fatura."

    conta_id = cartao["conta_id"]

    cursor.execute("""
        UPDATE contas
        SET saldo = saldo + ?
        WHERE id = ? AND usuario_id = ?
    """, (float(fatura["valor"]), conta_id, usuario_id))

    cursor.execute("""
        UPDATE faturas
        SET paga = 0, data_pagamento = NULL
        WHERE id = ?
    """, (fatura["id"],))

    conn.commit()
    conn.close()

    return True, "Fatura reaberta e valor devolvido para a conta."


def listar_compras_fatura(usuario_id, cartao_id, mes):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM compras_cartao
        WHERE usuario_id = ? AND cartao_id = ? AND mes = ?
        ORDER BY id DESC
    """, (usuario_id, cartao_id, mes))

    compras = cursor.fetchall()
    conn.close()
    return compras


def tela_faturas(usuario_id, mes):
    garantir_tabela_faturas()

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
