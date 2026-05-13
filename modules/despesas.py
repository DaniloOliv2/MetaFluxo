import streamlit as st
from utils.database import conectar


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabela_despesas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            conta_id INTEGER,
            valor REAL NOT NULL DEFAULT 0,
            paga INTEGER NOT NULL DEFAULT 0,
            vencimento TEXT,
            recorrente INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def listar_contas(usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, tipo, saldo
        FROM contas
        WHERE usuario_id = ?
        ORDER BY nome ASC
    """, (usuario_id,))

    contas = cursor.fetchall()
    conn.close()
    return contas


def criar_despesa(usuario_id, mes, descricao, categoria, conta_id, valor, paga, vencimento, recorrente):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO despesas (
            usuario_id, mes, descricao, categoria, conta_id, valor, paga, vencimento, recorrente
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        usuario_id,
        mes,
        descricao,
        categoria,
        conta_id,
        float(valor),
        int(paga),
        vencimento,
        int(recorrente)
    ))

    if paga and conta_id:
        cursor.execute("""
            UPDATE contas
            SET saldo = saldo - ?
            WHERE id = ? AND usuario_id = ?
        """, (float(valor), conta_id, usuario_id))

    conn.commit()
    conn.close()


def listar_despesas(usuario_id, mes):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT despesas.*, contas.nome AS conta_nome
        FROM despesas
        LEFT JOIN contas ON contas.id = despesas.conta_id
        WHERE despesas.usuario_id = ? AND despesas.mes = ?
        ORDER BY despesas.id DESC
    """, (usuario_id, mes))

    despesas = cursor.fetchall()
    conn.close()
    return despesas


def atualizar_status_despesa(usuario_id, despesa_id, novo_status):
    conn = conectar()
    cursor = conn.cursor()

    despesa = cursor.execute("""
        SELECT *
        FROM despesas
        WHERE id = ? AND usuario_id = ?
    """, (despesa_id, usuario_id)).fetchone()

    if not despesa:
        conn.close()
        return

    status_atual = int(despesa["paga"])
    novo_status = int(novo_status)
    valor = float(despesa["valor"])
    conta_id = despesa["conta_id"]

    if conta_id and status_atual != novo_status:
        if novo_status == 1:
            cursor.execute("""
                UPDATE contas
                SET saldo = saldo - ?
                WHERE id = ? AND usuario_id = ?
            """, (valor, conta_id, usuario_id))
        else:
            cursor.execute("""
                UPDATE contas
                SET saldo = saldo + ?
                WHERE id = ? AND usuario_id = ?
            """, (valor, conta_id, usuario_id))

    cursor.execute("""
        UPDATE despesas
        SET paga = ?
        WHERE id = ? AND usuario_id = ?
    """, (novo_status, despesa_id, usuario_id))

    conn.commit()
    conn.close()


def deletar_despesa(usuario_id, despesa_id):
    conn = conectar()
    cursor = conn.cursor()

    despesa = cursor.execute("""
        SELECT *
        FROM despesas
        WHERE id = ? AND usuario_id = ?
    """, (despesa_id, usuario_id)).fetchone()

    if despesa and despesa["paga"] and despesa["conta_id"]:
        cursor.execute("""
            UPDATE contas
            SET saldo = saldo + ?
            WHERE id = ? AND usuario_id = ?
        """, (float(despesa["valor"]), despesa["conta_id"], usuario_id))

    cursor.execute("""
        DELETE FROM despesas
        WHERE id = ? AND usuario_id = ?
    """, (despesa_id, usuario_id))

    conn.commit()
    conn.close()


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
        st.warning("Antes de cadastrar despesas, crie pelo menos uma conta na aba 🏦 Contas.")
        return

    contas_opcoes = {f"{conta['nome']} — {conta['tipo']} — {fmt_moeda(conta['saldo'])}": conta["id"] for conta in contas}

    with st.expander("➕ Nova despesa", expanded=False):
        with st.form("form_nova_despesa", clear_on_submit=True):

            descricao = st.text_input("Descrição", placeholder="Ex: aluguel, mercado, gasolina, internet")

            categoria = st.selectbox("Categoria", categorias)

            conta_nome = st.selectbox("Conta de origem", list(contas_opcoes.keys()))

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help="Para trinta mil, digite 30000. O sistema exibirá como R$ 30.000,00."
            )

            vencimento = st.date_input("Vencimento")

            paga = st.checkbox("Já está paga?", value=False)

            recorrente = st.checkbox("Despesa recorrente?", value=False)

            enviar = st.form_submit_button("Cadastrar despesa", use_container_width=True)

            if enviar:
                if not descricao.strip():
                    st.warning("Informe a descrição da despesa.")
                elif valor <= 0:
                    st.warning("Informe um valor maior que zero.")
                else:
                    criar_despesa(
                        usuario_id,
                        mes,
                        descricao.strip(),
                        categoria,
                        contas_opcoes[conta_nome],
                        valor,
                        paga,
                        str(vencimento),
                        recorrente
                    )
                    st.success("Despesa cadastrada com sucesso!")
                    st.rerun()

    despesas = listar_despesas(usuario_id, mes)

    total_pago = sum(float(d["valor"]) for d in despesas if d["paga"])
    total_pendente = sum(float(d["valor"]) for d in despesas if not d["paga"])

    c1, c2 = st.columns(2)
    c1.metric("✅ Pago", fmt_moeda(total_pago))
    c2.metric("⏳ Pendente", fmt_moeda(total_pendente))

    st.divider()

    if not despesas:
        st.info("Nenhuma despesa cadastrada neste mês.")
        return

    for despesa in despesas:
        status = "✅ Paga" if despesa["paga"] else "⏳ Pendente"
        conta_nome = despesa["conta_nome"] if despesa["conta_nome"] else "Sem conta"
        recorrente_txt = "Sim" if despesa["recorrente"] else "Não"

        with st.container(border=True):
            st.markdown(f"### {despesa['descricao']}")
            st.write(f"**Categoria:** {despesa['categoria']}")
            st.write(f"**Conta:** {conta_nome}")
            st.write(f"**Valor:** {fmt_moeda(despesa['valor'])}")
            st.write(f"**Vencimento:** {despesa['vencimento']}")
            st.write(f"**Recorrente:** {recorrente_txt}")
            st.write(f"**Status:** {status}")

            col1, col2 = st.columns(2)

            novo_status = col1.checkbox(
                "Marcar como paga",
                value=bool(despesa["paga"]),
                key=f"status_despesa_{despesa['id']}"
            )

            if novo_status != bool(despesa["paga"]):
                atualizar_status_despesa(usuario_id, despesa["id"], novo_status)
                st.rerun()

            if col2.button("🗑️ Excluir despesa", key=f"del_despesa_{despesa['id']}", use_container_width=True):
                deletar_despesa(usuario_id, despesa["id"])
                st.success("Despesa excluída!")
                st.rerun()
