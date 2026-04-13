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

# --- ESTILO CSS AVANÇADO ---
st.markdown("""
    <style>
    .stApp { 
        background-color: #020617;
        background-image: radial-gradient(circle at top right, #1e3a8a, #020617);
    }
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
    div[data-baseweb="input"] {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    input { color: #f1f5f9 !important; }
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        height: 45px !important;
        width: 100% !important;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #3b82f6 , #10b981);
    }
    .copyright { margin-top: 20px; font-size: 0.7rem; color: #475569; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_FILE = "metafluxo_db.json"

def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: 
                data = json.load(f)
                if "users" not in data: data["users"] = {}
                if "metas_sonhos" not in data: data["metas_sonhos"] = []
                return data
            except: pass
    return {
        "users": {"admin": {"password": "123", "security_answer": "Murillo"}}, 
        "metas_sonhos": [], 
        "config": {"categorias": {"🏠 Moradia": "#3498db", "🍎 Alimentação": "#e67e22"}}
    }

def salvar_banco(dados):
    with open(DB_FILE, "w") as f:
        json.dump(dados, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = carregar_banco()

# --- ESTADOS DE SESSÃO ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

# --- TELA DE ACESSO ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        st.write("")
        if st.session_state['auth_mode'] == 'login':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown("<h1 style='color: #60a5fa; font-weight: 800;'>METAFLUX</h1>", unsafe_allow_html=True)
            u = st.text_input("Usuário", key="user_login")
            p = st.text_input("Senha", type="password", key="pass_login")
            
            if st.button("ACESSAR PAINEL"):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")
            
            st.divider()
            if st.button("Criar nova conta"):
                st.session_state['auth_mode'] = 'signup'; st.rerun()
            if st.button("Esqueci a senha"):
                st.session_state['auth_mode'] = 'recover'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'signup':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Novo Cadastro")
            new_u = st.text_input("Escolha um Usuário")
            new_p = st.text_input("Escolha uma Senha", type="password")
            new_s = st.text_input("Pergunta de Segurança (Nome do filho?)")
            
            if st.button("FINALIZAR CADASTRO"):
                if new_u in st.session_state.db["users"]:
                    st.warning("Este usuário já existe!")
                elif new_u and new_p and new_s:
                    st.session_state.db["users"][new_u] = {"password": new_p, "security_answer": new_s}
                    salvar_banco(st.session_state.db)
                    st.success("Conta criada!")
                    time.sleep(1.5)
                    st.session_state['auth_mode'] = 'login'; st.rerun()
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['auth_mode'] == 'recover':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Recuperação")
            rec_u = st.text_input("Digite seu usuário")
            if rec_u in st.session_state.db["users"]:
                ans = st.text_input("Resposta de segurança")
                if st.button("REVELAR SENHA"):
                    if ans.lower() == st.session_state.db["users"][rec_u]["security_answer"].lower():
                        st.code(f"Sua senha é: {st.session_state.db['users'][rec_u]['password']}")
                    else:
                        st.error("Resposta incorreta")
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- DASHBOARD LOGADO ---
    with st.sidebar:
        st.title("📈 METAFLUX")
        st.caption(f"Bem-vindo, {st.session_state['current_user']}")
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        mes = st.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=3)
        
        if privacidade:
            renda, meta_inv = 0.0, 0.0
        else:
            renda = st.number_input("Renda Mensal (R$)", value=3000.0, step=100.0)
            meta_inv = st.number_input("Meta de Investimento (R$)", value=1000.0, step=50.0)
        
        if st.button("🚪 Encerrar Sessão"):
            st.session_state['logged_in'] = False; st.rerun()

    def fmt(valor):
        return "R$ ••••••" if privacidade else f"R$ {float(valor):,.2f}"

    # Inicialização do mês no banco
    if mes not in st.session_state.db: 
        st.session_state.db[mes] = {"gastos": [], "investido": 0.0}
    
    d_mes = st.session_state.db[mes]
    t_pago = sum(float(g['valor']) for g in d_mes['gastos'] if g['pago'])
    t_pend = sum(float(g['valor']) for g in d_mes['gastos'] if not g['pago'])
    inv_mes = float(d_mes.get('investido', 0.0))
    total_sonhos = sum(float(s['acumulado']) for s in st.session_state.db.get('metas_sonhos', []))
    saldo = renda - t_pago - t_pend - inv_mes

    st.title(f"🚀 Painel Financeiro - {mes}")
    
    # Métricas Principais
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ EFETUADOS", fmt(t_pago))
    c2.metric("⏳ AGENDADOS", fmt(t_pend))
    c3.metric("⭐ PATRIMÔNIO SONHOS", fmt(total_sonhos)) 
    c4.metric("💰 DISPONÍVEL", fmt(saldo))

    # Progresso da Meta
    st.write("")
    prog_meta = min(inv_mes / meta_inv, 1.0) if meta_inv > 0 else 0.0
    cp1, cp2 = st.columns([3, 1])
    cp1.markdown(f"**Progresso da Meta de Investimento ({prog_meta*100:.1f}%)**")
    cp2.markdown(f"<div style='text-align:right'>Faltam: {fmt(max(0, meta_inv - inv_mes))}</div>", unsafe_allow_html=True)
    st.progress(prog_meta)
    st.divider()

    col_l, col_g = st.columns([1.5, 1])
    
    with col_l:
        st.subheader("📝 Lançamentos e Aportes")
        
        # Melhoria: Form para evitar que cada dígito dispare o rerun
        with st.form("aporte_mensal"):
            new_inv = st.number_input("Valor Investido este Mês (R$)", value=inv_mes, format="%.2f")
            if st.form_submit_button("Confirmar Aporte"):
                st.session_state.db[mes]['investido'] = new_inv
                salvar_banco(st.session_state.db); st.rerun()

        if st.button("➕ Adicionar Novo Gasto"):
            st.session_state.db[mes]["gastos"].append({"item": "Novo Item", "valor": 0.0, "pago": False})
            salvar_banco(st.session_state.db); st.rerun()
        
        with st.container(height=400, border=True):
            idx_del = None
            for i, g in enumerate(d_mes["gastos"]):
                with st.expander(f"📌 {g['item']} - {fmt(g['valor'])}", expanded=not g['pago']):
                    ca1, ca2, ca3 = st.columns([2, 1, 1])
                    g["item"] = ca1.text_input("Descrição", g["item"], key=f"it_{mes}_{i}")
                    if not privacidade:
                        g["valor"] = ca2.number_input("Valor", value=float(g["valor"]), key=f"vl_{mes}_{i}")
                    g["pago"] = ca3.checkbox("Pago?", value=g["pago"], key=f"ck_{mes}_{i}")
                    if st.button("🗑️ Excluir", key=f"del_{mes}_{i}"): 
                        idx_del = i
            if idx_del is not None:
                d_mes["gastos"].pop(idx_del); salvar_banco(st.session_state.db); st.rerun()

    with col_g:
        st.subheader("📊 Composição do Mês")
        if privacidade:
            st.info("Gráfico oculto para sua proteção.")
        else:
            labels = ["Pago", "Pendente", "Investido", "Saldo"]
            valores = [t_pago, t_pend, inv_mes, max(0, saldo)]
            df_p = pd.DataFrame({"Legenda": labels, "Valor": valores})
            df_p = df_p[df_p["Valor"] > 0]
            if not df_p.empty:
                fig = px.pie(df_p, values='Valor', names='Legenda', hole=0.6,
                             color='Legenda', color_discrete_map={"Pago": "#10b981", "Pendente": "#ef4444", "Investido": "#f59e0b", "Saldo": "#3b82f6"})
                fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

    # --- SEÇÃO MEUS SONHOS ---
    st.divider()
    st.subheader("⭐ Gestão de Sonhos e Metas")
    s1, s2 = st.columns([1, 2])
    
    with s1:
        with st.form("form_sonho", clear_on_submit=True):
            st.write("Novo Objetivo")
            nome_s = st.text_input("O que você quer conquistar?")
            alvo_s = st.number_input("Valor Total (R$)", min_value=0.0)
            if st.form_submit_button("Criar Sonho"):
                if "metas_sonhos" not in st.session_state.db: st.session_state.db["metas_sonhos"] = []
                st.session_state.db["metas_sonhos"].append({"nome": nome_s, "alvo": alvo_s, "acumulado": 0.0})
                salvar_banco(st.session_state.db); st.rerun()

    with s2:
        with st.container(height=350, border=True):
            idx_s_del = None
            for i, s in enumerate(st.session_state.db.get("metas_sonhos", [])):
                alvo, acum = float(s['alvo']), float(s['acumulado'])
                prog = min(acum / alvo, 1.0) if alvo > 0 else 0.0
                with st.expander(f"🎯 {s['nome']} ({prog*100:.1f}%)"):
                    ci1, ci2, ci3 = st.columns([2, 1.5, 0.5])
                    ci1.write(f"Acumulado: {fmt(acum)} de {fmt(alvo)}")
                    ci1.progress(prog)
                    if not privacidade:
                        v_dep = ci2.number_input(f"Aportar valor", value=0.0, key=f"dep_{i}")
                        if ci2.button("Adicionar", key=f"btn_{i}"):
                            s['acumulado'] += v_dep; salvar_banco(st.session_state.db); st.rerun()
                    if ci3.button("🗑️", key=f"del_s_{i}"): idx_s_del = i
            if idx_s_del is not None:
                st.session_state.db["metas_sonhos"].pop(idx_s_del)
                salvar_banco(st.session_state.db); st.rerun()

    # Salvamento final preventivo
    salvar_banco(st.session_state.db)
