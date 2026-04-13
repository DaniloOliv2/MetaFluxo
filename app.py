import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd
from PIL import Image
import time

# --- CONFIGURAÇÃO VISUAL ---
try:
    img_favicon = Image.open("favicon.jpg")
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon=img_favicon)
except:
    st.set_page_config(page_title="MetaFlux Pro 📈", layout="wide", page_icon="📈")

# --- ESTILO CSS AVANÇADO (CORES E FUNDO CONFORME REFERÊNCIA) ---
st.markdown("""
    <style>
    /* Fundo degradê conforme imagem de referência */
    .stApp { 
        background-color: #020617;
        background-image: radial-gradient(circle at top right, #1e3a8a, #020617);
    }
    
    /* Cartão de Login Estilo Card */
    .login-card {
        background-color: #1e293b;
        padding: 40px;
        border-radius: 24px;
        border: 1px solid #334155;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        text-align: center;
        max-width: 380px;
        margin: auto;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #020617 100%);
    }
    
    /* Inputs Slim e Modernos */
    div[data-baseweb="input"] {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        min-height: 40px !important;
    }
    
    input { color: #f1f5f9 !important; font-size: 0.95rem !important; }

    /* Botão Principal */
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        height: 45px !important;
        width: 100% !important;
        border: none !important;
        margin-top: 10px;
    }
    
    /* Barra de progresso verde neon */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #3b82f6 , #10b981);
    }

    /* Rodapé e Links */
    .link-footer { margin-top: 15px; font-size: 0.85rem; }
    .link-footer button {
        background: none !important; border: none !important;
        color: #94a3b8 !important; text-decoration: underline !important;
    }
    .copyright { margin-top: 20px; font-size: 0.7rem; color: #475569; }
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

# --- TELA DE LOGIN ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        st.write("")
        if st.session_state['auth_mode'] == 'login':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            
            # --- TODA A SEÇÃO SUPERIOR FOI REMOVIDA (QUADRADO E NOME METAFLUX) ---
            # O card agora começa direto nos inputs abaixo.
            # ---------------------------------------------------------------------
            
            u = st.text_input("Usuário", placeholder="Seu usuário", key="user_login")
            p = st.text_input("Senha", type="password", placeholder="Sua senha", key="pass_login")
            
            c1, c2 = st.columns(2)
            c1.checkbox("Lembrar", key="rem")
            if c2.button("Esqueci a senha", key="forgot"):
                st.session_state['auth_mode'] = 'recover'; st.rerun()

            if st.button("ACESSAR PAINEL"):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else:
                    st.session_state['error_msg'] = True; st.rerun()
            
            if st.session_state['error_msg']:
                st.error("Dados incorretos!")
                time.sleep(3); st.session_state['error_msg'] = False; st.rerun()

            if st.button("Não tem conta? Cadastre-se"):
                st.session_state['auth_mode'] = 'signup'; st.rerun()
            st.markdown('<div class="copyright">© 2026 MetaFlux. Direitos reservados.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'signup':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Nova Conta")
            new_u = st.text_input("Usuário")
            new_p = st.text_input("Senha", type="password")
            new_s = st.text_input("Nome do filho? (Segurança)")
            if st.button("CADASTRAR"):
                if new_u and new_p and new_s:
                    st.session_state.db["users"][new_u] = {"password": new_p, "security_answer": new_s}
                    salvar_banco(st.session_state.db); st.success("Criado!"); time.sleep(2)
                    st.session_state['auth_mode'] = 'login'; st.rerun()
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'recover':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Recuperação")
            rec_u = st.text_input("Seu usuário")
            if rec_u in st.session_state.db["users"]:
                ans = st.text_input("Resposta de segurança")
                if st.button("VER SENHA"):
                    if ans.lower() == st.session_state.db["users"][rec_u]["security_answer"].lower():
                        st.info(f"Sua senha: {st.session_state.db['users'][rec_u]['password']}")
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- APP LOGADO (MANTIDO EXATAMENTE IGUAL) ---
    with st.sidebar:
        try: st.image("logo.png", use_column_width=True)
        except: st.title("📈 METAFLUX")
        st.divider()
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        mes = st.selectbox("Mês", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        
        if privacidade:
            renda, meta_inv = 3000.0, 1000.0
        else:
            renda = st.number_input("Sua Renda (R$)", value=3000.0, format="%.2f")
            meta_inv = st.number_input("Meta Investimento (R$)", value=1000.0, format="%.2f")
        
        if st.button("🚪 Sair"):
            st.session_state['logged_in'] = False; st.rerun()

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
    c4.metric("💰 SALDO LIVRE", fmt(saldo))

    # Barra de Progresso da Meta Mensal
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
            salvar_banco(st.session_state.db); st.rerun()

        if st.button("➕ Novo Gasto"):
            st.session_state.db[mes]["gastos"].append({"item": "Novo", "valor": 0.0, "pago": False})
            salvar_banco(st.session_state.db); st.rerun()
        
        with st.container(height=350):
            idx_del = None
            for i, g in enumerate(d_mes["gastos"]):
                with st.expander(f"📦 {g['item']} - {fmt(g['valor'])}", expanded=True):
                    ca1, ca2, ca3 = st.columns([2, 1, 1])
                    g["item"] = ca1.text_input("Item", g["item"], key=f"it_{mes}_{i}")
                    if not privacidade:
                        g["valor"] = ca2.number_input("Valor", value=float(g["valor"]), key=f"vl_{mes}_{i}", format="%.2f")
                    g["pago"] = ca3.checkbox("Pago?", value=g["pago"], key=f"ck_{mes}_{i}")
                    if st.button("🗑️ Deletar", key=f"del_{mes}_{i}"): idx_del = i
            if idx_del is not None:
                d_mes["gastos"].pop(idx_del); salvar_banco(st.session_state.db); st.rerun()

    with col_g:
        st.subheader("📊 Gráfico")
        labels = ["Pago", "Pendente", "Investido", "Sonhos", "Saldo Livre"]
        valores = [t_pago, t_pend, inv_mes, total_sonhos, max(0, saldo)]
        df_p = pd.DataFrame({"Legenda": labels, "Valor": valores})
        df_p = df_p[df_p["Valor"] > 0]
        if not df_p.empty:
            fig = px.pie(df_p, values='Valor', names='Legenda', hole=0.5, color='Legenda', color_discrete_map={"Pago": "#10b981", "Pendente": "#ef4444", "Investido": "#f59e0b", "Sonhos": "#8b5cf6", "Saldo Livre": "#3b82f6"})
            fig.update_layout(showlegend=(not privacidade), margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)

    # --- ABAIXO: SEÇÃO MEUS SONHOS ---
    st.divider()
    st.subheader("🚀 Meus Sonhos")
    s1, s2 = st.columns([1, 2])
    with s1:
        with st.form("form_sonho"):
            nome_s = st.text_input("Qual o seu sonho?")
            alvo_s = st.number_input("Valor da Meta (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Criar Objetivo"):
                if "metas_sonhos" not in st.session_state.db: st.session_state.db["metas_sonhos"] = []
                st.session_state.db["metas_sonhos"].append({"nome": nome_s, "alvo": alvo_s, "acumulado": 0.0})
                salvar_banco(st.session_state.db); st.rerun()

    with s2:
        with st.container(height=300):
            idx_s_del = None
            for i, s in enumerate(st.session_state.db.get("metas_sonhos", [])):
                alvo, acum = float(s['alvo']), float(s['acumulado'])
                prog = min(acum / alvo, 1.0) if alvo > 0 else 0.0
                with st.expander(f"⭐ {s['nome']} - {prog*100:.1f}%"):
                    ci1, ci2, ci3 = st.columns([2, 1.5, 0.5])
                    ci1.write(f"Guardado: {fmt(acum)}")
                    ci1.progress(prog)
                    if not privacidade:
                        v_dep = ci2.number_input(f"Aportar", value=0.0, key=f"dep_{i}")
                        if ci2.button("Confirmar", key=f"btn_{i}"):
                            s['acumulado'] += v_dep; salvar_banco(st.session_state.db); st.rerun()
                    if ci3.button("🗑️", key=f"del_s_{i}"): idx_s_del = i
            if idx_s_del is not None:
                st.session_state.db["metas_sonhos"].pop(idx_s_del)
                salvar_banco(st.session_state.db); st.rerun()
    salvar_banco(st.session_state.db)
