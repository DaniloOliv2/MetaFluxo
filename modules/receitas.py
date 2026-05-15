import streamlit as st
from utils.database import conectar
from database.supabase_config import supabase


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabela_receitas():
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

    conn.commit()
    conn.close()


def listar_contas(usuario_id):
    response = supabase.table("contas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .order("nome") \
        .execute()

    return response.data


def criar_receita(usuario_id, mes, descricao, categoria, conta_id, valor, recebida=True):

    supabase.table("receitas").insert({
        "usuario_id": usuario_id,
        "mes": mes,
        "descricao": descricao,
        "categoria": categoria,
        "conta_id": conta_id,
        "valor": float(valor),
        "recebida": recebida
    }).execute()

    if recebida and conta_id:

        conta = supabase.table("contas") \
            .select("saldo") \
            .eq("id", conta_id) \
            .single() \
            .execute()

        saldo_atual = float(conta.data["saldo"])

        supabase.table("contas").update({
            "saldo": saldo_atual + float(valor)
        }).eq("id", conta_id).execute()


def listar_receitas(usuario_id, mes):

    response = supabase.table("receitas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .eq("mes", mes) \
        .order("id", desc=True) \
        .execute()

    return response.data


def deletar_receita(usuario_id, receita_id):

    receita = supabase.table("receitas") \
        .select("*") \
        .eq("id", receita_id) \
        .eq("usuario_id", usuario_id) \
        .single() \
        .execute()

    receita_data = receita.data

    if receita_data and receita_data["recebida"] and receita_data["conta_id"]:

        conta = supabase.table("contas") \
            .select("saldo") \
            .eq("id", receita_data["conta_id"]) \
            .single() \
            .execute()

        saldo_atual = float(conta.data["saldo"])

        supabase.table("contas").update({
            "saldo": saldo_atual - float(receita_data["valor"])
        }).eq("id", receita_data["conta_id"]).execute()

    supabase.table("receitas") \
        .delete() \
        .eq("id", receita_id) \
        .execute()


def tela_receitas(usuario_id, mes):
    garantir_tabela_receitas()
# garantir_tabela_receitas()
    st.subheader("💵 Receitas")

    categorias = [
        "💼 Salário",
        "💰 Renda extra",
        "📲 PIX recebido",
        "🛒 Venda",
        "🎁 Presente",
        "💸 Reembolso",
        "📈 Rendimentos",
        "🛠️ Outros"
    ]

    contas = listar_contas(usuario_id)

    if not contas:
        st.warning("Antes de cadastrar receitas, crie pelo menos uma conta na aba 🏦 Contas.")
        return

    contas_opcoes = {f"{conta['nome']} — {conta['tipo']}": conta["id"] for conta in contas}

    with st.expander("➕ Nova receita", expanded=False):
        with st.form("form_nova_receita", clear_on_submit=True):

            descricao = st.text_input("Descrição", placeholder="Ex: Salário, PIX, venda, renda extra")

            categoria = st.selectbox("Categoria", categorias)

            conta_nome = st.selectbox("Conta de destino", list(contas_opcoes.keys()))

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help="Para trinta mil, digite 30000. O sistema exibirá como R$ 30.000,00."
            )

            recebida = st.checkbox("Já recebi esse valor?", value=True)

            enviar = st.form_submit_button("Cadastrar receita", use_container_width=True)

            if enviar:
                if not descricao.strip():
                    st.warning("Informe a descrição da receita.")
                elif valor <= 0:
                    st.warning("Informe um valor maior que zero.")
                else:
                    criar_receita(
                        usuario_id,
                        mes,
                        descricao.strip(),
                        categoria,
                        contas_opcoes[conta_nome],
                        valor,
                        recebida
                    )
                    st.success("Receita cadastrada com sucesso!")
                    st.rerun()

    receitas = listar_receitas(usuario_id, mes)

    total_recebido = sum(float(r["valor"]) for r in receitas if r["recebida"])
    total_a_receber = sum(float(r["valor"]) for r in receitas if not r["recebida"])

    c1, c2 = st.columns(2)
    c1.metric("✅ Recebido", fmt_moeda(total_recebido))
    c2.metric("⏳ A receber", fmt_moeda(total_a_receber))

    st.divider()

    if not receitas:
        st.info("Nenhuma receita cadastrada neste mês.")
        return

    for receita in receitas:
    status = "✅ Recebida" if receita["recebida"] else "⏳ A receber"

    conta_nome = "Sem conta"

    if receita.get("conta_id"):
        conta = supabase.table("contas") \
            .select("nome") \
            .eq("id", receita["conta_id"]) \
            .single() \
            .execute()

        if conta.data:
            conta_nome = conta.data["nome"]

    with st.container(border=True):
        st.markdown(f"### {receita['descricao']}")
            st.write(f"**Categoria:** {receita['categoria']}")
            st.write(f"**Conta:** {conta_nome}")
            st.write(f"**Valor:** {fmt_moeda(receita['valor'])}")
            st.write(f"**Status:** {status}")

            if st.button("🗑️ Excluir receita", key=f"del_receita_{receita['id']}", use_container_width=True):
                deletar_receita(usuario_id, receita["id"])
                st.success("Receita excluída!")
                st.rerun()
