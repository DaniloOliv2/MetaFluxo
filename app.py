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
            try:
                return json.load(f)
            except:
                pass
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
    user_atual = st.session_state['current_user']
    
    with st.sidebar:
        st.title("📈 MetaFluxo")
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        mes = st.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        # CORREÇÃO: Permitindo valores altos na Renda e Metas
        renda = st.number_input("Sua Renda (R$)", value=3000.0, step=100.0, format="%.2f")
        meta_inv = st.number_input("Meta de Investimento (R$)", value=1000.0, step=50.0, format="%.2f")
        st.divider()
        if st.button("🚪 Sair"):
            st.session_state['logged_in'] = False
            st.rerun()

    def fmt(valor):
        return "R$ *****" if privacidade else f"R$ {valor:,.2f}"

    if mes not in st.session_state.db:
        st.session_state.db[mes] = {"gastos": [], "investido": 0.0}
    dados_mes = st.session_state.db[mes]

    st.title(f"📈 Painel de {mes}")
    
    # --- CÁLCULOS TOTAIS ---
    total_pago = sum(float(g['valor']) for g in dados_mes['gastos'] if g['pago'])
    total_pendente = sum(float(g['valor']) for g in dados_mes['gastos'] if not g['pago'])
    investido = float(dados_mes.get('investido', 0.0))
    saldo_livre = renda - total_pago - total_pendente - investido

    # --- CARDS DE INDICADORES ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Já Pago", fmt(total_pago))
    c2.metric("⏳ Pendente", fmt(total_pendente))
    c3.metric("💰 Saldo Livre", fmt(saldo_livre))
    
    prog_inv = min(investido / meta_inv, 1.0) if meta_inv > 0 else 0.0
    c4.write(f"**🎯 Meta: {prog_inv*100:.1f}%**")
    st.progress(prog_inv)

    st.divider()

    col_lista, col_graf = st.columns([1.6, 1])

    with col_lista:
        st.subheader("📝 Gestão de Gastos")
        f1, f2 = st.columns([1, 1])
        filtro = f1.radio("Ver:", ["Todos", "Pendentes", "Pagos"], horizontal=True)
        if f2.button("➕ Adicionar Bloco"):
            st.session_state.db[mes]["gastos"].append({"item": "Novo", "valor": 0.0, "pago": False, "cat": "🛠️ Outros"})
            st.rerun()

        categorias_lista = list(st.session_state.db["config"]["categorias"].keys())
        
        with st.container(height=450):
            idx_del = None
            for i, gasto in enumerate(dados_mes["gastos"]):
                if filtro == "Pendentes" and gasto["pago"]: continue
                if filtro == "Pagos" and not gasto["pago"]: continue
                
                with st.expander(f"{gasto.get('cat', '🛠️')} {gasto['item']} - {fmt(gasto['valor'])}"):
                    ca1, ca2, ca3, ca4 = st.columns([2, 1.5, 1, 0.5])
                    gasto["item"] = ca1.text_input("Item", gasto["item"], key=f"it_{mes}_{i}")
                    gasto["cat"] = ca2.selectbox("Cat", categorias_lista, index=categorias_lista.index(gasto.get("cat", "🛠️ Outros")), key=f"ct_{mes}_{i}")
                    # CORREÇÃO: Valor sem limite baixo
                    gasto["valor"] = ca3.number_input("Valor", value=float(gasto["valor"]), key=f"vl_{mes}_{i}", format="%.2f")
                    gasto["pago"] = ca4.checkbox("Pago?", value=gasto["pago"], key=f"ck_{mes}_{i}")
                    if st.button("🗑️", key=f"del_{mes}_{i}"): idx_del = i
            
            if idx_del is not None:
                dados_mes["gastos"].pop(idx_del)
                salvar_banco(st.session_state.db)
                st.rerun()

    with col_graf:
        st.subheader("📊 Distribuição Total")
        # CORREÇÃO: Valor investido aceitando grandes quantias
        novo_inv = st.number_input("Valor Investido este mês:", value=float(investido), step=50.0, key="input_inv_total", format="%.2f")
        if novo_inv != investido:
            dados_mes["investido"] = novo_inv
            st.rerun()

        data = {
            "Destino": ["Pago", "Pendente", "Investido", "Saldo Livre"],
            "Valor": [total_pago, total_pendente, novo_inv, max(0, saldo_livre)]
        }
        df_p = pd.DataFrame(data)
        df_p = df_p[df_p["Valor"] > 0]

        if not df_p.empty:
            fig = px.pie(df_p, values='Valor', names='Destino', hole=0.5,
                         color='Destino',
                         color_discrete_map={"Pago": "#2ecc71", "Pendente": "#e74c3c", "Investido": "#f1c40f", "Saldo Livre": "#3498db"})
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    # --- SEÇÃO DE SONHOS (COM ROLAGEM E VALORES ALTOS) ---
    st.divider()
    st.subheader("🚀 Meus Sonhos e Objetivos")
    if 'metas_sonhos' not in st.session_state.db: st.session_state.db['metas_sonhos'] = []
    
    s_col1, s_col2 = st.columns([1, 2])
    with s_col1:
        with st.form("form_sonho"):
            n_s = st.text_input("Qual o seu sonho? (Ex: Terreno)")
            # CORREÇÃO: Valor alvo agora aceita 40.000,00 ou mais
            v_s = st.number_input("Quanto custa no total?", min_value=0.0, step=100.0, format="%.2f")
            if st.form_submit_button("Adicionar Objetivo"):
                st.session_state.db['metas_sonhos'].append({"nome": n_s, "alvo": v_s, "acumulado": 0.0})
                salvar_banco(st.session_state.db)
                st.rerun()
    
    with s_col2:
        # CORREÇÃO: Adicionada Janela de Rolagem para os Sonhos
        with st.container(height=350):
            idx_sonho_del = None
            for i, s in enumerate(st.session_state.db['metas_sonhos']):
                p = min(s['acumulado'] / s['alvo'], 1.0) if s['alvo'] > 0 else 0.0
                
                with st.expander(f"⭐ {s['nome']} - {p*100:.1f}%"):
                    col_info, col_aporta, col_del = st.columns([3, 2, 0.5])
                    col_info.write(f"Progresso: **{fmt(s['acumulado'])}** de **{fmt(s['alvo'])}**")
                    col_info.progress(p)
                    # CORREÇÃO: Aporte aceitando valores altos
                    s['acumulado'] = col_aporta.number_input(f"Aportar em {s['nome']}", value=float(s['acumulado']), key=f"snk_{i}", format="%.2f")
                    if col_del.button("🗑️", key=f"del_sonho_{i}"):
                        idx_sonho_del = i
            
            if idx_sonho_del is not None:
                st.session_state.db['metas_sonhos'].pop(idx_sonho_del)
                salvar_banco(st.session_state.db)
                st.rerun()

    salvar_banco(st.session_state.db)
