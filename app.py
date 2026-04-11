import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd
from PIL import Image

# --- CONFIGURAÇÃO VISUAL ---
# O ícone da aba do navegador (favicon) também usará o seu logo
try:
    img_logo = Image.open("logo.png")
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon=img_logo)
except:
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon="📈")

# --- ESTILO CSS DARK 2.0 (VISUAL PREMIUM) ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #020617 100%);
    }
    [data-testid="stSidebar"] * { color: #f1f5f9 !important; }

    /* Estilização dos campos de entrada */
    div[data-baseweb="input"] {
        background-color: #020617 !important;
        border: 2px solid #334155 !important;
        border-radius: 10px !important;
    }
    input {
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
        font-weight: bold !important;
    }

    /* Cards de métricas com efeito Glow */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
        border-left: 5px solid #60a5fa;
    }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: bold !important; text-transform: uppercase; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 28px !important; }

    /* Expanders (Blocos de Gastos) */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }
    
    /* Botões */
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100%;
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
    st.title("📈 MetaFlux Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Acessar Painel"):
        if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = u
            st.rerun()
        else: st.error("Acesso negado.")
else:
    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        # AQUI É ONDE O SEU LOGO APARECE
        try:
            st.image("logo.png", use_column_width=True)
        except:
            st.title("📈 METAFLUX")
            
        st.divider()
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        mes = st.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        
        # --- PRIVACIDADE BLINDADA ---
        if privacidade:
            st.text_input("🔐 RENDA (OCULTA)", value="******", disabled=True)
            st.text_input("🔐 META (OCULTA)", value="******", disabled=True)
            renda = 3000.0 # Valor padrão para cálculos internos
            meta_inv = 1000.0
        else:
            renda = st.number_input("Sua Renda (R$)", value=3000.0, format="%.2f")
            meta_inv = st.number_input("Meta Investimento (R$)", value=1000.0, format="%.2f")
        
        st.divider()
        if st.button("🚪 Sair"):
            st.session_state['logged_in'] = False
            st.rerun()

    def fmt(valor):
        return "R$ *****" if privacidade else f"R$ {valor:,.2f}"

    if mes not in st.session_state.db: st.session_state.db[mes] = {"gastos": [], "investido": 0.0}
    d_mes = st.session_state.db[mes]

    t_pago = sum(float(g['valor']) for g in d_mes['gastos'] if g['pago'])
    t_pend = sum(float(g['valor']) for g in d_mes['gastos'] if not g['pago'])
    inv_mes = float(d_mes.get('investido', 0.0))
    total_sonhos = sum(float(s['acumulado']) for s in st.session_state.db.get('metas_sonhos', []))
    saldo = renda - t_pago - t_pend - inv_mes

    st.title(f"🚀 Dashboard {mes}")
    
    # Cards métricos
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ PAGOS", fmt(t_pago))
    c2.metric("⏳ PENDENTES", fmt(t_pend))
    c3.metric("⭐ NOS SONHOS", fmt(total_sonhos))
    c4.metric("💰 SALDO LIVRE", fmt(saldo))

    st.divider()

    col_l, col_g = st.columns([1.4, 1])
    with col_l:
        st.subheader("📝 Gestão de Gastos")
        if st.button("➕ Novo Bloco"):
            st.session_state.db[mes]["gastos"].append({"item": "Novo", "valor": 0.0, "pago": False})
            st.rerun()
        
        with st.container(height=450):
            idx_del = None
            for i, g in enumerate(d_mes["gastos"]):
                with st.expander(f"📦 {g['item']} - {fmt(g['valor'])}"):
                    ca1, ca2, ca3 = st.columns([2, 1, 1])
                    g["item"] = ca1.text_input("Item", g["item"], key=f"it_{mes}_{i}")
                    
                    if privacidade:
                        ca2.text_input("Valor", value="****", disabled=True, key=f"vlp_{mes}_{i}")
                    else:
                        g["valor"] = ca2.number_input("Valor", value=float(g["valor"]), key=f"vl_{mes}_{i}", format="%.2f")
                    
                    g["pago"] = ca3.checkbox("Pago?", value=g["pago"], key=f"ck_{mes}_{i}")
                    if st.button("🗑️ Deletar", key=f"del_{mes}_{i}"): idx_del = i
            if idx_del is not None:
                d_mes["gastos"].pop(idx_del)
                salvar_banco(st.session_state.db)
                st.rerun()

    with col_g:
        st.subheader("📊 Raio-X Financeiro")
        labels = ["Pago", "Pendente", "Investido", "Sonhos", "Saldo Livre"]
        valores = [t_pago, t_pend, inv_mes, total_sonhos, max(0, saldo)]
        
        df_p = pd.DataFrame({"Legenda": labels, "Valor": valores})
        df_p = df_p[df_p["Valor"] > 0]

        if not df_p.empty:
            fig = px.pie(df_p, values='Valor', names='Legenda', hole=0.5,
                         color='Legenda',
                         color_discrete_map={"Pago": "#10b981", "Pendente": "#ef4444", "Investido": "#f59e0b", "Sonhos": "#8b5cf6", "Saldo Livre": "#3b82f6"})
            
            texto_info = 'percent+label' if not privacidade else 'none'
            fig.update_traces(textinfo=texto_info, pull=[0, 0, 0, 0, 0.1])
            fig.update_layout(showlegend=(not privacidade), margin=dict(t=0,b=0,l=0,r=0), 
                              paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)
            
    # --- SEÇÃO DE SONHOS ---
    st.divider()
    st.subheader("🚀 Meus Sonhos")
    s1, s2 = st.columns([1, 2])
    with s1:
        with st.form("f_sonho"):
            n_s = st.text_input("Qual o Sonho?")
            v_alvo = st.number_input("Meta (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Criar Objetivo"):
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
                    
                    if privacidade:
                        c_d.text_input("Aportar", value="****", disabled=True, key=f"dp_{i}")
                    else:
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
