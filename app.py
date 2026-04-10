import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd
from io import BytesIO

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="MetaFluxo 📈", layout="wide", page_icon="📈")

# --- BANCO DE DADOS ---
DB_FILE = "metafluxo_db.json"

def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {
        "users": {"admin": {"password": "123", "security_answer": "Murillo"}},
        "metas_sonhos": [],
        "config": {"categorias": {"🏠 Moradia": "#3498db", "🍎 Alimentação": "#e67e22", "🚗 Transporte": "#9b59b6", "🎡 Lazer": "#f1c40f", "💊 Saúde": "#e74c3c", "🛠️ Outros": "#95a5a6"}}
    }

def salvar_banco(dados):
    with open(DB_FILE, "w") as f:
        json.dump(dados, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = carregar_banco()

# --- LÓGICA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("📈 MetaFluxo")
    aba_login, aba_criar = st.tabs(["Acessar Login", "Criar Nova Conta"])
    
    with aba_login:
        user = st.text_input("Usuário", key="u_log")
        passw = st.text_input("Senha", type="password", key="p_log")
        if st.button("Entrar"):
            if user in st.session_state.db["users"] and st.session_state.db["users"][user]["password"] == passw:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = user
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
else:
    # --- INTERFACE LOGADA ---
    user_atual = st.session_state['current_user']
    
    # --- SIDEBAR COM MODO PRIVACIDADE ---
    with st.sidebar:
        st.title("📈 MetaFluxo")
        st.write(f"Olá, **{user_atual}**")
        
        privacidade = st.toggle("👁️ Modo Privacidade", help="Esconde os valores numéricos")
        
        st.divider()
        mes = st.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        renda = st.number_input("Sua Renda (R$)", value=3000.0)
        meta_inv = st.number_input("Meta de Investimento (R$)", value=1000.0)
        
        st.divider()
        if st.button("🚪 Sair"):
            st.session_state['logged_in'] = False
            st.rerun()

    # Função para formatar valores (Modo Privacidade)
    def fmt(valor):
        return "R$ *****" if privacidade else f"R$ {valor:,.2f}"

    if mes not in st.session_state.db:
        st.session_state.db[mes] = {"gastos": [], "investido": 0.0}
    dados_mes = st.session_state.db[mes]

    # --- DASHBOARD DE INDICADORES (CARDS) ---
    st.title(f"📈 Painel de {mes}")
    
    # Cálculos Prévios
    total_pago = sum(g['valor'] for g in dados_mes['gastos'] if g['pago'])
    total_pendente = sum(g['valor'] for g in dados_mes['gastos'] if not g['pago'])
    investido = dados_mes['investido']
    saldo_livre = renda - total_pago - total_pendente - investido

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Já Pago", fmt(total_pago))
    c2.metric("⏳ Pendente", fmt(total_pendente), delta_color="inverse")
    c3.metric("💰 Saldo Livre", fmt(saldo_livre))
    
    # Meta de Investimento
    progresso_inv = min(investido / meta_inv, 1.0) if meta_inv > 0 else 0.0
    c4.write(f"**🎯 Meta Investimento: {progresso_inv*100:.1f}%**")
    st.progress(progresso_inv)

    st.divider()

    # --- SEÇÃO CENTRAL: GASTOS E METAS ---
    col_lista, col_metas = st.columns([1.6, 1])

    with col_lista:
        tab_gastos, tab_config = st.tabs(["📝 Meus Gastos", "⚙️ Configurar Categorias"])
        
        with tab_gastos:
            f1, f2 = st.columns([1, 1])
            filtro = f1.radio("Filtro:", ["Todos", "Pendentes", "Pagos"], horizontal=True)
            if f2.button("➕ Novo Bloco"):
                st.session_state.db[mes]["gastos"].append({"item": "Novo", "valor": 0.0, "pago": False, "cat": "🛠️ Outros"})

            categorias_lista = list(st.session_state.db["config"]["categorias"].keys())
            
            with st.container(height=400):
                idx_del = None
                for i, gasto in enumerate(dados_mes["gastos"]):
                    if filtro == "Pendentes" and gasto["pago"]: continue
                    if filtro == "Pagos" and not gasto["pago"]: continue
                    
                    with st.expander(f"{gasto.get('cat', '🛠️')} {gasto['item']} - {fmt(gasto['valor'])}"):
                        ca1, ca2, ca3, ca4 = st.columns([2, 1.5, 1, 0.5])
                        gasto["item"] = ca1.text_input("Item", gasto["item"], key=f"it_{mes}_{i}")
                        gasto["cat"] = ca2.selectbox("Cat", categorias_lista, index=categorias_lista.index(gasto.get("cat", "🛠️ Outros")), key=f"ct_{mes}_{i}")
                        gasto["valor"] = ca3.number_input("Valor", value=float(gasto["valor"]), key=f"vl_{mes}_{i}")
                        gasto["pago"] = ca4.checkbox("P?", value=gasto["pago"], key=f"ck_{mes}_{i}")
                        if st.button("🗑️", key=f"del_{mes}_{i}"): idx_del = i
                
                if idx_del is not None:
                    dados_mes["gastos"].pop(idx_del)
                    salvar_banco(st.session_state.db)
                    st.rerun()

        with tab_config:
            st.write("Adicione novas categorias ou mude ícones aqui (Em breve)")

    with col_metas:
        st.subheader("📊 Gráfico e Exportação")
        
        # Gráfico
        df_pizza = pd.DataFrame({
            "Destino": ["Pago", "Pendente", "Investido", "Livre"],
            "Valor": [total_pago, total_pendente, investido, max(0, saldo_livre)]
        })
        fig = px.pie(df_pizza[df_pizza["Valor"] > 0], values='Valor', names='Destino', hole=0.5,
                     color='Destino', color_discrete_map={"Pago": "#2ecc71", "Pendente": "#e74c3c", "Investido": "#f1c40f", "Saldo Livre": "#3498db"})
        st.plotly_chart(fig, use_container_width=True)

        # BOTÃO EXPORTAR EXCEL
        if st.button("📥 Baixar Relatório Mensal (Excel)"):
            df_export = pd.DataFrame(dados_mes["gastos"])
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Gastos')
            st.download_button(label="Clique para baixar o arquivo", data=output.getvalue(), file_name=f"MetaFluxo_{mes}.xlsx")

    # --- SEÇÃO DE METAS/SONHOS (NOVIDADE) ---
    st.divider()
    st.subheader("🚀 Meus Sonhos e Objetivos")
    if 'metas_sonhos' not in st.session_state.db: st.session_state.db['metas_sonhos'] = []
    
    sm1, sm2 = st.columns([1, 2])
    with sm1:
        with st.form("novo_sonho"):
            nome_sonho = st.text_input("Qual seu sonho?")
            valor_alvo = st.number_input("Quanto custa?", min_value=1.0)
            if st.form_submit_button("Cadastrar Objetivo"):
                st.session_state.db['metas_sonhos'].append({"nome": nome_sonho, "alvo": valor_alvo, "acumulado": 0.0})
                salvar_banco(st.session_state.db)
                st.rerun()

    with sm2:
        for s in st.session_state.db['metas_sonhos']:
            prog = min(s['acumulado'] / s['alvo'], 1.0)
            col_s1, col_s2 = st.columns([3, 1])
            col_s1.write(f"**{s['nome']}** - {fmt(s['acumulado'])} de {fmt(s['alvo'])}")
            col_s1.progress(prog)
            s['acumulado'] = col_s2.number_input("Aportar", value=float(s['acumulado']), key=f"sn_{s['nome']}")

    salvar_banco(st.session_state.db)
