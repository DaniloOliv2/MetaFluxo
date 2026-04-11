import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd
from PIL import Image

# --- CONFIGURAÇÃO VISUAL ---
try:
    img_favicon = Image.open("favicon.jpg")
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon=img_favicon)
except:
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon="📈")

# --- ESTILO CSS DARK PRO ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 20px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #020617 100%);
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] * { color: #f1f5f9 !important; }

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

    div[data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
        border-left: 5px solid #60a5fa;
    }
    
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #3b82f6 , #2ecc71);
    }

    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        width: 100%;
        border: none !important;
    }
    
    /* Links de rodapé do login */
    .login-footer {
        text-align: center;
        margin-top: 15px;
        font-size: 0.9rem;
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

# --- ESTADOS DE TELA ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login' # login, signup, recover

# --- FUNÇÕES DE NAVEGAÇÃO ---
def mudar_modo(modo):
    st.session_state['auth_mode'] = modo
    st.rerun()

# --- TELA DE AUTENTICAÇÃO ---
if not st.session_state['logged_in']:
    col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
    
    with col_l2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        try: st.image("logo.png", width=180)
        except: st.title("📈 MetaFlux")
        
        # MODO LOGIN
        if st.session_state['auth_mode'] == 'login':
            st.subheader("Login")
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.button("Acessar Painel"):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else: st.error("Dados incorretos.")
            
            st.markdown('<div class="login-footer">', unsafe_allow_html=True)
            if st.button("Não tem conta? Cadastre-se", key="go_signup"): mudar_modo('signup')
            if st.button("Esqueci minha senha", key="go_recover"): mudar_modo('recover')
            st.markdown('</div>', unsafe_allow_html=True)

        # MODO CADASTRO
        elif st.session_state['auth_mode'] == 'signup':
            st.subheader("Novo Cadastro")
            new_u = st.text_input("Escolha um Usuário")
            new_p = st.text_input("Escolha uma Senha", type="password")
            new_s = st.text_input("Resposta de Segurança (Nome do seu filho?)")
            
            if st.button("Criar Conta"):
                if new_u and new_p and new_s:
                    st.session_state.db["users"][new_u] = {"password": new_p, "security_answer": new_s}
                    salvar_banco(st.session_state.db)
                    st.success("Conta criada! Pode logar.")
                    mudar_modo('login')
                else: st.warning("Preencha todos os campos.")
            if st.button("Voltar ao Login"): mudar_modo('login')

        # MODO RECUPERAÇÃO
        elif st.session_state['auth_mode'] == 'recover':
            st.subheader("Recuperar Senha")
            rec_u = st.text_input("Informe seu Usuário")
            if rec_u in st.session_state.db["users"]:
                ans = st.text_input("Pergunta: Qual o nome do seu filho?")
                if st.button("Revelar Senha"):
                    if ans.lower() == st.session_state.db["users"][rec_u]["security_answer"].lower():
                        st.info(f"Sua senha é: {st.session_state.db['users'][rec_u]['password']}")
                    else: st.error("Resposta incorreta.")
            else: st.warning("Usuário não encontrado.")
            if st.button("Voltar ao Login"): mudar_modo('login')
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- INTERFACE PRINCIPAL (LOGADA) ---
    with st.sidebar:
        try: st.image("logo.png", use_column_width=True)
        except: st.title("📈 METAFLUX")
            
        st.divider()
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        mes = st.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        
        if privacidade:
            st.text_input("🔐 RENDA (OCULTA)", value="******", disabled=True)
            st.text_input("🔐 META (OCULTA)", value="******", disabled=True)
            renda, meta_inv = 3000.0, 1000.0
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

    st.title(f"🚀 Dashboard de {mes}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ PAGOS", fmt(t_pago))
    c2.metric("⏳ PENDENTES", fmt(t_pend))
    c3.metric("🚀 MEUS SONHOS", fmt(total_sonhos)) 
    c4.metric("💰 SALDO LIVRE", fmt(saldo))

    st.write("")
    prog_meta = min(inv_mes / meta_inv, 1.0) if meta_inv > 0 else 0.0
    cp1, cp2 = st.columns([3, 1])
    cp1.markdown(f"**Meta de Investimento ({prog_meta*100:.1f}%)**")
    cp2.markdown(f"<div style='text-align:right'>Faltam: {fmt(max(0, meta_inv - inv_mes))}</div>", unsafe_allow_html=True)
    st.progress(prog_meta)
    st.divider()

    col_l, col_g = st.columns([1.4, 1])
    with col_l:
        st.subheader("📝 Lançamentos")
        new_inv = st.number_input("Investimento do Mês (R$)", value=inv_mes, format="%.2f")
        if new_inv != inv_mes:
            st.session_state.db[mes]['investido'] = new_inv
            salvar_banco(st.session_state.db)
            st.rerun()

        if st.button("➕ Novo Gasto"):
            st.session_state.db[mes]["gastos"].append({"item": "Novo", "valor": 0.0, "pago": False})
            st.rerun()
        
        with st.container(height=350):
            idx_del = None
            for i, g in enumerate(d_mes["gastos"]):
                with st.expander(f"📦 {g['item']} - {fmt(g['valor'])}", expanded=True):
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
            t_inf = 'percent+label' if not privacidade else 'none'
            fig.update_traces(textinfo=t_inf, pull=[0, 0, 0, 0, 0.1])
            fig.update_layout(showlegend=(not privacidade), margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)
            
    st.divider()
    st.subheader("🚀 Meus Sonhos") 
    s1, s2 = st.columns([1, 2])
    with s1:
        with st.form("f_sonho"):
            n_s = st.text_input("Qual o Sonho?")
            v_alvo = st.number_input("Meta (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Criar"):
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
