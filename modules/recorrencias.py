import calendar
from datetime import date
from decimal import Decimal

import streamlit as st
from sqlalchemy import text
from database.neon_config import buscar_todos, transacao


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _data_vencimento(valor):
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


def _chave_modelo(item):
    return (
        item["descricao"], item["categoria"], item["conta_id"],
        Decimal(str(item["valor"]))
    )


def _modelos_unicos(registros):
    # Cada parcela mensal gerada também é recorrente. Agrupar pela identidade
    # da despesa impede que essas cópias se tornem novos modelos.
    modelos = {}
    for item in registros:
        chave = _chave_modelo(item)
        if chave not in modelos:
            modelos[chave] = item
        else:
            atual = modelos[chave]
            if _data_vencimento(item["vencimento"]) < _data_vencimento(atual["vencimento"]):
                modelos[chave] = item
    return sorted(modelos.values(), key=lambda item: item["descricao"].casefold())


def listar_modelos_recorrentes(usuario_id):
    registros = buscar_todos("""
        SELECT descricao, categoria, conta_id, valor, vencimento
        FROM despesas
        WHERE usuario_id = :usuario_id AND recorrente = TRUE
          AND vencimento IS NOT NULL
        ORDER BY vencimento ASC, id ASC
    """, {"usuario_id": usuario_id})
    return _modelos_unicos(registros)


def despesa_ja_existe(usuario_id, mes, descricao, categoria, conta_id, valor):
    from database.neon_config import buscar_um
    return buscar_um("""
        SELECT id FROM despesas
        WHERE usuario_id = :usuario_id AND mes = :mes
          AND descricao = :descricao AND categoria = :categoria
          AND conta_id IS NOT DISTINCT FROM :conta_id AND valor = :valor
        LIMIT 1
    """, {
        "usuario_id": usuario_id, "mes": mes, "descricao": descricao,
        "categoria": categoria, "conta_id": conta_id, "valor": valor
    }) is not None


MESES_PT = ("janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")

def normalizar_mes(mes):
    texto_mes = str(mes).strip()
    if texto_mes.casefold() in MESES_PT:
        return f"{date.today().year}-{MESES_PT.index(texto_mes.casefold()) + 1:02d}"
    try:
        ano, numero_mes = map(int, texto_mes.split("-"))
        if len(texto_mes) == 7 and 1 <= ano <= 9999 and 1 <= numero_mes <= 12:
            return f"{ano:04d}-{numero_mes:02d}"
    except (TypeError, ValueError):
        pass
    raise ValueError("Selecione um mês válido.")

def gerar_recorrencias(usuario_id, mes):
    mes = normalizar_mes(mes)
    ano, numero_mes = map(int, mes.split("-"))

    criadas = 0
    # A verificação e a inserção ocorrem na mesma transação. O bloqueio por
    # usuário e mês impede duas gerações simultâneas de criar duplicatas.
    with transacao() as conexao:
        conexao.execute(text("SELECT pg_advisory_xact_lock(:usuario_id, :mes_num)"), {
            "usuario_id": int(usuario_id), "mes_num": ano * 100 + numero_mes
        })
        registros = conexao.execute(text("""
            SELECT descricao, categoria, conta_id, valor, vencimento
            FROM despesas
            WHERE usuario_id = :usuario_id AND recorrente = TRUE
              AND vencimento IS NOT NULL
            ORDER BY vencimento ASC, id ASC
        """), {"usuario_id": usuario_id}).mappings().all()

        for item in _modelos_unicos(registros):
            original = _data_vencimento(item["vencimento"])
            # Não gerar uma despesa em mês anterior ao seu primeiro vencimento.
            if (ano, numero_mes) < (original.year, original.month):
                continue
            dia = min(original.day, calendar.monthrange(ano, numero_mes)[1])
            vencimento = date(ano, numero_mes, dia)
            parametros = {
                "usuario_id": usuario_id, "mes": mes,
                "descricao": item["descricao"], "categoria": item["categoria"],
                "conta_id": item["conta_id"], "valor": item["valor"],
                "vencimento": vencimento
            }
            existe = conexao.execute(text("""
                SELECT id FROM despesas
                WHERE usuario_id = :usuario_id AND mes = :mes
                  AND descricao = :descricao AND categoria = :categoria
                  AND conta_id IS NOT DISTINCT FROM :conta_id AND valor = :valor
                LIMIT 1
            """), parametros).first()
            if existe:
                continue
            conexao.execute(text("""
                INSERT INTO despesas (
                    usuario_id, mes, descricao, categoria, conta_id,
                    valor, paga, vencimento, recorrente
                ) VALUES (
                    :usuario_id, :mes, :descricao, :categoria, :conta_id,
                    :valor, FALSE, :vencimento, TRUE
                )
            """), parametros)
            criadas += 1
    return criadas


def listar_recorrencias(usuario_id):
    registros = buscar_todos("""
        SELECT d.descricao, d.categoria, d.conta_id, d.valor,
               d.vencimento, COALESCE(c.nome, 'Sem conta') AS conta
        FROM despesas d
        LEFT JOIN contas c ON c.id = d.conta_id AND c.usuario_id = d.usuario_id
        WHERE d.usuario_id = :usuario_id AND d.recorrente = TRUE
          AND d.vencimento IS NOT NULL
        ORDER BY d.vencimento ASC, d.id ASC
    """, {"usuario_id": usuario_id})
    return _modelos_unicos(registros)


def tela_recorrencias(usuario_id, mes):
    mes = normalizar_mes(mes)
    st.subheader("📅 Recorrências")
    st.info("As recorrências são criadas a partir das despesas marcadas como recorrentes na aba 💳 Despesas.")
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🔄 Gerar recorrências deste mês", use_container_width=True):
            try:
                criadas = gerar_recorrencias(usuario_id, mes)
            except (ValueError, Exception) as erro:
                st.error(f"Não foi possível gerar as recorrências: {erro}")
            else:
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
    total = sum((Decimal(str(item["valor"])) for item in recorrencias), Decimal("0"))
    st.metric("Total mensal previsto em recorrências", fmt_moeda(total))
    st.divider()
    for item in recorrencias:
        with st.container(border=True):
            st.markdown(f"### {item['descricao']}")
            st.write(f"**Categoria:** {item['categoria']}")
            st.write(f"**Conta:** {item['conta']}")
            st.write(f"**Valor:** {fmt_moeda(item['valor'])}")
            st.write(f"**Vencimento original:** {item['vencimento']}")
