import streamlit as st
from database.neon_config import executar_sql, buscar_todos, buscar_um


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_tabela_faturas():
    executar_sql("""
        CREATE TABLE IF NOT EXISTS faturas (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL,
            cartao_id BIGINT NOT NULL,
            mes TEXT NOT NULL,
            valor NUMERIC(15,2) NOT NULL DEFAULT 0,
            paga BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT fk_faturas_cartao
                FOREIGN KEY (cartao_id)
                REFERENCES cartoes(id)
                ON DELETE CASCADE,
            CONSTRAINT uq_fatura_cartao_mes
                UNIQUE (usuario_id, cartao_id, mes)
        )
    """)


def listar_cartoes(usuario_id):
    return buscar_todos("""
        SELECT
            c.*,
            ct.nome AS conta_nome,
            COALESCE(ct.saldo, 0) AS conta_saldo
        FROM cartoes c
        LEFT JOIN contas ct
            ON ct.id = c.conta_id
        WHERE c.usuario_id = :usuario_id
          AND c.ativo = TRUE
        ORDER BY c.nome
    """, {
        "usuario_id": usuario_id
    })


def total_compras_cartao_mes(usuario_id, cartao_id, mes):
    resultado = buscar_um("""
        SELECT COALESCE(SUM(valor_parcela), 0) AS total
        FROM compras_cartao
        WHERE usuario_id = :usuario_id
          AND cartao_id = :cartao_id
          AND mes = :mes
    """, {
        "usuario_id": usuario_id,
        "cartao_id": cartao_id,
        "mes": mes
    })

    return float(resultado["total"] or 0)


def buscar_fatura(usuario_id, cartao_id, mes):
    return buscar_um("""
        SELECT *
        FROM faturas
        WHERE usuario_id = :usuario_id
          AND cartao_id = :cartao_id
          AND mes = :mes
        LIMIT 1
    """, {
        "usuario_id": usuario_id,
        "cartao_id": cartao_id,
        "mes": mes
    })


def gerar_ou_atualizar_fatura(usuario_id, cartao_id, mes, valor):
    fatura = buscar_fatura(usuario_id, cartao_id, mes)

    if fatura:
        if not fatura["paga"]:
            executar_sql("""
                UPDATE faturas
                SET valor = :valor
                WHERE id = :id
            """, {
                "valor": float(valor),
                "id": fatura["id"]
            })
    else:
        executar_sql("""
            INSERT INTO faturas (
                usuario_id, cartao_id, mes, valor, paga
            )
            VALUES (
                :usuario_id, :cartao_id, :mes, :valor, FALSE
            )
        """, {
            "usuario_id": usuario_id,
            "cartao_id": cartao_id,
            "mes": mes,
            "valor": float(valor)
        })


def pagar_fatura(usuario_id, cartao_id, mes):
    fatura = buscar_fatura(usuario_id, cartao_id, mes)

    if not fatura:
        return False, "Fatura não encontrada."

    if fatura["paga"]:
        return False, "Essa fatura já está paga."

    cartao = buscar_um("""
        SELECT
            c.*,
            ct.id AS conta_id_vinculada,
            ct.saldo AS conta_saldo
        FROM cartoes c
        LEFT JOIN contas ct
            ON ct.id = c.conta_id
        WHERE c.id = :cartao_id
          AND c.usuario_id = :usuario_id
        LIMIT 1
    """, {
        "cartao_id": cartao_id,
        "usuario_id": usuario_id
    })

    if not cartao:
        return False, "Cartão não encontrado."

    if not cartao["conta_id_vinculada"]:
        return False, "Cartão sem conta vinculada."

    valor = float(fatura["valor"])
    saldo = float(cartao["conta_saldo"] or 0)

    if saldo < valor:
        return False, "Saldo insuficiente."

    executar_sql("""
        UPDATE contas
        SET saldo = saldo - :valor
        WHERE id = :conta_id
    """, {
        "valor": valor,
        "conta_id": cartao["conta_id_vinculada"]
    })

    executar_sql("""
        UPDATE faturas
        SET paga = TRUE
        WHERE id = :fatura_id
    """, {
        "fatura_id": fatura["id"]
    })

    return True, "Fatura paga com sucesso!"


def reabrir_fatura(usuario_id, cartao_id, mes):
    fatura = buscar_fatura(usuario_id, cartao_id, mes)

    if not fatura or not fatura["paga"]:
        return False, "Não foi possível reabrir."

    cartao = buscar_um("""
        SELECT
            c.*,
            ct.id AS conta_id_vinculada
        FROM cartoes c
        LEFT JOIN contas ct
            ON ct.id = c.conta_id
        WHERE c.id = :cartao_id
          AND c.usuario_id = :usuario_id
        LIMIT 1
    """, {
        "cartao_id": cartao_id,
        "usuario_id": usuario_id
    })

    if not cartao:
        return False, "Cartão não encontrado."

    if not cartao["conta_id_vinculada"]:
        return False, "Conta não encontrada."

    executar_sql("""
        UPDATE contas
        SET saldo = saldo + :valor
        WHERE id = :conta_id
    """, {
        "valor": float(fatura["valor"]),
        "conta_id": cartao["conta_id_vinculada"]
    })

    executar_sql("""
        UPDATE faturas
        SET paga = FALSE
        WHERE id = :fatura_id
    """, {
        "fatura_id": fatura["id"]
    })

    return True, "Fatura reaberta!"


def listar_compras_fatura(usuario_id, cartao_id, mes):
    return buscar_todos("""
        SELECT *
        FROM compras_cartao
        WHERE usuario_id = :usuario_id
          AND cartao_id = :cartao_id
          AND mes = :mes
        ORDER BY id DESC
    """, {
        "usuario_id": usuario_id,
        "cartao_id": cartao_id,
        "mes": mes
    })


def tela_faturas(usuario_id, mes):
    garantir_tabela_faturas()

    st.subheader("🧾 Faturas do Cartão")

    cartoes = listar_cartoes(usuario_id)

    if not cartoes:
        st.warning("Antes de gerar faturas, cadastre um cartão na aba 💳 Cartões.")
        return

    total_geral = 0

    for cartao in cartoes:
        total_mes = total_compras_cartao_mes(usuario_id, cartao["id"], mes)
        gerar_ou_atualizar_fatura(usuario_id, cartao["id"], mes, total_mes)
        fatura = buscar_fatura(usuario_id, cartao["id"], mes)

        total_geral += total_mes
        status = "✅ Paga" if fatura and fatura["paga"] else "⏳ Pendente"

        with st.container(border=True):
            st.markdown(f"### 💳 {cartao['nome']}")
            st.write(f"**Mês:** {mes}")
            st.write(f"**Conta vinculada:** {cartao['conta_nome'] or 'Não vinculada'}")
            st.write(f"**Saldo da conta:** {fmt_moeda(cartao['conta_saldo'] or 0)}")
            st.write(f"**Valor da fatura:** {fmt_moeda(total_mes)}")
            st.write(f"**Status:** {status}")
            st.caption(f"Fecha dia {cartao['fechamento']} | Vence dia {cartao['vencimento']}")

            compras = listar_compras_fatura(usuario_id, cartao["id"], mes)

            with st.expander("Ver compras da fatura"):
                if not compras:
                    st.info("Nenhuma compra nesse cartão neste mês.")
                else:
                    for compra in compras:
                        parcelas = int(compra["parcelas"])
                        valor_parcela = float(compra["valor_parcela"])

                        st.markdown(f"**{compra['descricao']}**")
                        st.write(f"Categoria: {compra['categoria']}")
                        st.write(f"Valor total: {fmt_moeda(compra['valor_total'])}")
                        st.write(
                            f"Parcela: {compra['parcela_atual']}/{parcelas} "
                            f"• {fmt_moeda(valor_parcela)}"
                        )
                        st.divider()

            col1, col2 = st.columns(2)

            if fatura and not fatura["paga"]:
                if col1.button(
                    "💰 Pagar fatura",
                    key=f"pagar_fatura_{cartao['id']}",
                    use_container_width=True
                ):
                    ok, msg = pagar_fatura(usuario_id, cartao["id"], mes)

                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

                    st.rerun()

            if fatura and fatura["paga"]:
                if col2.button(
                    "↩️ Reabrir fatura",
                    key=f"reabrir_fatura_{cartao['id']}",
                    use_container_width=True
                ):
                    ok, msg = reabrir_fatura(usuario_id, cartao["id"], mes)

                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

                    st.rerun()

    st.divider()
    st.metric("Total geral de faturas no mês", fmt_moeda(total_geral))
