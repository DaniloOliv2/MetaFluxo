import streamlit as st
from database.supabase_config import supabase
from datetime import date


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def criar_meta(usuario_id, nome, descricao, valor_meta, valor_atual, prazo, categoria):
    supabase.table("metas").insert({
        "usuario_id": usuario_id,
        "nome": nome,
        "descricao": descricao,
        "valor_meta": float(valor_meta),
        "valor_atual": float(valor_atual),
        "prazo": str(prazo) if prazo else None,
        "categoria": categoria
    }).execute()


def listar_metas(usuario_id):
    response = supabase.table("metas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .order("id", desc=True) \
        .execute()

    return response.data


def atualizar_meta(meta_id, nome, descricao, valor_meta, valor_atual, prazo, categoria):
    supabase.table("metas") \
        .update({
            "nome": nome,
            "descricao": descricao,
            "valor_meta": float(valor_meta),
            "valor_atual": float(valor_atual),
            "prazo": str(prazo) if prazo else None,
            "categoria": categoria
        }) \
        .eq("id", meta_id) \
        .execute()


def deletar_meta(meta_id):
    supabase.table("metas") \
        .delete() \
        .eq("id", meta_id) \
        .execute()


def tela_metas(usuario_id):

    st.subheader("🚀 Meus Sonhos e Metas")

    categorias = [
        "Reserva de emergência",
        "Viagem",
        "Casa",
        "Carro",
        "Moto",
        "Notebook",
        "Celular",
        "Investimentos",
        "Aposentadoria",
        "Outros"
    ]

    with st.expander("➕ Nova meta", expanded=False):

        with st.form("form_meta", clear_on_submit=True):

            nome = st.text_input(
                "Nome da meta",
                placeholder="Ex: Viagem para Europa"
            )

            descricao = st.text_area(
                "Descrição",
                placeholder="Detalhes da meta..."
            )

            categoria = st.selectbox(
                "Categoria",
                categorias
            )

            valor_meta = st.number_input(
                "Valor da meta",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

            valor_atual = st.number_input(
                "Quanto você já possui",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

            prazo = st.date_input(
                "Prazo estimado",
                value=date.today()
            )

            enviar = st.form_submit_button(
                "Criar meta",
                use_container_width=True
            )

            if enviar:

                if not nome.strip():
                    st.warning("Informe o nome da meta.")

                elif valor_meta <= 0:
                    st.warning("Informe um valor válido.")

                else:

                    criar_meta(
                        usuario_id,
                        nome.strip(),
                        descricao.strip(),
                        valor_meta,
                        valor_atual,
                        prazo,
                        categoria
                    )

                    st.success("Meta criada com sucesso!")
                    st.rerun()

    metas = listar_metas(usuario_id)

    if not metas:
        st.info("Nenhuma meta cadastrada ainda.")
        return

    total_metas = sum(float(m["valor_meta"]) for m in metas)
    total_guardado = sum(float(m["valor_atual"]) for m in metas)

    progresso_total = (
        total_guardado / total_metas * 100
        if total_metas > 0
        else 0
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "🎯 Total das metas",
        fmt_moeda(total_metas)
    )

    c2.metric(
        "💰 Total guardado",
        fmt_moeda(total_guardado)
    )

    c3.metric(
        "📈 Progresso geral",
        f"{progresso_total:.1f}%"
    )

    st.divider()

    for meta in metas:

        valor_meta = float(meta["valor_meta"])
        valor_atual = float(meta["valor_atual"])

        progresso = (
            valor_atual / valor_meta
            if valor_meta > 0
            else 0
        )

        faltam = valor_meta - valor_atual

        with st.container(border=True):

            st.markdown(f"## 🚀 {meta['nome']}")

            st.write(f"**Categoria:** {meta['categoria']}")

            if meta["descricao"]:
                st.write(meta["descricao"])

            st.progress(
                min(progresso, 1.0)
            )

            st.write(
                f"**{progresso * 100:.1f}% concluído**"
            )

            st.write(
                f"💰 Guardado: {fmt_moeda(valor_atual)}"
            )

            st.write(
                f"🎯 Meta: {fmt_moeda(valor_meta)}"
            )

            st.write(
                f"📌 Faltam: {fmt_moeda(faltam)}"
            )

            if meta["prazo"]:
                st.write(f"📅 Prazo: {meta['prazo']}")

            if progresso >= 1:
                st.success("🎉 Meta concluída!")

            with st.expander("✏️ Editar / Excluir"):

                novo_nome = st.text_input(
                    "Nome",
                    value=meta["nome"],
                    key=f"nome_meta_{meta['id']}"
                )

                nova_descricao = st.text_area(
                    "Descrição",
                    value=meta["descricao"] or "",
                    key=f"desc_meta_{meta['id']}"
                )

                nova_categoria = st.selectbox(
                    "Categoria",
                    categorias,
                    index=categorias.index(meta["categoria"])
                    if meta["categoria"] in categorias else 0,
                    key=f"cat_meta_{meta['id']}"
                )

                novo_valor_meta = st.number_input(
                    "Valor da meta",
                    min_value=0.0,
                    value=float(meta["valor_meta"]),
                    step=100.0,
                    format="%.2f",
                    key=f"meta_valor_{meta['id']}"
                )

                novo_valor_atual = st.number_input(
                    "Valor atual",
                    min_value=0.0,
                    value=float(meta["valor_atual"]),
                    step=100.0,
                    format="%.2f",
                    key=f"meta_atual_{meta['id']}"
                )

                novo_prazo = st.date_input(
                    "Prazo",
                    value=date.fromisoformat(meta["prazo"])
                    if meta["prazo"] else date.today(),
                    key=f"prazo_meta_{meta['id']}"
                )

                b1, b2 = st.columns(2)

                if b1.button(
                    "Salvar",
                    key=f"salvar_meta_{meta['id']}",
                    use_container_width=True
                ):

                    atualizar_meta(
                        meta["id"],
                        novo_nome.strip(),
                        nova_descricao.strip(),
                        novo_valor_meta,
                        novo_valor_atual,
                        novo_prazo,
                        nova_categoria
                    )

                    st.success("Meta atualizada!")
                    st.rerun()

                if b2.button(
                    "Excluir",
                    key=f"excluir_meta_{meta['id']}",
                    use_container_width=True
                ):

                    deletar_meta(meta["id"])

                    st.success("Meta excluída!")

                    st.rerun()