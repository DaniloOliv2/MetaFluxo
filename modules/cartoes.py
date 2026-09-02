import streamlit as st
from datetime import datetime
from database.neon_config import executar_sql, buscar_todos, buscar_um


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabelas_cartoes():
    executar_sql("""
        CREATE TABLE IF NOT EXISTS cartoes (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL,
            nome TEXT NOT NULL,
            bandeira TEXT NOT NULL,
            limite NUMERIC(15,2) NOT NULL DEFAULT 0,
            conta_id BIGINT,
            fechamento INTEGER NOT NULL,
            vencimento INTEGER NOT NULL,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT fk_cartoes_conta
                FOREIGN KEY (conta_id)
                REFERENCES contas(id)
                ON DELETE SET NULL
        )
    """)

    executar_sql("""
        CREATE TABLE IF NOT EXISTS compras_cartao (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL,
            cartao_id BIGINT NOT NULL,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor_total NUMERIC(15,2) NOT NULL DEFAULT 0,
            parcelas INTEGER NOT NULL DEFAULT 1,
            parcela_atual INTEGER NOT NULL DEFAULT 1,
            valor_parcela NUMERIC(15,2) NOT NULL DEFAULT 0,
            compra_pai_id BIGINT,
            paga BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT fk_compras_cartao
                FOREIGN KEY (cartao_id)
                REFERENCES cartoes(id)
                ON DELETE CASCADE
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


def criar_cartao(usuario_id, nome, bandeira, limite, conta_id, fechamento, vencimento):
    executar_sql("""
        INSERT INTO cartoes (
            usuario_id, nome, bandeira, limite, conta_id,
            fechamento, vencimento, ativo
        )
        VALUES (
            :usuario_id, :nome, :bandeira, :limite, :conta_id,
            :fechamento, :vencimento, TRUE
        )
    """, {
        "usuario_id": usuario_id,
        "nome": nome,
        "bandeira": bandeira,
        "limite": float(limite),
        "conta_id": conta_id,
        "fechamento": int(fechamento),
        "vencimento": int(vencimento)
    })


def listar_cartoes(usuario_id):
    return buscar_todos("""
        SELECT
            c.*,
            COALESCE(ct.nome, 'Não vinculada') AS conta_nome
        FROM cartoes c
        LEFT JOIN contas ct
            ON ct.id = c.conta_id
        WHERE c.usuario_id = :usuario_id
          AND c.ativo = TRUE
        ORDER BY c.id DESC
    """, {
        "usuario_id": usuario_id
    })


def atualizar_cartao(usuario_id, cartao_id, nome, bandeira, limite, conta_id, fechamento, vencimento):
    executar_sql("""
        UPDATE cartoes
        SET nome = :nome,
            bandeira = :bandeira,
            limite = :limite,
            conta_id = :conta_id,
            fechamento = :fechamento,
            vencimento = :vencimento
        WHERE id = :cartao_id
          AND usuario_id = :usuario_id
    """, {
        "nome": nome,
        "bandeira": bandeira,
        "limite": float(limite),
        "conta_id": conta_id,
        "fechamento": int(fechamento),
        "vencimento": int(vencimento),
        "cartao_id": cartao_id,
        "usuario_id": usuario_id
    })


def deletar_cartao(usuario_id, cartao_id):
    executar_sql("""
        UPDATE cartoes
        SET ativo = FALSE
        WHERE id = :cartao_id
          AND usuario_id = :usuario_id
    """, {
        "cartao_id": cartao_id,
        "usuario_id": usuario_id
    })


def calcular_mes_fatura(fechamento):
    hoje = datetime.now()

    if hoje.day > int(fechamento):
        if hoje.month == 12:
            return f"{hoje.year + 1}-01"

        return f"{hoje.year}-{str(hoje.month + 1).zfill(2)}"

    return f"{hoje.year}-{str(hoje.month).zfill(2)}"


def adicionar_meses(mes_base, incremento):
    ano, mes = map(int, mes_base.split("-"))
    mes += incremento

    while mes > 12:
        mes -= 12
        ano += 1

    return f"{ano}-{str(mes).zfill(2)}"


def criar_compra(usuario_id, cartao_id, descricao, categoria, valor_total, parcelas):
    cartao = buscar_um("""
        SELECT fechamento
        FROM cartoes
        WHERE id = :cartao_id
    """, {
        "cartao_id": cartao_id
    })

    fechamento = cartao["fechamento"]
    mes_inicial = calcular_mes_fatura(fechamento)
    valor_parcela = float(valor_total) / int(parcelas)

    resultado = executar_sql("""
        INSERT INTO compras_cartao (
            usuario_id, cartao_id, mes, descricao, categoria,
            valor_total, parcelas, parcela_atual, valor_parcela, paga
        )
        VALUES (
            :usuario_id, :cartao_id, :mes, :descricao, :categoria,
            :valor_total, :parcelas, 1, :valor_parcela, FALSE
        )
        RETURNING id
    """, {
        "usuario_id": usuario_id,
        "cartao_id": cartao_id,
        "mes": mes_inicial,
        "descricao": descricao,
        "categoria": categoria,
        "valor_total": float(valor_total),
        "parcelas": int(parcelas),
        "valor_parcela": valor_parcela
    })

    compra_pai_id = resultado.scalar_one()

    executar_sql("""
        UPDATE compras_cartao
        SET compra_pai_id = :compra_pai_id
        WHERE id = :compra_pai_id
    """, {
        "compra_pai_id": compra_pai_id
    })

    for parcela in range(2, int(parcelas) + 1):
        mes_parcela = adicionar_meses(mes_inicial, parcela - 1)

        executar_sql("""
            INSERT INTO compras_cartao (
                usuario_id, cartao_id, mes, descricao, categoria,
                valor_total, parcelas, parcela_atual, valor_parcela,
                compra_pai_id, paga
            )
            VALUES (
                :usuario_id, :cartao_id, :mes, :descricao, :categoria,
                :valor_total, :parcelas, :parcela_atual, :valor_parcela,
                :compra_pai_id, FALSE
            )
        """, {
            "usuario_id": usuario_id,
            "cartao_id": cartao_id,
            "mes": mes_parcela,
            "descricao": descricao,
            "categoria": categoria,
            "valor_total": valor_parcela,
            "parcelas": int(parcelas),
            "parcela_atual": parcela,
            "valor_parcela": valor_parcela,
            "compra_pai_id": compra_pai_id
        })


def listar_compras_cartao(usuario_id, cartao_id):
    return buscar_todos("""
        SELECT *
        FROM compras_cartao
        WHERE usuario_id = :usuario_id
          AND cartao_id = :cartao_id
        ORDER BY id DESC
    """, {
        "usuario_id": usuario_id,
        "cartao_id": cartao_id
    })


def listar_compras_mes(usuario_id, mes):
    return buscar_todos("""
        SELECT
            cc.*,
            COALESCE(c.nome, 'Sem cartão') AS cartao_nome
        FROM compras_cartao cc
        LEFT JOIN cartoes c
            ON c.id = cc.cartao_id
        WHERE cc.usuario_id = :usuario_id
          AND cc.mes = :mes
        ORDER BY cc.id DESC
    """, {
        "usuario_id": usuario_id,
        "mes": mes
    })


def deletar_compra(usuario_id, compra_id):
    executar_sql("""
        DELETE FROM compras_cartao
        WHERE id = :compra_id
          AND usuario_id = :usuario_id
    """, {
        "compra_id": compra_id,
        "usuario_id": usuario_id
    })


def total_usado_cartao(usuario_id, cartao_id):
    resultado = buscar_um("""
        SELECT COALESCE(SUM(valor_total), 0) AS total
        FROM compras_cartao
        WHERE usuario_id = :usuario_id
          AND cartao_id = :cartao_id
    """, {
        "usuario_id": usuario_id,
        "cartao_id": cartao_id
    })

    return float(resultado["total"] or 0)


def tela_cartoes(usuario_id, mes):
    garantir_tabelas_cartoes()

    st.subheader("💳 Cartões de Crédito")

    bandeiras = ["Mastercard", "Visa", "Elo", "American Express", "Hipercard", "Outro"]
    categorias = [
        "🍎 Alimentação", "🚗 Transporte", "🎡 Lazer", "💊 Saúde",
        "📚 Estudos", "📱 Assinaturas", "👕 Vestuário", "🏠 Casa", "🛠️ Outros"
    ]

    contas = listar_contas(usuario_id)

    if not contas:
        st.warning("Antes de cadastrar cartões, crie pelo menos uma conta na aba 🏦 Contas.")
        return

    contas_opcoes = {
        f"{c['nome']} — {c['tipo']} — {fmt_moeda(c['saldo'])}": c["id"]
        for c in contas
    }

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
                    criar_compra(
                        usuario_id,
                        cartoes_opcoes[cartao_nome],
                        descricao.strip(),
                        categoria,
                        valor_total,
                        parcelas
                    )

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
                st.write(f"**Conta da fatura:** {cartao.get('conta_nome', 'Não vinculada')}")
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

                            if st.button(
                                "Excluir compra",
                                key=f"del_compra_{compra['id']}",
                                use_container_width=True
                            ):
                                deletar_compra(usuario_id, compra["id"])
                                st.success("Compra excluída!")
                                st.rerun()

                            st.divider()

                with st.expander("✏️ Editar / Excluir cartão"):
                    novo_nome = st.text_input(
                        "Nome",
                        value=cartao["nome"],
                        key=f"nome_cartao_{cartao['id']}"
                    )

                    nova_bandeira = st.selectbox(
                        "Bandeira",
                        bandeiras,
                        index=bandeiras.index(cartao["bandeira"])
                        if cartao["bandeira"] in bandeiras else 0,
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
                        index=list(contas_opcoes.keys()).index(conta_atual_label)
                        if conta_atual_label in contas_opcoes else 0,
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

                    if b1.button(
                        "Salvar",
                        key=f"salvar_cartao_{cartao['id']}",
                        use_container_width=True
                    ):
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

                    if b2.button(
                        "Excluir",
                        key=f"excluir_cartao_{cartao['id']}",
                        use_container_width=True
                    ):
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
                st.write(f"**Cartão:** {compra.get('cartao_nome', 'Sem cartão')}")
                st.write(f"**Categoria:** {compra['categoria']}")
                st.write(f"**Valor total:** {fmt_moeda(compra['valor_total'])}")
                st.write(f"**Parcelas:** {compra['parcelas']}x de {fmt_moeda(valor_parcela)}")

                if st.button(
                    "🗑️ Excluir",
                    key=f"del_compra_mes_{compra['id']}",
                    use_container_width=True
                ):
                    deletar_compra(usuario_id, compra["id"])
                    st.success("Compra excluída!")
                    st.rerun()
