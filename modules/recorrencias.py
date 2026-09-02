import streamlit as st
from database.neon_config import executar_sql, buscar_todos, buscar_um


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def listar_modelos_recorrentes(usuario_id):
    return buscar_todos("""
        SELECT DISTINCT
            descricao,
            categoria,
            conta_id,
            valor,
            vencimento
        FROM despesas
        WHERE usuario_id = :usuario_id
          AND recorrente = TRUE
        ORDER BY descricao ASC
    """, {
        "usuario_id": usuario_id
    })


def despesa_ja_existe(usuario_id, mes, descricao, categoria, conta_id, valor):
    existe = buscar_um("""
        SELECT id
        FROM despesas
        WHERE usuario_id = :usuario_id
          AND mes = :mes
          AND descricao = :descricao
          AND categoria = :categoria
          AND conta_id IS NOT DISTINCT FROM :conta_id
          AND valor = :valor
        LIMIT 1
    """, {
        "usuario_id": usuario_id,
        "mes": mes,
        "descricao": descricao,
        "categoria": categoria,
        "conta_id": conta_id,
        "valor": float(valor)
    })

    return existe is not None


def gerar_recorrencias(usuario_id, mes):
    modelos = listar_modelos_recorrentes(usuario_id)

    if not modelos:
        return 0

    criadas = 0

    for item in modelos:
        if despesa_ja_existe(
            usuario_id,
            mes,
            item["descricao"],
            item["categoria"],
            item["conta_id"],
            item["valor"]
        ):
            continue

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
                FALSE,
                :vencimento,
                TRUE
            )
        """, {
            "usuario_id": usuario_id,
            "mes": mes,
            "descricao": item["descricao"],
            "categoria": item["categoria"],
            "conta_id": item["conta_id"],
            "valor": float(item["valor"]),
            "vencimento": item["vencimento"]
        })

        criadas += 1

    return criadas


def listar_recorrencias(usuario_id):
    return buscar_todos("""
        SELECT DISTINCT
            d.descricao,
            d.categoria,
            d.valor,
            d.vencimento,
            COALESCE(c.nome, 'Sem conta') AS conta
        FROM despesas d
        LEFT JOIN contas c
            ON c.id = d.conta_id
        WHERE d.usuario_id = :usuario_id
          AND d.recorrente = TRUE
        ORDER BY d.descricao ASC
    """, {
        "usuario_id": usuario_id
    })


def tela_recorrencias(usuario_id, mes):
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

    total = sum(float(item["valor"]) for item in recorrencias)

    st.metric("Total mensal previsto em recorrências", fmt_moeda(total))

    st.divider()

    for item in recorrencias:
        with st.container(border=True):
            st.markdown(f"### {item['descricao']}")
            st.write(f"**Categoria:** {item['categoria']}")
            st.write(f"**Conta:** {item['conta']}")
            st.write(f"**Valor:** {fmt_moeda(item['valor'])}")
            st.write(f"**Vencimento original:** {item['vencimento']}")
