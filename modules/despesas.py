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
        SELECT *
        FROM contas
        WHERE usuario_id = :usuario_id
        ORDER BY nome
    """, {
        "usuario_id": usuario_id
    })


def criar_despesa(usuario_id, mes, descricao, categoria, conta_id, valor, paga, vencimento, recorrente):
    executar_sql("""
        INSERT INTO despesas (
            usuario_id, mes, descricao, categoria, conta_id,
            valor, paga, vencimento, recorrente
        )
        VALUES (
            :usuario_id, :mes, :descricao, :categoria, :conta_id,
            :valor, :paga, :vencimento, :recorrente
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
        SELECT *
        FROM despesas
        WHERE usuario_id = :usuario_id
          AND mes = :mes
        ORDER BY id DESC
    """, {
        "usuario_id": usuario_id,
        "mes": mes
    })


def buscar_nome_conta(conta_id):
    if not conta_id:
        return "Sem conta"

    conta = buscar_um("""
        SELECT nome
        FROM contas
        WHERE id = :conta_id
    """, {
        "conta_id": conta_id
    })

    return conta["nome"] if conta else "Sem conta"


def atualizar_status_despesa(usuario_id, despesa_id, novo_status):
    despesa = buscar_um("""
        SELECT *
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
    valor = float(despesa["valor"])
    conta_id = despesa["conta_id"]

    if conta_id and status_atual != bool(novo_status):
        if novo_status:
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
        else:
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
        "paga": bool(novo_status),
        "despesa_id": despesa_id,
        "usuario_id": usuario_id
    })


def deletar_despesa(usuario_id, despesa_id):
    despesa = buscar_um("""
        SELECT *
        FROM despesas
        WHERE id = :despesa_id
          AND usuario_id = :usuario_id
    """, {
        "despesa_id": despesa_id,
        "usuario_id": usuario_id
    })

    if despesa and despesa["paga"] and despesa["conta_id"]:
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
            conta_nome = st.selectbox("Conta", list(contas_opcoes.keys()))

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

            vencimento = st.date_input("Vencimento")
            paga = st.checkbox("Já foi paga?")
            recorrente = st.checkbox("Despesa recorrente?")

            enviar = st.form_submit_button("Cadastrar despesa", use_container_width=True)

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
        conta_nome = buscar_nome_conta(despesa.get("conta_id"))
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
                value=bool(despesa["paga"]),
                key=f"status_{despesa['id']}"
            )

            if novo_status != bool(despesa["paga"]):
                atualizar_status_despesa(
                    usuario_id,
                    despesa["id"],
                    novo_status
                )
                st.rerun()

           if st.button(
                "🗑️ Excluir despesa",
                key=f"despesas_del_{usuario_id}_{mes}_{despesa['id']}",
                use_container_width=True
            ):
                deletar_despesa(usuario_id, despesa["id"])
                st.success("Despesa excluída!")
                st.rerun()
