import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd
from PIL import Image
import time

# --- CONFIGURAÇÃO VISUAL (Favicon e Título) ---
try:
    # Mantemos o favicon na aba para identificação
    img_favicon = Image.open("favicon.jpg")
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon=img_favicon)
except:
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon="📈")

# --- ESTILO CSS AVANÇADO (ESTILO CARD CENTRALIZADO) ---
st.markdown("""
    <style>
    /* Fundo Infinito com Degradê Dark */
    .stApp { 
        background-color: #020617;
        background-image: radial-gradient(circle at top right, #1e3a8a, #020617);
    }
    
    /* O Cartão de Login (Baseado no seu modelo) */
    .login-card {
        background-color: #1e293b;
        padding: 45px;
        border-radius: 24px;
        border: 1px solid #334155;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        text-align: center;
        max-width: 400px;
        margin: auto;
    }

    /* Ajuste da Barra Lateral (Mantenho o gradiente) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #020617 100%);
    }
    
    /* Inputs Estilizados - Estilo Moderno */
    div[data-baseweb="input"] {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        min-height: 45px !important;
    }
    
    input { 
        color: #f1f5f9 !important; 
        font-size: 1rem !important;
    }

    /* Botão ACESSAR PAINEL */
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        height: 50px !important;
        width: 100% !important;
        border: none !important;
        margin-top: 15px;
        transition: 0.4s;
    }
    .stButton>button:hover {
        background-color: #3b82f6 !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }

    /* Opções de Login (Lembrar/Esqueci) */
    .login-options {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
        font-size: 0.85rem;
        color: #94a3b8;
    }
    
    /* Links de Rodapé do Card */
    .link-footer {
        margin-top: 25px;
        font-size: 0.85rem;
    }
    .link-footer button {
        background: none !important;
        border: none !important;
        color: #94a3b8 !important;
        text-decoration: none !important;
    }
    .link-footer button:hover {
        color: #f1f5f9 !important;
    }
    
    /* Direitos Autorais */
    .copyright {
        margin-top: 30px;
        font-size: 0.75rem;
        color: #475569;
        text-align: center;
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

# --- ESTADOS DE SESSÃO ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'
if 'error_msg' not in st.session_state: st.session_state['error_msg'] = False

# --- TELA DE AUTENTICAÇÃO ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1, 1.8, 1])
    
    with center_col:
        st.write("") # Espaçadores verticais
        st.write("")
        
        # --- MODO LOGIN ---
        if st.session_state['auth_mode'] == 'login':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            
            # Título METAFLUX em texto, sem logo
            st.markdown("<h1 style='text-align: center; color: #60a5fa; font-family: sans-serif; font-weight: 800; margin-bottom: 30px;'>METAFLUX</h1>", unsafe_allow_html=True)
            
            u = st.text_input("Usuário", placeholder="Seu usuário", key="u_login")
            p = st.text_input("Senha", type="password", placeholder="Sua senha", key="p_login")
            
            # Opções de Login (Lembrar/Esqueci)
            col_opt1, col_opt2 = st.columns([1, 1])
            with col_opt1:
                st.checkbox("Lembrar senha", key="remember_me")
            with col_opt2:
                # Botão de link para recuperação
                if st.button("Esqueceu sua senha?", key="go_recover_link"):
                    st.session_state['auth_mode'] = 'recover'
                    st.rerun()
            
            if st.button("ACESSAR PAINEL"):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else:
                    st.session_state['error_msg'] = True
                    st.rerun()
            
            # Inteligência de Erro (Some após 5s)
            if st.session_state['error_msg']:
                st.error("Dados incorretos!")
                time.sleep(5)
                st.session_state['error_msg'] = False
                st.rerun()

            # Rodapé do Card
            st.markdown('<div class="link-footer">', unsafe_allow_html=True)
            if st.button("Não tem conta? Cadastre-se aqui", key="go_signup_link"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Direitos Autorais
            st.markdown('<div class="copyright">© 2026 MetaFlux. Todos os direitos reservados.</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

        # --- MODO CADASTRO ---
        elif st.session_state['auth_mode'] == 'signup':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Nova Conta")
            new_u = st.text_input("Escolha um Usuário")
            new_p = st.text_input("Escolha uma Senha", type="password")
            new_s = st.text_input("Pergunta: Nome do filho?")
            if st.button("FINALIZAR CADASTRO"):
                if new_u and new_p and new_s:
                    st.session_state.db["users"][new_u] = {"password": new_p, "security_answer": new_s}
                    salvar_banco(st.session_state.db)
                    st.success("Conta criada com sucesso!")
                    time.sleep(2)
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()
            if st.button("Voltar ao Login"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # --- MODO RECUPERAÇÃO ---
        elif st.session_state['auth_mode'] == 'recover':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Recuperação")
            rec_u = st.text_input("Seu usuário")
            if rec_u in st.session_state.db["users"]:
                ans = st.text_input("Nome do filho?")
                if st.button("REVELAR SENHA"):
                    if ans.lower() == st.session_state.db["users"][rec_u]["security_answer"].lower():
                        st.info(f"Sua senha é: {st.session_state.db['users'][rec_u]['password']}")
            if st.button("Voltar ao Login"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- INTERFACE LOGADA ---
    with st.sidebar:
        try:
            # Mantemos o logo na sidebar para identificação do app logado
            st.image("logo.png", use_column_width=True)
        except:
            st.title("📈 METAFLUX")
        st.divider()
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        mes = st.selectbox("Mês", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        
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

    st.title(f"🚀 Dashboard {mes}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ PAGOS", fmt(t_pago))
    c2.metric("⏳ PENDENTES", fmt(t_pend))
    c3.metric("🚀 MEUS SONHOS", fmt(total_sonhos)) 
    c4.metric("💰 LIVRE", fmt(saldo))

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
        new_inv = st.number_input("Investido no Mês (R$)", value=inv_mes, format="%.2f")
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
        st.subheader("📊 Gráfico")
        labels = ["Pago", "Pendente", "Investido", "Sonhos", "Saldo Livre"]
        valores = [t_pago, t_pend, inv_mes, total_sonhos, max(0, saldo)]
        df_p = pd.DataFrame({"Legenda": labels, "Valor": valores})
        df_p = df_p[df_p["Valor"] > 0]

        if not df_p.empty:
            fig = px.pie(df_p, values='Valor', names='Legenda', hole=0.5, color='Legenda', color_discrete_map={"Pago": "#10b981", "Pendente": "#ef4444", "Investido": "#f59e0b", "Sonhos": "#8b5cf6", "Saldo Livre": "#3b82f6"})
            t_inf = 'percent+label' if not privacidade else 'none'
            fig.update_traces(textinfo=t_inf, pull=[0, 0, 0, 0, 0.1])
            fig.update_layout(showlegend=(not privacidade), margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)
            
    salvar_banco(st.session_state.db)
