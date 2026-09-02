import streamlit as st
from database.neon_config import executar_sql, buscar_todos


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabela_investimentos():
    executar_sql("""
        CREATE TABLE IF NOT EXISTS investimentos (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            instituicao TEXT,
            valor_inicial NUMERIC(15,2) NOT NULL DEFAULT 0,
            valor_atual NUMERIC(15,2) NOT NULL DEFAULT 0,
            rendimento NUMERIC(15,2) NOT NULL DEFAULT 0,
            data_investimento DATE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)


def criar_investimento(usuario_id, nome, categoria, instituicao, valor_inicial, valor_atual, rendimento, data_investimento):
    executar_sql("""
        INSERT INTO investimentos (
            usuario_id, nome, categoria, instituicao,
            valor_inicial, valor_atual, rendimento, data_investimento
        )
        VALUES (
            :usuario_id, :nome, :categoria, :instituicao,
            :valor_inicial, :valor_atual, :rendimento, :data_investimento
        )
    """, {
        "usuario_id": usuario_id,
        "nome": nome,
        "categoria": categoria,
        "instituicao": instituicao,
        "valor_inicial": float(valor_inicial),
        "valor_atual": float(valor_atual),
        "rendimento": float(rendimento),
        "data_investimento": data_investimento
    })


def listar_investimentos(usuario_id):
    return buscar_todos("""
        SELECT *
        FROM investimentos
        WHERE usuario_id = :usuario_id
        ORDER BY id DESC
    """, {
        "usuario_id": usuario_id
    })


def atualizar_investimento(investimento_id, nome, categoria, instituicao, valor_inicial, valor_atual, rendimento):
    executar_sql("""
        UPDATE investimentos
        SET nome = :nome,
            categoria = :categoria,
            instituicao = :instituicao,
            valor_inicial = :valor_inicial,
            valor_atual = :valor_atual,
            rendimento = :rendimento
        WHERE id = :investimento_id
    """, {
        "nome": nome,
        "categoria": categoria,
        "instituicao": instituicao,
        "valor_inicial": float(valor_inicial),
        "valor_atual": float(valor_atual),
        "rendimento": float(rendimento),
        "investimento_id": investimento_id
    })


def deletar_investimento(investimento_id):
    executar_sql("""
        DELETE FROM investimentos
        WHERE id = :investimento_id
    """, {
        "investimento_id": investimento_id
    })


def tela_investimentos(usuario_id):
    garantir_tabela_investimentos()

    st.subheader("💹 Investimentos")

    categorias = [
        "Tesouro Direto",
        "CDB",
        "LCI/LCA",
        "Fundos",
        "Ações",
        "FIIs",
        "Criptomoedas",
        "Poupança",
        "Reserva de emergência",
        "Outros"
    ]

    with st.expander("➕ Novo investimento", expanded=False):
        with st.form("form_novo_investimento", clear_on_submit=True):
            nome = st.text_input("Nome do investimento", placeholder="Ex: CDB Nubank, Tesouro Selic")
            categoria = st.selectbox("Categoria", categorias)
            instituicao = st.text_input("Instituição", placeholder="Ex: Nubank, XP, Inter")

            valor_inicial = st.number_input(
                "Valor aplicado",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

            valor_atual = st.number_input(
                "Valor atual",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

            rendimento = valor_atual - valor_inicial
            data_investimento = st.date_input("Data do investimento")

            enviar = st.form_submit_button("Cadastrar investimento", use_container_width=True)

            if enviar:
                if not nome.strip():
                    st.warning("Informe o nome do investimento.")
                elif valor_inicial <= 0:
                    st.warning("Informe um valor aplicado maior que zero.")
                else:
                    criar_investimento(
                        usuario_id,
                        nome.strip(),
                        categoria,
                        instituicao.strip(),
                        valor_inicial,
                        valor_atual,
                        rendimento,
                        data_investimento
                    )
                    st.success("Investimento cadastrado com sucesso!")
                    st.rerun()

    investimentos = listar_investimentos(usuario_id)

    if not investimentos:
        st.info("Nenhum investimento cadastrado ainda.")
        return

    total_aplicado = sum(float(i["valor_inicial"]) for i in investimentos)
    total_atual = sum(float(i["valor_atual"]) for i in investimentos)
    total_rendimento = total_atual - total_aplicado
    rentabilidade = (total_rendimento / total_aplicado * 100) if total_aplicado > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total aplicado", fmt_moeda(total_aplicado))
    c2.metric("📈 Valor atual", fmt_moeda(total_atual))
    c3.metric("🟢 Rendimento", fmt_moeda(total_rendimento))
    c4.metric("📊 Rentabilidade", f"{rentabilidade:.2f}%")

    st.divider()

    for investimento in investimentos:
        rendimento_item = float(investimento["valor_atual"]) - float(investimento["valor_inicial"])
        rentabilidade_item = (
            rendimento_item / float(investimento["valor_inicial"]) * 100
            if float(investimento["valor_inicial"]) > 0 else 0
        )

        with st.container(border=True):
            st.markdown(f"### 💹 {investimento['nome']}")
            st.write(f"**Categoria:** {investimento['categoria']}")
            st.write(f"**Instituição:** {investimento['instituicao'] or 'Não informada'}")
            st.write(f"**Valor aplicado:** {fmt_moeda(investimento['valor_inicial'])}")
            st.write(f"**Valor atual:** {fmt_moeda(investimento['valor_atual'])}")
            st.write(f"**Rendimento:** {fmt_moeda(rendimento_item)}")
            st.write(f"**Rentabilidade:** {rentabilidade_item:.2f}%")
            st.write(f"**Data:** {investimento['data_investimento']}")

            with st.expander("✏️ Editar / Excluir"):
                novo_nome = st.text_input(
                    "Nome",
                    value=investimento["nome"],
                    key=f"nome_inv_{investimento['id']}"
                )

                nova_categoria = st.selectbox(
                    "Categoria",
                    categorias,
                    index=categorias.index(investimento["categoria"])
                    if investimento["categoria"] in categorias else 0,
                    key=f"cat_inv_{investimento['id']}"
                )

                nova_instituicao = st.text_input(
                    "Instituição",
                    value=investimento["instituicao"] or "",
                    key=f"inst_inv_{investimento['id']}"
                )

                novo_valor_inicial = st.number_input(
                    "Valor aplicado",
                    min_value=0.0,
                    value=float(investimento["valor_inicial"]),
                    step=100.0,
                    format="%.2f",
                    key=f"valor_ini_inv_{investimento['id']}"
                )

                novo_valor_atual = st.number_input(
                    "Valor atual",
                    min_value=0.0,
                    value=float(investimento["valor_atual"]),
                    step=100.0,
                    format="%.2f",
                    key=f"valor_atual_inv_{investimento['id']}"
                )

                novo_rendimento = novo_valor_atual - novo_valor_inicial

                b1, b2 = st.columns(2)

                if b1.button(
                    "Salvar",
                    key=f"salvar_inv_{investimento['id']}",
                    use_container_width=True
                ):
                    atualizar_investimento(
                        investimento["id"],
                        novo_nome.strip(),
                        nova_categoria,
                        nova_instituicao.strip(),
                        novo_valor_inicial,
                        novo_valor_atual,
                        novo_rendimento
                    )
                    st.success("Investimento atualizado!")
                    st.rerun()

                if b2.button(
                    "Excluir",
                    key=f"excluir_inv_{investimento['id']}",
                    use_container_width=True
                ):
                    deletar_investimento(investimento["id"])
                    st.success("Investimento excluído!")
                    st.rerun()
