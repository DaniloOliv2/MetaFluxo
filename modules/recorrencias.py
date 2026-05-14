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


def listar_modelos_recorrentes(usuario_id):
    garantir_tabela_despesas()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT descricao, categoria, conta_id, valor, vencimento
        FROM despesas
        WHERE usuario_id = ? AND recorrente = 1
        GROUP BY descricao, categoria, conta_id, valor
        ORDER BY descricao ASC
    """, (usuario_id,))

    dados = cursor.fetchall()
    conn.close()
    return dados


def despesa_ja_existe(usuario_id, mes, descricao, categoria, conta_id, valor):
    conn = conectar()
    cursor = conn.cursor()

    existe = cursor.execute("""
        SELECT id
        FROM despesas
        WHERE usuario_id = ?
          AND mes = ?
          AND descricao = ?
          AND categoria = ?
          AND conta_id = ?
          AND valor = ?
        LIMIT 1
    """, (
        usuario_id,
        mes,
        descricao,
        categoria,
        conta_id,
        float(valor)
    )).fetchone()

    conn.close()
    return existe is not None


def gerar_recorrencias(usuario_id, mes):
    modelos = listar_modelos_recorrentes(usuario_id)

    if not modelos:
        return 0

    conn = conectar()
    cursor = conn.cursor()

    criadas = 0

    for item in modelos:
        descricao = item["descricao"]
        categoria = item["categoria"]
        conta_id = item["conta_id"]
        valor = float(item["valor"])
        vencimento = item["vencimento"]

        if despesa_ja_existe(usuario_id, mes, descricao, categoria, conta_id, valor):
            continue

        cursor.execute("""
            INSERT INTO despesas (
                usuario_id, mes, descricao, categoria, conta_id, valor, paga, vencimento, recorrente
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, 1)
        """, (
            usuario_id,
            mes,
            descricao,
            categoria,
            conta_id,
            valor,
            vencimento
        ))

        criadas += 1

    conn.commit()
    conn.close()

    return criadas


def listar_recorrencias(usuario_id):
    modelos = listar_modelos_recorrentes(usuario_id)

    resultado = []

    conn = conectar()
    cursor = conn.cursor()

    for item in modelos:
        conta = cursor.execute("""
            SELECT nome
            FROM contas
            WHERE id = ? AND usuario_id = ?
        """, (item["conta_id"], usuario_id)).fetchone()

        resultado.append({
            "descricao": item["descricao"],
            "categoria": item["categoria"],
            "conta": conta["nome"] if conta else "Sem conta",
            "valor": float(item["valor"]),
            "vencimento": item["vencimento"]
        })

    conn.close()
    return resultado


def tela_recorrencias(usuario_id, mes):
    garantir_tabela_despesas()

    st.subheader("📅 Recorrências")

    st.info(
        "As recorrências são criadas a partir das despesas marcadas como recorrentes na aba 💳 Despesas."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("🔄 Gerar recorrências deste mês", use_container_width=True):
            criadas = gerar_recorrencias(usuario_id, mes)

            if criadas > 0:
                st.success(f"{criadas} despesa(s) recorrente(s) criada(s) para {mes}.")
            else:
                st.warning("Nenhuma nova recorrência foi criada. Talvez elas já existam neste mês.")

            st.rerun()

    recorrencias = listar_recorrencias(usuario_id)

    if not recorrencias:
        st.warning("Nenhuma despesa recorrente cadastrada ainda.")
        st.caption("Vá na aba 💳 Despesas, cadastre uma despesa e marque como recorrente.")
        return

    st.divider()

    total = sum(item["valor"] for item in recorrencias)

    st.metric("Total mensal previsto em recorrências", fmt_moeda(total))

    st.divider()

    for item in recorrencias:
        with st.container(border=True):
            st.markdown(f"### {item['descricao']}")
            st.write(f"**Categoria:** {item['categoria']}")
            st.write(f"**Conta:** {item['conta']}")
            st.write(f"**Valor:** {fmt_moeda(item['valor'])}")
            st.write(f"**Vencimento original:** {item['vencimento']}")
