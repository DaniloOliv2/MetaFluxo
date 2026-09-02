import streamlit as st
from database.neon_config import executar_sql, buscar_todos


def fmt_moeda(valor):
    """Formata valor no padrão brasileiro."""
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabela_contas():
    executar_sql("""
        CREATE TABLE IF NOT EXISTS contas (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            saldo NUMERIC(15,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)


def criar_conta(usuario_id, nome, tipo, saldo):
    executar_sql("""
        INSERT INTO contas (
            usuario_id,
            nome,
            tipo,
            saldo
        )
        VALUES (
            :usuario_id,
            :nome,
            :tipo,
            :saldo
        )
    """, {
        "usuario_id": usuario_id,
        "nome": nome,
        "tipo": tipo,
        "saldo": float(saldo)
    })


def listar_contas(usuario_id):
    return buscar_todos("""
        SELECT id, usuario_id, nome, tipo, saldo
        FROM contas
        WHERE usuario_id = :usuario_id
        ORDER BY id DESC
    """, {
        "usuario_id": usuario_id
    })


def atualizar_conta(conta_id, nome, tipo, saldo):
    executar_sql("""
        UPDATE contas
        SET nome = :nome,
            tipo = :tipo,
            saldo = :saldo
        WHERE id = :conta_id
    """, {
        "conta_id": conta_id,
        "nome": nome,
        "tipo": tipo,
        "saldo": float(saldo)
    })


def deletar_conta(conta_id):
    try:
        executar_sql("""
            DELETE FROM contas
            WHERE id = :conta_id
        """, {
            "conta_id": conta_id
        })

        st.success("✅ Conta excluída com sucesso!")

    except Exception:
        st.error(
            "❌ Esta conta está vinculada a cartões, receitas ou despesas.\n\n"
            "Exclua os vínculos primeiro."
        )


def tela_contas(usuario_id):
    garantir_tabela_contas()

    st.subheader("🏦 Contas Financeiras")

    tipos_conta = [
        "Conta corrente",
        "Carteira",
        "Poupança",
        "Investimento",
        "Dinheiro",
        "Conta digital",
        "Reserva de emergência"
    ]

    with st.expander("➕ Nova conta", expanded=False):
        with st.form("form_nova_conta", clear_on_submit=True):
            nome = st.text_input(
                "Nome da conta",
                placeholder="Ex: Nubank, Santander, Carteira"
            )

            tipo = st.selectbox("Tipo", tipos_conta)

            saldo = st.number_input(
                "Saldo inicial",
                step=100.0,
                format="%.2f",
                help="Para trinta mil, digite 30000."
            )

            enviar = st.form_submit_button(
                "Criar conta",
                use_container_width=True
            )

            if enviar:
                if not nome.strip():
                    st.warning("Informe o nome da conta.")
                else:
                    criar_conta(
                        usuario_id,
                        nome.strip(),
                        tipo,
                        saldo
                    )

                    st.success("Conta criada com sucesso!")
                    st.rerun()

    contas = listar_contas(usuario_id)

    if not contas:
        st.info("Nenhuma conta cadastrada ainda.")
        return

    saldo_total = sum(float(conta["saldo"]) for conta in contas)

    st.metric("💰 Saldo total em contas", fmt_moeda(saldo_total))
    st.divider()

    cols = st.columns(3)

    for i, conta in enumerate(contas):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### 💳 {conta['nome']}")
                st.write(f"**Tipo:** {conta['tipo']}")
                st.write(f"**Saldo:** {fmt_moeda(conta['saldo'])}")

                with st.expander("✏️ Editar / Excluir"):
                    novo_nome = st.text_input(
                        "Nome",
                        value=conta["nome"],
                        key=f"nome_conta_{conta['id']}"
                    )

                    novo_tipo = st.selectbox(
                        "Tipo",
                        tipos_conta,
                        index=tipos_conta.index(conta["tipo"])
                        if conta["tipo"] in tipos_conta else 0,
                        key=f"tipo_conta_{conta['id']}"
                    )

                    novo_saldo = st.number_input(
                        "Saldo",
                        value=float(conta["saldo"]),
                        step=100.0,
                        format="%.2f",
                        key=f"saldo_conta_{conta['id']}"
                    )

                    c1, c2 = st.columns(2)

                    if c1.button(
                        "Salvar",
                        key=f"salvar_conta_{conta['id']}",
                        use_container_width=True
                    ):
                        if not novo_nome.strip():
                            st.warning("Informe o nome da conta.")
                        else:
                            atualizar_conta(
                                conta["id"],
                                novo_nome.strip(),
                                novo_tipo,
                                novo_saldo
                            )
                            st.success("Conta atualizada!")
                            st.rerun()

                    if c2.button(
                        "Excluir",
                        key=f"excluir_conta_{conta['id']}",
                        use_container_width=True
                    ):
                        deletar_conta(conta["id"])
                        st.rerun()
