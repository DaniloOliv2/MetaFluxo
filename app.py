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
        padding: 40px; border-radius: 24px; border: 1px solid #334155;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6); text-align: center;
        max-width: 380px; margin: auto;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #020617 100%);
    }
    .status-card {
        background: rgba(30, 41, 59, 0.7);
        padding: 20px; border-radius: 15px; border: 1px solid #334155;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b; border-radius: 10px 10px 0 0;
        color: white; padding: 10px 20px;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #3b82f6 , #10b981);
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTES E BANCO DE DADOS ---
DB_FILE = "metafluxo_db_v2.json"
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

def carregar_banco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
                if "users" not in data: data["users"] = {"admin": {"password": "123", "security_answer": "Murillo"}}
                if "recorrentes" not in data: data["recorrentes"] = []
                if "metas_sonhos" not in data: data["metas_sonhos"] = []
                return data
            except: pass
    return {
        "users": {"admin": {"password": "123", "security_answer": "Murillo"}},
        "recorrentes": [],
        "metas_sonhos": [],
        "config": {"taxa_juros": 0.08, "reserva_meses": 6}
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
                else: st.error("Dados incorretos")
            if st.button("Criar Conta"): st.session_state['auth_mode'] = 'signup'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state['auth_mode'] == 'signup':
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("Novo Cadastro")
            nu = st.text_input("Usuário")
            np = st.text_input("Senha", type="password")
            ns = st.text_input("Pergunta de Segurança (Nome do Filho?)")
            if st.button("CADASTRAR"):
                if nu and np and ns:
                    st.session_state.db["users"][nu] = {"password": np, "security_answer": ns}
                    salvar_banco(st.session_state.db)
                    st.success("Conta criada!"); time.sleep(1); st.session_state['auth_mode'] = 'login'; st.rerun()
            if st.button("Voltar"): st.session_state['auth_mode'] = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- INTERFACE PRINCIPAL ---
    with st.sidebar:
        st.title("📈 METAFLUX PRO")
        privacidade = st.toggle("👁️ Modo Privacidade")
        st.divider()
        
        with st.expander("⚙️ Gastos Recorrentes (Fixos)"):
            item_rec = st.text_input("Nome (ex: Netflix)")
            valor_rec = st.number_input("Valor R$", min_value=0.0)
            dia_rec = st.number_input("Dia Vencimento", 1, 31, 10)
            if st.button("Salvar Recorrente"):
                st.session_state.db["recorrentes"].append({"item": item_rec, "valor": valor_rec, "vencimento": dia_rec})
                salvar_banco(st.session_state.db); st.rerun()
            
            for i, r in enumerate(st.session_state.db["recorrentes"]):
                st.caption(f"{r['item']} (Dia {r['vencimento']})")
                if st.button(f"Remover {i}", key=f"rem_rec_{i}"):
                    st.session_state.db["recorrentes"].pop(i)
                    salvar_banco(st.session_state.db); st.rerun()

        st.divider()
        renda_fixa = st.number_input("Renda Mensal (R$)", value=3000.0)
        mes_ref = st.selectbox("Mês de Referência", MESES, index=3)
        if st.button("🚪 Sair"): st.session_state['logged_in'] = False; st.rerun()

    # --- INICIALIZAÇÃO DO MÊS (FIXADO) ---
    if mes_ref not in st.session_state.db:
        st.session_state.db[mes_ref] = {
            "gastos": [g.copy() for g in st.session_state.db["recorrentes"]],
            "investido": 0.0
        }
        for g in st.session_state.db[mes_ref]["gastos"]: 
            g["pago"] = False

    d_mes = st.session_state.db[mes_ref]
    t_gastos = sum(float(g['valor']) for g in d_mes['gastos'])
    t_pago = sum(float(g['valor']) for g in d_mes['gastos'] if g.get('pago'))
    inv_mes = float(d_mes.get('investido', 0.0))
    patrimonio = sum(float(s['acumulado']) for s in st.session_state.db.get('metas_sonhos', []))

    # --- HEADER GAMIFICADO ---
    st.markdown("### 🧱 Status do Babycraft")
    c_img, c_msg = st.columns([1, 5])
    
    if inv_mes >= (renda_fixa * 0.2):
        status, cor, icon = "Babycraft está em modo DIAMANTE!", "#10b981", "💎"
    elif t_pago > (t_gastos * 0.5):
        status, cor, icon = "Contas em dia. O peixinho está nadando tranquilo.", "#3b82f6", "🐟"
    else:
        status, cor, icon = "Babycraft precisa minerar mais... contas pendentes!", "#ef4444", "⚒️"
    
    c_msg.markdown(f"""<div style='background:{cor}; padding:15px; border-radius:12px; color:white; font-weight:bold;'>
    {icon} {status}</div>""", unsafe_allow_html=True)

    tab_m, tab_s, tab_h = st.tabs(["📅 Gestão Mensal", "🛡️ Saúde & Sonhos", "📊 Histórico"])

    with tab_m:
        st.write("")
        col1, col2, col3, col4 = st.columns(4)
        def fmt(v): return "R$ ****" if privacidade else f"R$ {v:,.2f}"
        
        col1.metric("Total Gastos", fmt(t_gastos))
        col2.metric("Pago", fmt(t_pago))
        col3.metric("Investido", fmt(inv_mes))
        col4.metric("Saldo Livre", fmt(renda_fixa - t_gastos - inv_mes))

        st.divider()
        cl1, cl2 = st.columns([1.5, 1])
        
        with cl1:
            st.subheader("📝 Lançamentos")
            if st.button("➕ Novo Gasto Extra"):
                d_mes["gastos"].append({"item": "Novo", "valor": 0.0, "pago": False, "vencimento": 10})
                salvar_banco(st.session_state.db); st.rerun()

            with st.container(height=400, border=True):
                idx_del = None
                for i, g in enumerate(d_mes["gastos"]):
                    with st.expander(f"📌 {g['item']} - Dia {g.get('vencimento',10)}"):
                        cx1, cx2, cx3, cx4 = st.columns([2, 1, 1, 0.5])
                        g["item"] = cx1.text_input("Item", g["item"], key=f"it_{mes_ref}_{i}")
                        g["valor"] = cx2.number_input("Valor", value=float(g["valor"]), key=f"vl_{mes_ref}_{i}")
                        g["vencimento"] = cx3.number_input("Venc.", 1, 31, int(g.get("vencimento",10)), key=f"vc_{mes_ref}_{i}")
                        g["pago"] = cx4.checkbox("OK", value=g.get("pago", False), key=f"pg_{mes_ref}_{i}")
                        if st.button("🗑️", key=f"del_{mes_ref}_{i}"): idx_del = i
                if idx_del is not None:
                    d_mes["gastos"].pop(idx_del); salvar_banco(st.session_state.db); st.rerun()

        with cl2:
            st.subheader("📊 Resumo Visual")
            if not privacidade:
                df_p = pd.DataFrame({"Cat": ["Pago", "Pendente", "Investido"], "Val": [t_pago, t_gastos-t_pago, inv_mes]})
                fig = px.pie(df_p, values="Val", names="Cat", hole=0.5, color="Cat",
                             color_discrete_map={"Pago": "#10b981", "Pendente": "#ef4444", "Investido": "#f59e0b"})
                st.plotly_chart(fig, use_container_width=True)
            
            with st.form("aporte"):
                st.write("Aporte de Investimento")
                novo_inv = st.number_input("Valor", value=inv_mes)
                if st.form_submit_button("Confirmar Investimento"):
                    d_mes["investido"] = novo_inv
                    salvar_banco(st.session_state.db); st.rerun()

    with tab_s:
        c_res, c_lib = st.columns(2)
        custo_vida = t_gastos if t_gastos > 0 else 1.0
        meta_reserva = custo_vida * 6
        prog_reserva = min(patrimonio / meta_reserva, 1.0)
        
        with c_res:
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.markdown("#### 🛡️ Reserva de Emergência")
            st.progress(prog_reserva)
            st.write(f"Cobertura: **{patrimonio/custo_vida:.1f} meses**")
            st.markdown('</div>', unsafe_allow_html=True)

        with c_lib:
            patrimonio_liberdade = (custo_vida * 12) / 0.08
            prog_lib = min(patrimonio / patrimonio_liberdade, 1.0)
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.markdown("#### 🕊️ Independência")
            st.progress(prog_lib)
            st.write(f"Progresso: **{prog_lib*100:.2f}%**")
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("🚀 Meus Sonhos")
        s_col1, s_col2 = st.columns([1, 2])
        with s_col1:
            with st.form("novo_sonho"):
                n_s = st.text_input("Qual o seu sonho?")
                v_s = st.number_input("Valor Alvo R$", min_value=0.0)
                if st.form_submit_button("Criar Meta"):
                    st.session_state.db["metas_sonhos"].append({"nome": n_s, "alvo": v_s, "acumulado": 0.0})
                    salvar_banco(st.session_state.db); st.rerun()
        with s_col2:
            idx_s_del = None
            for i, s in enumerate(st.session_state.db["metas_sonhos"]):
                alvo, acum = float(s['alvo']), float(s['acumulado'])
                prog = min(acum/alvo, 1.0) if alvo > 0 else 0.0
                with st.expander(f"⭐ {s['nome']} - {prog*100:.1f}%"):
                    cs1, cs2, cs3 = st.columns([2, 1, 0.5])
                    cs1.progress(prog)
                    dep = cs2.number_input("Aportar", min_value=0.0, key=f"dep_{i}")
                    if cs2.button("Adicionar", key=f"btn_dep_{i}"):
                        s['acumulado'] += dep; salvar_banco(st.session_state.db); st.rerun()
                    if cs3.button("🗑️", key=f"del_s_{i}"): idx_s_del = i
            if idx_s_del is not None:
                st.session_state.db["metas_sonhos"].pop(idx_s_del); salvar_banco(st.session_state.db); st.rerun()

    with tab_h:
        st.subheader("📈 Evolução")
        dados_h = []
        for m in MESES:
            if m in st.session_state.db:
                g_m = sum(float(x['valor']) for x in st.session_state.db[m]['gastos'])
                i_m = float(st.session_state.db[m].get('investido', 0.0))
                if g_m > 0 or i_m > 0:
                    dados_h.append({"Mês": m, "Gastos": g_m, "Investido": i_m})
        if dados_h:
            df_h = pd.DataFrame(dados_h)
            st.plotly_chart(px.bar(df_h, x="Mês", y=["Gastos", "Investido"], barmode="group"), use_container_width=True)
            st.table(df_h)

    salvar_banco(st.session_state.db)
