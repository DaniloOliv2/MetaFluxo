import streamlit as st
import re
from decimal import Decimal, InvalidOperation
from database.neon_config import executar_sql, buscar_todos


def interpretar_reais(texto):
    """Aceita 1000, 1000,00 e 1.000,00, sem ambiguidades."""
    texto = str(texto).strip().replace("R$", "").strip()
    if not re.fullmatch(r"-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?", texto):
        raise ValueError("Use o formato brasileiro, por exemplo: 1.000,00")
    try:
        return Decimal(texto.replace(".", "").replace(",", "."))
    except InvalidOperation as erro:
        raise ValueError("Valor inválido.") from erro


def texto_reais(valor):
    return f"{Decimal(str(valor)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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


def deletar_conta(conta_id, usuario_id):
    try:
        executar_sql("""
            DELETE FROM contas
            WHERE id = :conta_id AND usuario_id = :usuario_id
        """, {
            "conta_id": conta_id,
            "usuario_id": usuario_id
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

            saldo_texto = st.text_input(
                "Saldo inicial (R$)",
                value="0,00",
                help="Exemplo: 1.000,00"
            )

            enviar = st.form_submit_button(
                "Criar conta",
                use_container_width=True
            )

            if enviar:
                if not nome.strip():
                    st.warning("Informe o nome da conta.")
                else:
                    try:
                        saldo = interpretar_reais(saldo_texto)
                        criar_conta(usuario_id, nome.strip(), tipo, saldo)
                    except ValueError as erro:
                        st.error(str(erro))
                    else:
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

                    novo_saldo_texto = st.text_input(
                        "Saldo (R$)",
                        value=texto_reais(conta["saldo"]),
                        key=f"saldo_conta_br_{conta['id']}"
                    )

                    chave_confirmacao = f"confirmar_exclusao_conta_{conta['id']}"
                    if st.session_state.get(chave_confirmacao, False):
                        st.warning(
                            f"Tem certeza de que deseja excluir a conta '{conta['nome']}'?"
                        )
                        confirmar, cancelar = st.columns(2)
                        if confirmar.button(
                            "Confirmar exclusão",
                            key=f"confirmar_conta_{conta['id']}",
                            use_container_width=True,
                        ):
                            deletar_conta(conta["id"], usuario_id)
                            st.session_state[chave_confirmacao] = False
                            st.rerun()
                        if cancelar.button(
                            "Cancelar",
                            key=f"cancelar_conta_{conta['id']}",
                            use_container_width=True,
                        ):
                            st.session_state[chave_confirmacao] = False
                            st.rerun()
                    else:
                        c1, c2 = st.columns(2)
                        if c1.button(
                            "Salvar",
                            key=f"salvar_conta_{conta['id']}",
                            use_container_width=True,
                        ):
                            if not novo_nome.strip():
                                st.warning("Informe o nome da conta.")
                            else:
                                try:
                                    novo_saldo = interpretar_reais(novo_saldo_texto)
                                    atualizar_conta(
                                        conta["id"], novo_nome.strip(), novo_tipo, novo_saldo
                                    )
                                except ValueError as erro:
                                    st.error(str(erro))
                                else:
                                    st.success("Conta atualizada!")
                                    st.rerun()
                        if c2.button(
                            "Excluir",
                            key=f"excluir_conta_{conta['id']}",
                            use_container_width=True,
                        ):
                            st.session_state[chave_confirmacao] = True
                            st.rerun()
