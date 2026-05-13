import streamlit as st
from utils.database import conectar


def criar_conta(usuario_id, nome, tipo, saldo):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO contas (usuario_id, nome, tipo, saldo)
    VALUES (?, ?, ?, ?)
    """, (usuario_id, nome, tipo, saldo))

    conn.commit()
    conn.close()


def listar_contas(usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM contas
    WHERE usuario_id = ?
    """, (usuario_id,))

    contas = cursor.fetchall()

    conn.close()

    return contas


def tela_contas(usuario_id):

    st.subheader("🏦 Contas Financeiras")

    with st.expander("➕ Nova conta"):

        nome = st.text_input("Nome da conta")

        tipo = st.selectbox(
            "Tipo",
            [
                "Conta corrente",
                "Carteira",
                "Poupança",
                "Investimento",
                "Dinheiro"
            ]
        )

        saldo = st.number_input(
            "Saldo inicial",
            min_value=0.0,
            step=0.01
        )

        if st.button("Criar conta"):

            criar_conta(
                usuario_id,
                nome,
                tipo,
                saldo
            )

            st.success("Conta criada com sucesso!")
            st.rerun()

    contas = listar_contas(usuario_id)

    if contas:

        cols = st.columns(3)

        for i, conta in enumerate(contas):

            with cols[i % 3]:

                st.markdown(f"""
                ### 💳 {conta['nome']}

                **Tipo:** {conta['tipo']}

                **Saldo:** R$ {conta['saldo']:,.2f}
                """)