import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="MetaFluxo 📈", layout="wide", page_icon="📈")

# --- BANCO DE DADOS ---
DB_FILE = "metafluxo_db.json"

def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: pass
    return {"users": {"admin": {"password": "123", "security_answer": "Murillo"}}, "metas_sonhos": [], "config": {"categorias": {"🏠 Moradia": "#3498db", "🍎 Alimentação": "#e67e22", "🚗 Transporte": "#9b59b6", "🎡 Lazer": "#f1c40f", "💊 Saúde": "#e74c3c", "🛠️ Outros": "#95a5a6"}}}

def salvar_banco(dados):
    with open(DB_FILE, "w") as f:
        json.dump(dados, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = carregar_banco()

# --- LOGIN SIMPLIFICADO ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("📈 MetaFluxo")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = u
            st.rerun()
else:
    # --- APP PRINCIPAL ---
    with st.sidebar:
        st.title("📈 MetaFluxo")
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        mes = st.selectbox("Mês", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        renda = st.number_input("Sua Renda (R$)", value=3000.0, format="%.2f")
        meta_inv = st.number_input("Meta de Investimento (R$)", value=1000.0, format="%.2f")
        if st.button("🚪 Sair"):
            st.session_state['logged_in'] = False
            st.rerun()

    def fmt(valor):
        return "R$ *****" if privacidade else f"R$ {valor:,.2f}"

    if mes not in st.session_state.db: st.session_state.db[mes] = {"gastos": [], "investido": 0.0}
    d_mes = st.session_state.db[mes]

    # --- CARDS ---
    t_pago = sum(float(g['valor']) for g in d_mes['gastos'] if g['pago'])
    t_pend = sum(float(g['valor']) for g in d_mes['gastos'] if not g['pago'])
    inv = float(d_mes.get('investido', 0.0))
    saldo = renda - t_pago - t_pend - inv

    st.title(f"📈 Painel de {mes}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Pago", fmt(t_pago))
    c2.metric("⏳ Pendente", fmt(t_pend))
    c3.metric("💰 Livre", fmt(saldo))
    prog_i = min(inv / meta_inv, 1.0) if meta_inv > 0 else 0.0
    c4.write(f"**🎯 Meta: {prog_i*100:.1f}%**")
    st.progress(prog_i)

    st.divider()

    # --- GASTOS ---
    col_l, col_g = st.columns([1.6, 1])
    with col_l:
        st.subheader("📝 Gastos")
        if st.button("➕ Novo Gasto"):
            st.session_state.db[mes]["gastos"].append({"item": "Novo", "valor": 0.0, "pago": False, "cat": "🛠️ Outros"})
            st.rerun()
        
        with st.container(height=400):
            idx_del = None
            for i, g in enumerate(d_mes["gastos"]):
                with st.expander(f"{g.get('cat', '🛠️')} {g['item']} - {fmt(g['valor'])}"):
                    ca1, ca2, ca3, ca4 = st.columns([2, 1.5, 1, 0.5])
                    g["item"] = ca1.text_input("Item", g["item"], key=f"it_{mes}_{i}")
                    g["valor"] = ca3.number_input("Valor", value=float(g["valor"]), key=f"vl_{mes}_{i}", format="%.2f")
                    g["pago"] = ca4.checkbox("Pago?", value=g["pago"], key=f"ck_{mes}_{i}")
                    if st.button("🗑️", key=f"del_{mes}_{i}"): idx_del = i
            if idx_del is not None:
                d_mes["gastos"].pop(idx_del)
                salvar_banco(st.session_state.db)
                st.rerun()

    with col_g:
        st.subheader("📊 Gráfico")
        n_inv = st.number_input("Investir agora:", value=float(inv), format="%.2f", key="n_inv")
        if n_inv != inv:
            d_mes["investido"] = n_inv
            st.rerun()
        
        df_p = pd.DataFrame({"Destino": ["Pago", "Pendente", "Investido", "Livre"], "Valor": [t_pago, t_pend, n_inv, max(0, saldo)]})
        fig = px.pie(df_p[df_p["Valor"] > 0], values='Valor', names='Destino', hole=0.5, color='Destino', color_discrete_map={"Pago": "#2ecc71", "Pendente": "#e74c3c", "Investido": "#f1c40f", "Livre": "#3498db"})
        st.plotly_chart(fig, use_container_width=True)

    # --- SONHOS COM BOTÃO DE SOMAR (DEPÓSITO) ---
    st.divider()
    st.subheader("🚀 Meus Sonhos (Objetivos)")
    if 'metas_sonhos' not in st.session_state.db: st.session_state.db['metas_sonhos'] = []
    
    s1, s2 = st.columns([1, 2])
    with s1:
        with st.form("f_sonho"):
            n_s = st.text_input("Nome do Sonho")
            v_alvo = st.number_input("Valor Total (Meta)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Criar Sonho"):
                st.session_state.db['metas_sonhos'].append({"nome": n_s, "alvo": v_alvo, "acumulado": 0.0})
                salvar_banco(st.session_state.db)
                st.rerun()

    with s2:
        with st.container(height=350):
            idx_s_del = None
            for i, s in enumerate(st.session_state.db['metas_sonhos']):
                alvo = float(s['alvo'])
                acum = float(s['acumulado'])
                prog = min(acum / alvo, 1.0) if alvo > 0 else 0.0
                
                with st.expander(f"⭐ {s['nome']} - {prog*100:.1f}%"):
                    c_info, c_deposito, c_del = st.columns([2, 2, 0.5])
                    c_info.write(f"Guardado: **{fmt(acum)}**")
                    c_info.write(f"Falta: **{fmt(max(0, alvo - acum))}**")
                    c_info.progress(prog)
                    
                    # AQUI ESTÁ A MÁGICA: Campo para somar valor novo
                    valor_deposito = c_deposito.number_input(f"Somar valor em {s['nome']}:", value=0.0, format="%.2f", key=f"dep_{i}")
                    if c_deposito.button(f"Confirmar Depósito", key=f"btn_dep_{i}"):
                        s['acumulado'] += valor_deposito
                        salvar_banco(st.session_state.db)
                        st.rerun()
                        
                    if c_del.button("🗑️", key=f"ds_{i}"): idx_s_del = i
            
            if idx_s_del is not None:
                st.session_state.db['metas_sonhos'].pop(idx_s_del)
                salvar_banco(st.session_state.db)
                st.rerun()

    salvar_banco(st.session_state.db)
