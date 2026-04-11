import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="MetaFluxo Premium 📈", layout="wide", page_icon="📈")

# --- ESTILO CSS DEFINITIVO (FOCO EM VISIBILIDADE) ---
st.markdown("""
    <style>
    /* Fundo da página */
    .stApp { background-color: #f8fafc; }
    
    /* Barra lateral */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #0f172a 100%);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* CORREÇÃO DE VISIBILIDADE: Forçando texto ESCURO nos inputs */
    input, textarea, select {
        color: #0f172a !important; /* Azul quase preto */
        -webkit-text-fill-color: #0f172a !important;
    }
    
    /* Estilizando as caixas de texto para ficarem visíveis */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    
    /* Garantindo que o texto dentro do expander seja legível */
    .st-expanderContent {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    /* Cards de métricas */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 6px solid #3b82f6;
    }
    div[data-testid="stMetricLabel"] { color: #64748b !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] { color: #1e293b !important; }

    /* Botões */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("📈 MetaFluxo")
    u = st.text_input("Usuário", placeholder="Seu nome de usuário")
    p = st.text_input("Senha", type="password", placeholder="Sua senha")
    if st.button("Acessar Sistema"):
        if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = u
            st.rerun()
        else:
            st.error("Login ou senha incorretos.")
else:
    # --- INTERFACE ---
    with st.sidebar:
        st.title("📈 MetaFluxo")
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        mes = st.selectbox("Mês", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        
        lbl_renda = "Sua Renda (R$)" if not privacidade else "Renda (OCULTO)"
        renda = st.number_input(lbl_renda, value=3000.0, format="%.2f", step=1.0)
        
        lbl_meta = "Meta Investimento" if not privacidade else "Meta (OCULTO)"
        meta_inv = st.number_input(lbl_meta, value=1000.0, format="%.2f", step=1.0)
        
        st.divider()
        if st.button("🚪 Sair"):
            st.session_state['logged_in'] = False
            st.rerun()

    def fmt(valor):
        return "R$ *****" if privacidade else f"R$ {valor:,.2f}"

    if mes not in st.session_state.db: st.session_state.db[mes] = {"gastos": [], "investido": 0.0}
    d_mes = st.session_state.db[mes]

    # --- CÁLCULOS ---
    t_pago = sum(float(g['valor']) for g in d_mes['gastos'] if g['pago'])
    t_pend = sum(float(g['valor']) for g in d_mes['gastos'] if not g['pago'])
    inv_mes = float(d_mes.get('investido', 0.0))
    total_sonhos = sum(float(s['acumulado']) for s in st.session_state.db.get('metas_sonhos', []))
    saldo = renda - t_pago - t_pend - inv_mes

    st.title(f"📊 Dashboard {mes}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ PAGOS", fmt(t_pago))
    c2.metric("⏳ PENDENTES", fmt(t_pend))
    c3.metric("🚀 NOS SONHOS", fmt(total_sonhos))
    c4.metric("💰 SALDO LIVRE", fmt(saldo))

    st.divider()

    col_l, col_g = st.columns([1.5, 1])
    with col_l:
        st.subheader("📝 Gastos do Mês")
        if st.button("➕ Adicionar Bloco"):
            st.session_state.db[mes]["gastos"].append({"item": "Novo", "valor": 0.0, "pago": False, "cat": "🛠️ Outros"})
            st.rerun()
        
        with st.container(height=450):
            idx_del = None
            for i, g in enumerate(d_mes["gastos"]):
                with st.expander(f"📦 {g['item']} - {fmt(g['valor'])}", expanded=True):
                    ca1, ca2, ca3 = st.columns([2, 1, 1])
                    g["item"] = ca1.text_input("O que é?", g["item"], key=f"it_{mes}_{i}")
                    g["valor"] = ca2.number_input("Quanto?", value=float(g["valor"]), key=f"vl_{mes}_{i}", format="%.2f")
                    g["pago"] = ca3.checkbox("Pago?", value=g["pago"], key=f"ck_{mes}_{i}")
                    if st.button("🗑️ Deletar", key=f"del_{mes}_{i}"): idx_del = i
            if idx_del is not None:
                d_mes["gastos"].pop(idx_del)
                salvar_banco(st.session_state.db)
                st.rerun()

    with col_g:
        st.subheader("📊 Gráfico de Distribuição")
        labels = ["Pago", "Pendente", "Investido (Mês)", "Guardado Sonhos", "Saldo Livre"]
        valores = [t_pago, t_pend, inv_mes, total_sonhos, max(0, saldo)]
        
        df_p = pd.DataFrame({"Legenda": labels, "Valor": valores})
        df_p = df_p[df_p["Valor"] > 0]

        if not df_p.empty:
            fig = px.pie(df_p, values='Valor', names='Legenda', hole=0.6,
                         color='Legenda',
                         color_discrete_map={"Pago": "#2ecc71", "Pendente": "#e74c3c", "Investido (Mês)": "#f1c40f", "Guardado Sonhos": "#9b59b6", "Saldo Livre": "#3498db"})
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)

    # --- SONHOS ---
    st.divider()
    st.subheader("🚀 Meus Sonhos")
    s1, s2 = st.columns([1, 2])
    with s1:
        with st.form("f_sonho"):
            n_s = st.text_input("Novo Objetivo")
            v_alvo = st.number_input("Valor da Meta", min_value=0.0, format="%.2f")
            if st.form_submit_button("Cadastrar"):
                st.session_state.db['metas_sonhos'].append({"nome": n_s, "alvo": v_alvo, "acumulado": 0.0})
                salvar_banco(st.session_state.db)
                st.rerun()
    with s2:
        with st.container(height=300):
            idx_s_del = None
            for i, s in enumerate(st.session_state.db['metas_sonhos']):
                alvo, acum = float(s['alvo']), float(s['acumulado'])
                prog = min(acum / alvo, 1.0) if alvo > 0 else 0.0
                with st.expander(f"⭐ {s['nome']} - {prog*100:.1f}%"):
                    c_i, c_d, c_x = st.columns([2, 2, 0.5])
                    c_i.write(f"Guardado: {fmt(acum)}")
                    c_i.progress(prog)
                    v_dep = c_d.number_input(f"Somar em {s['nome']}", value=0.0, format="%.2f", key=f"d_{i}")
                    if c_d.button("Confirmar", key=f"b_{i}"):
                        s['acumulado'] += v_dep
                        salvar_banco(st.session_state.db)
                        st.rerun()
                    if c_x.button("🗑️", key=f"x_{i}"): idx_s_del = i
            if idx_s_del is not None:
                st.session_state.db['metas_sonhos'].pop(idx_s_del)
                salvar_banco(st.session_state.db)
                st.rerun()
    salvar_banco(st.session_state.db)
