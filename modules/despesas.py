import streamlit as st
from database.neon_config import executar_sql, buscar_todos, buscar_um


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabela_despesas():
    executar_sql("""
        CREATE TABLE IF NOT EXISTS despesas (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            conta_id BIGINT,
            valor NUMERIC(15,2) NOT NULL DEFAULT 0,
            paga BOOLEAN NOT NULL DEFAULT FALSE,
            vencimento DATE,
            recorrente BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT fk_despesas_conta
                FOREIGN KEY (conta_id)
                REFERENCES contas(id)
                ON DELETE SET NULL
        )
    """)


def listar_contas(usuario_id):
    return buscar_todos("""
        SELECT id, usuario_id, nome, tipo, saldo
        FROM contas
        WHERE usuario_id = :usuario_id
        ORDER BY nome
    """, {
        "usuario_id": usuario_id
    })


def criar_despesa(
    usuario_id,
    mes,
    descricao,
    categoria,
    conta_id,
    valor,
    paga,
    vencimento,
    recorrente
):
    executar_sql("""
        INSERT INTO despesas (
            usuario_id,
            mes,
            descricao,
            categoria,
            conta_id,
            valor,
            paga,
            vencimento,
            recorrente
        )
        VALUES (
            :usuario_id,
            :mes,
            :descricao,
            :categoria,
            :conta_id,
            :valor,
            :paga,
            :vencimento,
            :recorrente
        )
    """, {
        "usuario_id": usuario_id,
        "mes": mes,
        "descricao": descricao,
        "categoria": categoria,
        "conta_id": conta_id,
        "valor": float(valor),
        "paga": bool(paga),
        "vencimento": vencimento,
        "recorrente": bool(recorrente)
    })

    # Se a despesa já foi cadastrada como paga,
    # desconta o valor da conta.
    if paga and conta_id:
        executar_sql("""
            UPDATE contas
            SET saldo = saldo - :valor
            WHERE id = :conta_id
              AND usuario_id = :usuario_id
        """, {
            "valor": float(valor),
            "conta_id": conta_id,
            "usuario_id": usuario_id
        })


def listar_despesas(usuario_id, mes):
    return buscar_todos("""
        SELECT
            d.id,
            d.usuario_id,
            d.mes,
            d.descricao,
            d.categoria,
            d.conta_id,
            d.valor,
            d.paga,
            d.vencimento,
            d.recorrente,
            d.created_at,
            c.nome AS conta_nome
        FROM despesas d
        LEFT JOIN contas c
            ON c.id = d.conta_id
        WHERE d.usuario_id = :usuario_id
          AND d.mes = :mes
        ORDER BY d.id DESC
    """, {
        "usuario_id": usuario_id,
        "mes": mes
    })


def atualizar_status_despesa(usuario_id, despesa_id, novo_status):
    despesa = buscar_um("""
        SELECT id, usuario_id, conta_id, valor, paga
        FROM despesas
        WHERE id = :despesa_id
          AND usuario_id = :usuario_id
    """, {
        "despesa_id": despesa_id,
        "usuario_id": usuario_id
    })

    if not despesa:
        return

    status_atual = bool(despesa["paga"])
    novo_status = bool(novo_status)

    # Não faz nada se o status não mudou.
    if status_atual == novo_status:
        return

    valor = float(despesa["valor"])
    conta_id = despesa["conta_id"]

    # Se passou de pendente para paga:
    # desconta da conta.
    if conta_id and novo_status:
        executar_sql("""
            UPDATE contas
            SET saldo = saldo - :valor
            WHERE id = :conta_id
              AND usuario_id = :usuario_id
        """, {
            "valor": valor,
            "conta_id": conta_id,
            "usuario_id": usuario_id
        })

    # Se passou de paga para pendente:
    # devolve o valor para a conta.
    elif conta_id and not novo_status:
        executar_sql("""
            UPDATE contas
            SET saldo = saldo + :valor
            WHERE id = :conta_id
              AND usuario_id = :usuario_id
        """, {
            "valor": valor,
            "conta_id": conta_id,
            "usuario_id": usuario_id
        })

    executar_sql("""
        UPDATE despesas
        SET paga = :paga
        WHERE id = :despesa_id
          AND usuario_id = :usuario_id
    """, {
        "paga": novo_status,
        "despesa_id": despesa_id,
        "usuario_id": usuario_id
    })


def deletar_despesa(usuario_id, despesa_id):
    despesa = buscar_um("""
        SELECT id, usuario_id, conta_id, valor, paga
        FROM despesas
        WHERE id = :despesa_id
          AND usuario_id = :usuario_id
    """, {
        "despesa_id": despesa_id,
        "usuario_id": usuario_id
    })

    if not despesa:
        return

    # Se a despesa estava paga, o dinheiro havia sido
    # descontado da conta. Ao excluir, devolvemos o valor.
    if despesa["paga"] and despesa["conta_id"]:
        executar_sql("""
            UPDATE contas
            SET saldo = saldo + :valor
            WHERE id = :conta_id
              AND usuario_id = :usuario_id
        """, {
            "valor": float(despesa["valor"]),
            "conta_id": despesa["conta_id"],
            "usuario_id": usuario_id
        })

    executar_sql("""
        DELETE FROM despesas
        WHERE id = :despesa_id
          AND usuario_id = :usuario_id
    """, {
        "despesa_id": despesa_id,
        "usuario_id": usuario_id
    })


def tela_despesas(usuario_id, mes):
    garantir_tabela_despesas()

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
        st.warning(
            "Antes de cadastrar despesas, crie pelo menos uma conta."
        )
        return

    contas_opcoes = {
        f"{conta['nome']} — {conta['tipo']}": conta["id"]
        for conta in contas
    }

    # =====================================================
    # NOVA DESPESA
    # =====================================================

    with st.expander("➕ Nova despesa", expanded=False):
        with st.form(
            "form_nova_despesa",
            clear_on_submit=True
        ):
            descricao = st.text_input(
                "Descrição",
                placeholder="Ex: Aluguel, supermercado, combustível"
            )

            categoria = st.selectbox(
                "Categoria",
                categorias
            )

            conta_nome = st.selectbox(
                "Conta",
                list(contas_opcoes.keys())
            )

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=10.0,
                format="%.2f",
                help="Exemplo: para R$ 150,00 digite 150."
            )

            vencimento = st.date_input(
                "Vencimento"
            )

            paga = st.checkbox(
                "Já foi paga?"
            )

            recorrente = st.checkbox(
                "Despesa recorrente?"
            )

            enviar = st.form_submit_button(
                "Cadastrar despesa",
                use_container_width=True
            )

            if enviar:
                if not descricao.strip():
                    st.warning(
                        "Informe a descrição da despesa."
                    )

                elif valor <= 0:
                    st.warning(
                        "Informe um valor maior que zero."
                    )

                else:
                    criar_despesa(
                        usuario_id=usuario_id,
                        mes=mes,
                        descricao=descricao.strip(),
                        categoria=categoria,
                        conta_id=contas_opcoes[conta_nome],
                        valor=valor,
                        paga=paga,
                        vencimento=vencimento,
                        recorrente=recorrente
                    )

                    st.success(
                        "Despesa cadastrada com sucesso!"
                    )

                    st.rerun()

    # =====================================================
    # LISTAGEM
    # =====================================================

    despesas = listar_despesas(
        usuario_id,
        mes
    )

    total_pago = sum(
        float(d["valor"])
        for d in despesas
        if bool(d["paga"])
    )

    total_pendente = sum(
        float(d["valor"])
        for d in despesas
        if not bool(d["paga"])
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "✅ Pago",
        fmt_moeda(total_pago)
    )

    col2.metric(
        "⏳ Pendente",
        fmt_moeda(total_pendente)
    )

    st.divider()

    if not despesas:
        st.info(
            "Nenhuma despesa cadastrada neste mês."
        )
        return

    # =====================================================
    # DESPESAS CADASTRADAS
    # =====================================================

    for despesa in despesas:
        despesa_id = despesa["id"]

        conta_nome = (
            despesa["conta_nome"]
            if despesa.get("conta_nome")
            else "Sem conta"
        )

        status = (
            "✅ Paga"
            if bool(despesa["paga"])
            else "⏳ Pendente"
        )

        with st.container(border=True):
            st.markdown(
                f"### {despesa['descricao']}"
            )

            st.write(
                f"**Categoria:** {despesa['categoria']}"
            )

            st.write(
                f"**Conta:** {conta_nome}"
            )

            st.write(
                f"**Valor:** {fmt_moeda(despesa['valor'])}"
            )

            st.write(
                f"**Vencimento:** {despesa['vencimento']}"
            )

            st.write(
                f"**Status:** {status}"
            )

            if bool(despesa.get("recorrente")):
                st.caption(
                    "🔁 Despesa recorrente"
                )

            novo_status = st.checkbox(
                "Marcar como paga",
                value=bool(despesa["paga"]),
                key=(
                    f"despesas_status_"
                    f"{usuario_id}_"
                    f"{mes}_"
                    f"{despesa_id}"
                )
            )

            if novo_status != bool(despesa["paga"]):
                atualizar_status_despesa(
                    usuario_id=usuario_id,
                    despesa_id=despesa_id,
                    novo_status=novo_status
                )

                st.rerun()

            if st.button(
                "🗑️ Excluir despesa",
                key=(
                    f"despesas_excluir_"
                    f"{usuario_id}_"
                    f"{mes}_"
                    f"{despesa_id}"
                ),
                use_container_width=True
            ):
                deletar_despesa(
                    usuario_id=usuario_id,
                    despesa_id=despesa_id
                )

                st.success(
                    "Despesa excluída com sucesso!"
                )

                st.rerun()
