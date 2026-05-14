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

    cursor.execute('''
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
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compras_cartao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            cartao_id INTEGER NOT NULL,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor_total REAL NOT NULL DEFAULT 0,
            parcelas INTEGER NOT NULL DEFAULT 1,
            paga INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def listar_contas(usuario_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, tipo, saldo FROM contas WHERE usuario_id = ? ORDER BY nome ASC",
        (usuario_id,)
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def criar_cartao(usuario_id, nome, bandeira, limite, conta_id, fechamento, vencimento):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cartoes (usuario_id, nome, bandeira, limite, conta_id, fechamento, vencimento)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (usuario_id, nome, bandeira, float(limite), conta_id, int(fechamento), int(vencimento)))
    conn.commit()
    conn.close()


def listar_cartoes(usuario_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cartoes.*, contas.nome AS conta_nome
        FROM cartoes
        LEFT JOIN contas ON contas.id = cartoes.conta_id
        WHERE cartoes.usuario_id = ? AND cartoes.ativo = 1
        ORDER BY cartoes.id DESC
    ''', (usuario_id,))
    dados = cursor.fetchall()
    conn.close()
    return dados


def atualizar_cartao(usuario_id, cartao_id, nome, bandeira, limite, conta_id, fechamento, vencimento):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE cartoes
        SET nome=?, bandeira=?, limite=?, conta_id=?, fechamento=?, vencimento=?
        WHERE id=? AND usuario_id=?
    ''', (nome, bandeira, float(limite), conta_id, int(fechamento), int(vencimento), cartao_id, usuario_id))
    conn.commit()
    conn.close()


def deletar_cartao(usuario_id, cartao_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE cartoes SET ativo = 0 WHERE id = ? AND usuario_id = ?", (cartao_id, usuario_id))
    conn.commit()
    conn.close()


def criar_compra(usuario_id, cartao_id, mes, descricao, categoria, valor_total, parcelas):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO compras_cartao (usuario_id, cartao_id, mes, descricao, categoria, valor_total, parcelas)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (usuario_id, cartao_id, mes, descricao, categoria, float(valor_total), int(parcelas)))
    conn.commit()
    conn.close()


def listar_compras_cartao(usuario_id, cartao_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM compras_cartao
        WHERE usuario_id = ? AND cartao_id = ?
        ORDER BY id DESC
    ''', (usuario_id, cartao_id))
    dados = cursor.fetchall()
    conn.close()
    return dados


def listar_compras_mes(usuario_id, mes):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT compras_cartao.*, cartoes.nome AS cartao_nome
        FROM compras_cartao
        LEFT JOIN cartoes ON cartoes.id = compras_cartao.cartao_id
        WHERE compras_cartao.usuario_id = ? AND compras_cartao.mes = ?
        ORDER BY compras_cartao.id DESC
    ''', (usuario_id, mes))
    dados = cursor.fetchall()
    conn.close()
    return dados


def deletar_compra(usuario_id, compra_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM compras_cartao WHERE id = ? AND usuario_id = ?", (compra_id, usuario_id))
    conn.commit()
    conn.close()


def total_usado_cartao(usuario_id, cartao_id):
    conn = conectar()
    cursor = conn.cursor()
    total = cursor.execute('''
        SELECT COALESCE(SUM(valor_total), 0) AS total
        FROM compras_cartao
        WHERE usuario_id = ? AND cartao_id = ?
    ''', (usuario_id, cartao_id)).fetchone()["total"]
    conn.close()
    return float(total or 0)


def tela_cartoes(usuario_id, mes):
    garantir_tabelas_cartoes()
    st.subheader("💳 Cartões de Crédito")

    bandeiras = ["Mastercard", "Visa", "Elo", "American Express", "Hipercard", "Outro"]
    categorias = ["🍎 Alimentação", "🚗 Transporte", "🎡 Lazer", "💊 Saúde", "📚 Estudos", "📱 Assinaturas", "👕 Vestuário", "🏠 Casa", "🛠️ Outros"]

    contas = listar_contas(usuario_id)
    if not contas:
        st.warning("Antes de cadastrar cartões, crie pelo menos uma conta na aba 🏦 Contas.")
        return

    contas_opcoes = {f"{c['nome']} — {c['tipo']} — {fmt_moeda(c['saldo'])}": c["id"] for c in contas}

    with st.expander("➕ Novo cartão", expanded=False):
        with st.form("form_novo_cartao", clear_on_submit=True):
            nome = st.text_input("Nome do cartão", placeholder="Ex: Nubank Roxinho, Inter Gold")
            bandeira = st.selectbox("Bandeira", bandeiras)
            limite = st.number_input("Limite total", min_value=0.0, step=100.0, format="%.2f")
            conta_nome = st.selectbox("Conta para pagamento da fatura", list(contas_opcoes.keys()))
            col1, col2 = st.columns(2)
            fechamento = col1.number_input("Dia de fechamento", min_value=1, max_value=31, value=1, step=1)
            vencimento = col2.number_input("Dia de vencimento", min_value=1, max_value=31, value=10, step=1)

            if st.form_submit_button("Cadastrar cartão", use_container_width=True):
                if not nome.strip():
                    st.warning("Informe o nome do cartão.")
                elif limite <= 0:
                    st.warning("Informe um limite maior que zero.")
                else:
                    criar_cartao(usuario_id, nome.strip(), bandeira, limite, contas_opcoes[conta_nome], fechamento, vencimento)
                    st.success("Cartão cadastrado com sucesso!")
                    st.rerun()

    cartoes = listar_cartoes(usuario_id)
    if not cartoes:
        st.info("Nenhum cartão cadastrado ainda.")
        return

    cartoes_opcoes = {f"{c['nome']} — {c['bandeira']}": c["id"] for c in cartoes}

    with st.expander("🛒 Nova compra no cartão", expanded=False):
        with st.form("form_nova_compra_cartao", clear_on_submit=True):
            cartao_nome = st.selectbox("Cartão", list(cartoes_opcoes.keys()))
            descricao = st.text_input("Descrição da compra", placeholder="Ex: mercado, celular, assinatura")
            categoria = st.selectbox("Categoria", categorias)
            valor_total = st.number_input("Valor total da compra", min_value=0.0, step=100.0, format="%.2f")
            parcelas = st.number_input("Quantidade de parcelas", min_value=1, max_value=48, value=1, step=1)

            if st.form_submit_button("Cadastrar compra", use_container_width=True):
                if not descricao.strip():
                    st.warning("Informe a descrição da compra.")
                elif valor_total <= 0:
                    st.warning("Informe um valor maior que zero.")
                else:
                    criar_compra(usuario_id, cartoes_opcoes[cartao_nome], mes, descricao.strip(), categoria, valor_total, parcelas)
                    st.success("Compra cadastrada com sucesso!")
                    st.rerun()

    st.divider()
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

                with st.expander("🛒 Compras deste cartão"):
                    compras = listar_compras_cartao(usuario_id, cartao["id"])
                    if not compras:
                        st.info("Nenhuma compra neste cartão.")
                    else:
                        for compra in compras:
                            valor_parcela = float(compra["valor_total"]) / int(compra["parcelas"])
                            st.markdown(f"**{compra['descricao']}**")
                            st.write(f"Categoria: {compra['categoria']}")
                            st.write(f"Valor total: {fmt_moeda(compra['valor_total'])}")
                            st.write(f"Parcelas: {compra['parcelas']}x de {fmt_moeda(valor_parcela)}")
                            st.write(f"Mês: {compra['mes']}")
                            if st.button("Excluir compra", key=f"del_compra_{compra['id']}", use_container_width=True):
                                deletar_compra(usuario_id, compra["id"])
                                st.success("Compra excluída!")
                                st.rerun()
                            st.divider()

                with st.expander("✏️ Editar / Excluir cartão"):
                    novo_nome = st.text_input("Nome", value=cartao["nome"], key=f"nome_cartao_{cartao['id']}")
                    nova_bandeira = st.selectbox("Bandeira", bandeiras, index=bandeiras.index(cartao["bandeira"]) if cartao["bandeira"] in bandeiras else 0, key=f"bandeira_cartao_{cartao['id']}")
                    novo_limite = st.number_input("Limite", min_value=0.0, value=float(cartao["limite"]), step=100.0, format="%.2f", key=f"limite_cartao_{cartao['id']}")

                    conta_atual_label = None
                    for label, cid in contas_opcoes.items():
                        if cid == cartao["conta_id"]:
                            conta_atual_label = label
                            break

                    nova_conta = st.selectbox("Conta da fatura", list(contas_opcoes.keys()), index=list(contas_opcoes.keys()).index(conta_atual_label) if conta_atual_label in contas_opcoes else 0, key=f"conta_cartao_{cartao['id']}")

                    c1, c2 = st.columns(2)
                    novo_fechamento = c1.number_input("Fechamento", min_value=1, max_value=31, value=int(cartao["fechamento"]), step=1, key=f"fechamento_cartao_{cartao['id']}")
                    novo_vencimento = c2.number_input("Vencimento", min_value=1, max_value=31, value=int(cartao["vencimento"]), step=1, key=f"vencimento_cartao_{cartao['id']}")

                    b1, b2 = st.columns(2)
                    if b1.button("Salvar", key=f"salvar_cartao_{cartao['id']}", use_container_width=True):
                        atualizar_cartao(usuario_id, cartao["id"], novo_nome.strip(), nova_bandeira, novo_limite, contas_opcoes[nova_conta], novo_fechamento, novo_vencimento)
                        st.success("Cartão atualizado!")
                        st.rerun()

                    if b2.button("Excluir", key=f"excluir_cartao_{cartao['id']}", use_container_width=True):
                        deletar_cartao(usuario_id, cartao["id"])
                        st.success("Cartão excluído!")
                        st.rerun()

    st.divider()
    st.subheader(f"📄 Compras do mês: {mes}")
    compras_mes = listar_compras_mes(usuario_id, mes)

    if not compras_mes:
        st.info("Nenhuma compra cadastrada neste mês.")
    else:
        total_mes = sum(float(c["valor_total"]) for c in compras_mes)
        st.metric("Total comprado no mês", fmt_moeda(total_mes))

        for compra in compras_mes:
            valor_parcela = float(compra["valor_total"]) / int(compra["parcelas"])
            with st.container(border=True):
                st.markdown(f"### {compra['descricao']}")
                st.write(f"**Cartão:** {compra['cartao_nome']}")
                st.write(f"**Categoria:** {compra['categoria']}")
                st.write(f"**Valor total:** {fmt_moeda(compra['valor_total'])}")
                st.write(f"**Parcelas:** {compra['parcelas']}x de {fmt_moeda(valor_parcela)}")
                if st.button("🗑️ Excluir", key=f"del_compra_mes_{compra['id']}", use_container_width=True):
                    deletar_compra(usuario_id, compra["id"])
                    st.success("Compra excluída!")
                    st.rerun()
