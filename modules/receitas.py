import streamlit as st
from database.neon_config import executar_sql, buscar_todos, buscar_um


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabela_receitas():
    executar_sql("""
        CREATE TABLE IF NOT EXISTS receitas (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            conta_id BIGINT,
            valor NUMERIC(15,2) NOT NULL DEFAULT 0,
            recebida BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT fk_receitas_conta
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


def criar_receita(usuario_id, mes, descricao, categoria, conta_id, valor, recebida=True):
    executar_sql("""
        INSERT INTO receitas (
            usuario_id, mes, descricao, categoria, conta_id, valor, recebida
        )
        VALUES (
            :usuario_id, :mes, :descricao, :categoria, :conta_id, :valor, :recebida
        )
    """, {
        "usuario_id": usuario_id,
        "mes": mes,
        "descricao": descricao,
        "categoria": categoria,
        "conta_id": conta_id,
        "valor": float(valor),
        "recebida": bool(recebida)
    })

    if recebida and conta_id:
        executar_sql("""
            UPDATE contas
            SET saldo = saldo + :valor
            WHERE id = :conta_id
              AND usuario_id = :usuario_id
        """, {
            "valor": float(valor),
            "conta_id": conta_id,
            "usuario_id": usuario_id
        })


def listar_receitas(usuario_id, mes):
    return buscar_todos("""
        SELECT id, usuario_id, mes, descricao, categoria, conta_id, valor, recebida
        FROM receitas
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


def deletar_receita(usuario_id, receita_id):
    receita = buscar_um("""
        SELECT *
        FROM receitas
        WHERE id = :receita_id
          AND usuario_id = :usuario_id
    """, {
        "receita_id": receita_id,
        "usuario_id": usuario_id
    })

    if not receita:
        return

    if receita["recebida"] and receita["conta_id"]:
        executar_sql("""
            UPDATE contas
            SET saldo = saldo - :valor
            WHERE id = :conta_id
              AND usuario_id = :usuario_id
        """, {
            "valor": float(receita["valor"]),
            "conta_id": receita["conta_id"],
            "usuario_id": usuario_id
        })

    executar_sql("""
        DELETE FROM receitas
        WHERE id = :receita_id
          AND usuario_id = :usuario_id
    """, {
        "receita_id": receita_id,
        "usuario_id": usuario_id
    })


def tela_receitas(usuario_id, mes):
    garantir_tabela_receitas()

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

    contas_opcoes = {
        f"{conta['nome']} — {conta['tipo']}": conta["id"]
        for conta in contas
    }

    with st.expander("➕ Nova receita", expanded=False):
        with st.form("form_nova_receita", clear_on_submit=True):
            descricao = st.text_input(
                "Descrição",
                placeholder="Ex: Salário, PIX, venda, renda extra"
            )

            categoria = st.selectbox("Categoria", categorias)
            conta_nome = st.selectbox("Conta de destino", list(contas_opcoes.keys()))

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help="Para trinta mil, digite 30000."
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
        conta_nome = buscar_nome_conta(receita.get("conta_id"))

        with st.container(border=True):
            st.markdown(f"### {receita['descricao']}")
            st.write(f"**Categoria:** {receita['categoria']}")
            st.write(f"**Conta:** {conta_nome}")
            st.write(f"**Valor:** {fmt_moeda(receita['valor'])}")
            st.write(f"**Status:** {status}")

            if st.button(
                "🗑️ Excluir receita",
                key=f"del_receita_{receita['id']}",
                use_container_width=True
            ):
                deletar_receita(usuario_id, receita["id"])
                st.success("Receita excluída!")
                st.rerun()
