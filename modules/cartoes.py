import streamlit as st
from utils.database import conectar


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabelas_cartoes():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cartoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            bandeira TEXT NOT NULL,
            limite REAL NOT NULL DEFAULT 0,
            conta_id INTEGER,
            fechamento INTEGER NOT NULL DEFAULT 1,
            vencimento INTEGER NOT NULL DEFAULT 10,
            ativo INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras_cartao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            cartao_id INTEGER NOT NULL,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor_total REAL NOT NULL DEFAULT 0,
            parcelas INTEGER NOT NULL DEFAULT 1,
            parcela_atual INTEGER NOT NULL DEFAULT 1,
            paga INTEGER NOT NULL DEFAULT 0,
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


def criar_cartao(usuario_id, nome, bandeira, limite, conta_id, fechamento, vencimento):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cartoes (
            usuario_id, nome, bandeira, limite, conta_id, fechamento, vencimento
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        usuario_id,
        nome,
        bandeira,
        float(limite),
        conta_id,
        int(fechamento),
        int(vencimento)
    ))

    conn.commit()
    conn.close()


def listar_cartoes(usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cartoes.*, contas.nome AS conta_nome
        FROM cartoes
        LEFT JOIN contas ON contas.id = cartoes.conta_id
        WHERE cartoes.usuario_id = ? AND cartoes.ativo = 1
        ORDER BY cartoes.id DESC
    """, (usuario_id,))

    cartoes = cursor.fetchall()
    conn.close()
    return cartoes


def atualizar_cartao(usuario_id, cartao_id, nome, bandeira, limite, conta_id, fechamento, vencimento):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cartoes
        SET nome = ?, bandeira = ?, limite = ?, conta_id = ?, fechamento = ?, vencimento = ?
        WHERE id = ? AND usuario_id = ?
    """, (
        nome,
        bandeira,
        float(limite),
        conta_id,
        int(fechamento),
        int(vencimento),
        cartao_id,
        usuario_id
    ))

    conn.commit()
    conn.close()


def deletar_cartao(usuario_id, cartao_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cartoes
        SET ativo = 0
        WHERE id = ? AND usuario_id = ?
    """, (cartao_id, usuario_id))

    conn.commit()
    conn.close()


def total_usado_cartao(usuario_id, cartao_id):
    conn = conectar()
    cursor = conn.cursor()

    total = cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0) AS total
        FROM compras_cartao
        WHERE usuario_id = ? AND cartao_id = ?
    """, (usuario_id, cartao_id)).fetchone()["total"]

    conn.close()
    return float(total or 0)


def tela_cartoes(usuario_id):
    garantir_tabelas_cartoes()

    st.subheader("💳 Cartões de Crédito")

    bandeiras = [
        "Mastercard",
        "Visa",
        "Elo",
        "American Express",
        "Hipercard",
        "Outro"
    ]

    contas = listar_contas(usuario_id)

    if not contas:
        st.warning("Antes de cadastrar cartões, crie pelo menos uma conta na aba 🏦 Contas.")
        return

    contas_opcoes = {
        f"{conta['nome']} — {conta['tipo']} — {fmt_moeda(conta['saldo'])}": conta["id"]
        for conta in contas
    }

    with st.expander("➕ Novo cartão", expanded=False):
        with st.form("form_novo_cartao", clear_on_submit=True):
            nome = st.text_input("Nome do cartão", placeholder="Ex: Nubank Roxinho, Inter Gold")

            bandeira = st.selectbox("Bandeira", bandeiras)

            limite = st.number_input(
                "Limite total",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help="Para cinco mil, digite 5000."
            )

            conta_nome = st.selectbox("Conta para pagamento da fatura", list(contas_opcoes.keys()))

            col1, col2 = st.columns(2)

            fechamento = col1.number_input(
                "Dia de fechamento",
                min_value=1,
                max_value=31,
                value=1,
                step=1
            )

            vencimento = col2.number_input(
                "Dia de vencimento",
                min_value=1,
                max_value=31,
                value=10,
                step=1
            )

            enviar = st.form_submit_button("Cadastrar cartão", use_container_width=True)

            if enviar:
                if not nome.strip():
                    st.warning("Informe o nome do cartão.")
                elif limite <= 0:
                    st.warning("Informe um limite maior que zero.")
                else:
                    criar_cartao(
                        usuario_id,
                        nome.strip(),
                        bandeira,
                        limite,
                        contas_opcoes[conta_nome],
                        fechamento,
                        vencimento
                    )
                    st.success("Cartão cadastrado com sucesso!")
                    st.rerun()

    cartoes = listar_cartoes(usuario_id)

    if not cartoes:
        st.info("Nenhum cartão cadastrado ainda.")
        return

    cols = st.columns(3)

    for i, cartao in enumerate(cartoes):
        usado = total_usado_cartao(usuario_id, cartao["id"])
        limite = float(cartao["limite"])
        disponivel = limite - usado
        progresso = min(usado / limite, 1.0) if limite > 0 else 0

        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### 💳 {cartao['nome']}")
                st.write(f"**Bandeira:** {cartao['bandeira']}")
                st.write(f"**Conta da fatura:** {cartao['conta_nome'] or 'Não vinculada'}")
                st.write(f"**Limite:** {fmt_moeda(limite)}")
                st.write(f"**Usado:** {fmt_moeda(usado)}")
                st.write(f"**Disponível:** {fmt_moeda(disponivel)}")
                st.progress(progresso)
                st.caption(f"Fecha dia {cartao['fechamento']} | Vence dia {cartao['vencimento']}")

                with st.expander("✏️ Editar / Excluir"):
                    novo_nome = st.text_input(
                        "Nome",
                        value=cartao["nome"],
                        key=f"nome_cartao_{cartao['id']}"
                    )

                    nova_bandeira = st.selectbox(
                        "Bandeira",
                        bandeiras,
                        index=bandeiras.index(cartao["bandeira"]) if cartao["bandeira"] in bandeiras else 0,
                        key=f"bandeira_cartao_{cartao['id']}"
                    )

                    novo_limite = st.number_input(
                        "Limite",
                        min_value=0.0,
                        value=float(cartao["limite"]),
                        step=100.0,
                        format="%.2f",
                        key=f"limite_cartao_{cartao['id']}"
                    )

                    conta_atual_label = None
                    for label, cid in contas_opcoes.items():
                        if cid == cartao["conta_id"]:
                            conta_atual_label = label
                            break

                    nova_conta = st.selectbox(
                        "Conta da fatura",
                        list(contas_opcoes.keys()),
                        index=list(contas_opcoes.keys()).index(conta_atual_label) if conta_atual_label in contas_opcoes else 0,
                        key=f"conta_cartao_{cartao['id']}"
                    )

                    c1, c2 = st.columns(2)

                    novo_fechamento = c1.number_input(
                        "Fechamento",
                        min_value=1,
                        max_value=31,
                        value=int(cartao["fechamento"]),
                        step=1,
                        key=f"fechamento_cartao_{cartao['id']}"
                    )

                    novo_vencimento = c2.number_input(
                        "Vencimento",
                        min_value=1,
                        max_value=31,
                        value=int(cartao["vencimento"]),
                        step=1,
                        key=f"vencimento_cartao_{cartao['id']}"
                    )

                    b1, b2 = st.columns(2)

                    if b1.button("Salvar", key=f"salvar_cartao_{cartao['id']}", use_container_width=True):
                        if not novo_nome.strip():
                            st.warning("Informe o nome do cartão.")
                        else:
                            atualizar_cartao(
                                usuario_id,
                                cartao["id"],
                                novo_nome.strip(),
                                nova_bandeira,
                                novo_limite,
                                contas_opcoes[nova_conta],
                                novo_fechamento,
                                novo_vencimento
                            )
                            st.success("Cartão atualizado!")
                            st.rerun()

                    if b2.button("Excluir", key=f"excluir_cartao_{cartao['id']}", use_container_width=True):
                        deletar_cartao(usuario_id, cartao["id"])
                        st.success("Cartão excluído!")
                        st.rerun()
