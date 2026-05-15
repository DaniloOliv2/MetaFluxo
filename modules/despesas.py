import streamlit as st
from database.supabase_config import supabase


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


def listar_contas(usuario_id):
    response = supabase.table("contas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .order("nome") \
        .execute()

    return response.data


def criar_despesa(usuario_id, mes, descricao, categoria, conta_id, valor, paga, vencimento, recorrente):

    supabase.table("despesas").insert({
        "usuario_id": usuario_id,
        "mes": mes,
        "descricao": descricao,
        "categoria": categoria,
        "conta_id": conta_id,
        "valor": float(valor),
        "paga": paga,
        "vencimento": str(vencimento),
        "recorrente": recorrente
    }).execute()

    if paga and conta_id:

        conta = supabase.table("contas") \
            .select("saldo") \
            .eq("id", conta_id) \
            .single() \
            .execute()

        saldo_atual = float(conta.data["saldo"])

        supabase.table("contas").update({
            "saldo": saldo_atual - float(valor)
        }).eq("id", conta_id).execute()


def listar_despesas(usuario_id, mes):

    response = supabase.table("despesas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .eq("mes", mes) \
        .order("id", desc=True) \
        .execute()

    return response.data


def buscar_nome_conta(conta_id):

    if not conta_id:
        return "Sem conta"

    conta = supabase.table("contas") \
        .select("nome") \
        .eq("id", conta_id) \
        .single() \
        .execute()

    if conta.data:
        return conta.data["nome"]

    return "Sem conta"


def atualizar_status_despesa(usuario_id, despesa_id, novo_status):

    despesa = supabase.table("despesas") \
        .select("*") \
        .eq("id", despesa_id) \
        .eq("usuario_id", usuario_id) \
        .single() \
        .execute()

    despesa = despesa.data

    if not despesa:
        return

    status_atual = despesa["paga"]
    valor = float(despesa["valor"])
    conta_id = despesa["conta_id"]

    if conta_id and status_atual != novo_status:

        conta = supabase.table("contas") \
            .select("saldo") \
            .eq("id", conta_id) \
            .single() \
            .execute()

        saldo_atual = float(conta.data["saldo"])

        if novo_status:
            novo_saldo = saldo_atual - valor
        else:
            novo_saldo = saldo_atual + valor

        supabase.table("contas").update({
            "saldo": novo_saldo
        }).eq("id", conta_id).execute()

    supabase.table("despesas").update({
        "paga": novo_status
    }).eq("id", despesa_id).execute()


def deletar_despesa(usuario_id, despesa_id):

    despesa = supabase.table("despesas") \
        .select("*") \
        .eq("id", despesa_id) \
        .eq("usuario_id", usuario_id) \
        .single() \
        .execute()

    despesa = despesa.data

    if despesa and despesa["paga"] and despesa["conta_id"]:

        conta = supabase.table("contas") \
            .select("saldo") \
            .eq("id", despesa["conta_id"]) \
            .single() \
            .execute()

        saldo_atual = float(conta.data["saldo"])

        supabase.table("contas").update({
            "saldo": saldo_atual + float(despesa["valor"])
        }).eq("id", despesa["conta_id"]).execute()

    supabase.table("despesas") \
        .delete() \
        .eq("id", despesa_id) \
        .execute()


def tela_despesas(usuario_id, mes):

    st.subheader("💳 Despesas")

    categorias = [
        "🏠 Moradia",
        "🍎 Alimentação",
        "🚗 Transporte",
        "🎡 Lazer",
        "💊 Saúde",
        "📚 Estudos",
        "👕 Vestuário",
        "📱 Assinaturas",
        "💳 Cartão",
        "🛠️ Outros"
    ]

    contas = listar_contas(usuario_id)

    if not contas:
        st.warning("Antes de cadastrar despesas, crie pelo menos uma conta.")
        return

    contas_opcoes = {
        f"{conta['nome']} — {conta['tipo']}": conta["id"]
        for conta in contas
    }

    with st.expander("➕ Nova despesa"):

        with st.form("nova_despesa", clear_on_submit=True):

            descricao = st.text_input("Descrição")

            categoria = st.selectbox("Categoria", categorias)

            conta_nome = st.selectbox(
                "Conta",
                list(contas_opcoes.keys())
            )

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

            vencimento = st.date_input("Vencimento")

            paga = st.checkbox("Já foi paga?")

            recorrente = st.checkbox("Despesa recorrente?")

            enviar = st.form_submit_button(
                "Cadastrar despesa",
                use_container_width=True
            )

            if enviar:

                criar_despesa(
                    usuario_id,
                    mes,
                    descricao,
                    categoria,
                    contas_opcoes[conta_nome],
                    valor,
                    paga,
                    vencimento,
                    recorrente
                )

                st.success("Despesa cadastrada!")
                st.rerun()

    despesas = listar_despesas(usuario_id, mes)

    total_pago = sum(float(d["valor"]) for d in despesas if d["paga"])

    total_pendente = sum(float(d["valor"]) for d in despesas if not d["paga"])

    c1, c2 = st.columns(2)

    c1.metric("✅ Pago", fmt_moeda(total_pago))
    c2.metric("⏳ Pendente", fmt_moeda(total_pendente))

    st.divider()

    if not despesas:
        st.info("Nenhuma despesa cadastrada.")
        return

    for despesa in despesas:

        conta_nome = buscar_nome_conta(
            despesa.get("conta_id")
        )

        status = "✅ Paga" if despesa["paga"] else "⏳ Pendente"

        with st.container(border=True):

            st.markdown(f"### {despesa['descricao']}")

            st.write(f"**Categoria:** {despesa['categoria']}")
            st.write(f"**Conta:** {conta_nome}")
            st.write(f"**Valor:** {fmt_moeda(despesa['valor'])}")
            st.write(f"**Vencimento:** {despesa['vencimento']}")
            st.write(f"**Status:** {status}")

            novo_status = st.checkbox(
                "Marcar como paga",
                value=despesa["paga"],
                key=f"status_{despesa['id']}"
            )

            if novo_status != despesa["paga"]:

                atualizar_status_despesa(
                    usuario_id,
                    despesa["id"],
                    novo_status
                )

                st.rerun()

            if st.button(
                "🗑️ Excluir despesa",
                key=f"del_{despesa['id']}",
                use_container_width=True
            ):

                deletar_despesa(
                    usuario_id,
                    despesa["id"]
                )

                st.success("Despesa excluída!")
                st.rerun()
