import streamlit as st
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from database.neon_config import executar_sql, buscar_todos


def interpretar_reais(texto):
    s = str(texto).strip().replace('R$', '').replace(' ', '')
    if not s:
        raise ValueError('Informe um valor.')
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif s.count('.') > 1:
        s = s.replace('.', '')
    elif '.' in s and len(s.split('.')[-1]) == 3:
        s = s.replace('.', '')
    try:
        valor = Decimal(s)
    except InvalidOperation:
        raise ValueError('Valor inválido. Exemplo: 1.500,00')
    if not valor.is_finite() or valor < 0:
        raise ValueError('Informe um valor maior ou igual a zero.')
    return valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def texto_reais(valor):
    return f'{Decimal(str(valor or 0)):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def fmt_moeda(valor):
    return f'R$ {texto_reais(valor)}'


def garantir_tabela_metas():
    executar_sql('''
        CREATE TABLE IF NOT EXISTS metas (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT,
            valor_meta NUMERIC(15,2) NOT NULL DEFAULT 0,
            valor_atual NUMERIC(15,2) NOT NULL DEFAULT 0,
            prazo DATE,
            categoria TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')


def criar_meta(usuario_id, nome, descricao, valor_meta, valor_atual, prazo, categoria):
    executar_sql('''
        INSERT INTO metas (usuario_id, nome, descricao, valor_meta, valor_atual, prazo, categoria)
        VALUES (:usuario_id, :nome, :descricao, :valor_meta, :valor_atual, :prazo, :categoria)
    ''', {'usuario_id': usuario_id, 'nome': nome, 'descricao': descricao,
          'valor_meta': str(valor_meta), 'valor_atual': str(valor_atual),
          'prazo': prazo, 'categoria': categoria})


def listar_metas(usuario_id):
    return buscar_todos('''
        SELECT * FROM metas WHERE usuario_id = :usuario_id ORDER BY id DESC
    ''', {'usuario_id': usuario_id})


def atualizar_meta(usuario_id, meta_id, nome, descricao, valor_meta, valor_atual, prazo, categoria):
    executar_sql('''
        UPDATE metas SET nome = :nome, descricao = :descricao,
            valor_meta = :valor_meta, valor_atual = :valor_atual,
            prazo = :prazo, categoria = :categoria
        WHERE id = :meta_id AND usuario_id = :usuario_id
    ''', {'usuario_id': usuario_id, 'meta_id': meta_id, 'nome': nome,
          'descricao': descricao, 'valor_meta': str(valor_meta),
          'valor_atual': str(valor_atual), 'prazo': prazo, 'categoria': categoria})


def adicionar_aporte(usuario_id, meta_id, valor):
    executar_sql('''
        UPDATE metas SET valor_atual = valor_atual + :valor
        WHERE id = :meta_id AND usuario_id = :usuario_id
    ''', {'usuario_id': usuario_id, 'meta_id': meta_id, 'valor': str(valor)})


def deletar_meta(usuario_id, meta_id):
    executar_sql('''
        DELETE FROM metas WHERE id = :meta_id AND usuario_id = :usuario_id
    ''', {'usuario_id': usuario_id, 'meta_id': meta_id})


def tela_metas(usuario_id):
    garantir_tabela_metas()
    st.subheader('🚀 Meus Sonhos e Metas')
    categorias = ['Reserva de emergência', 'Viagem', 'Casa', 'Carro', 'Moto',
                  'Notebook', 'Celular', 'Investimentos', 'Aposentadoria', 'Outros']

    with st.expander('➕ Nova meta', expanded=False):
        with st.form('form_meta', clear_on_submit=True):
            nome = st.text_input('Nome da meta', placeholder='Ex: Viagem para Europa')
            descricao = st.text_area('Descrição', placeholder='Detalhes da meta...')
            categoria = st.selectbox('Categoria', categorias)
            valor_meta_txt = st.text_input('Valor da meta (R$)', value='0,00', key='nova_meta_valor')
            valor_atual_txt = st.text_input('Quanto você já possui (R$)', value='0,00', key='nova_meta_atual')
            prazo = st.date_input('Prazo estimado', value=date.today())
            enviar = st.form_submit_button('Criar meta', use_container_width=True)
            if enviar:
                try:
                    valor_meta = interpretar_reais(valor_meta_txt)
                    valor_atual = interpretar_reais(valor_atual_txt)
                    if not nome.strip():
                        st.warning('Informe o nome da meta.')
                    elif valor_meta <= 0:
                        st.warning('O valor da meta deve ser maior que zero.')
                    else:
                        criar_meta(usuario_id, nome.strip(), descricao.strip(), valor_meta,
                                   valor_atual, prazo, categoria)
                        st.success('Meta criada com sucesso!')
                        st.rerun()
                except ValueError as erro:
                    st.warning(str(erro))

    metas = listar_metas(usuario_id)
    if not metas:
        st.info('Nenhuma meta cadastrada ainda.')
        return

    total_metas = sum(Decimal(str(m['valor_meta'])) for m in metas)
    total_guardado = sum(Decimal(str(m['valor_atual'])) for m in metas)
    progresso_total = (total_guardado / total_metas * 100) if total_metas > 0 else 0
    c1, c2, c3 = st.columns(3)
    c1.metric('🎯 Total das metas', fmt_moeda(total_metas))
    c2.metric('💰 Total guardado', fmt_moeda(total_guardado))
    c3.metric('📈 Progresso geral', f'{progresso_total:.1f}%')
    st.caption('Os valores das metas são um acompanhamento separado. Aportes não movimentam automaticamente contas bancárias.')
    st.divider()

    for meta in metas:
        mid = meta['id']
        valor_meta = Decimal(str(meta['valor_meta']))
        valor_atual = Decimal(str(meta['valor_atual']))
        progresso = valor_atual / valor_meta if valor_meta > 0 else Decimal(0)
        faltam = max(valor_meta - valor_atual, Decimal(0))
        with st.container(border=True):
            st.markdown(f"### 🚀 {meta['nome']}")
            st.write(f"**Categoria:** {meta['categoria']}")
            if meta['descricao']:
                st.write(meta['descricao'])
            st.progress(max(0.0, min(float(progresso), 1.0)))
            st.write(f'**{progresso * 100:.1f}% concluído**')
            st.write(f'💰 Guardado: {fmt_moeda(valor_atual)}')
            st.write(f'🎯 Meta: {fmt_moeda(valor_meta)}')
            st.write(f'📌 Faltam: {fmt_moeda(faltam)}')
            if meta['prazo']:
                st.write(f"📅 Prazo: {meta['prazo']}")
            if progresso >= 1:
                st.success('🎉 Meta concluída!')

            with st.expander('💰 Adicionar aporte'):
                with st.form(f'aporte_form_{mid}', clear_on_submit=True):
                    aporte_txt = st.text_input('Valor do aporte (R$)', value='0,00', key=f'aporte_txt_{mid}')
                    if st.form_submit_button('Registrar aporte', use_container_width=True):
                        try:
                            aporte = interpretar_reais(aporte_txt)
                            if aporte <= 0:
                                st.warning('O aporte deve ser maior que zero.')
                            else:
                                adicionar_aporte(usuario_id, mid, aporte)
                                st.success('Aporte registrado na meta!')
                                st.rerun()
                        except ValueError as erro:
                            st.warning(str(erro))

            with st.expander('✏️ Editar / Excluir'):
                novo_nome = st.text_input('Nome', value=meta['nome'], key=f'nome_meta_{mid}')
                nova_descricao = st.text_area('Descrição', value=meta['descricao'] or '', key=f'desc_meta_{mid}')
                nova_categoria = st.selectbox('Categoria', categorias,
                    index=categorias.index(meta['categoria']) if meta['categoria'] in categorias else 0,
                    key=f'cat_meta_{mid}')
                novo_valor_meta_txt = st.text_input('Valor da meta (R$)',
                    value=texto_reais(valor_meta), key=f'meta_valor_{mid}')
                novo_valor_atual_txt = st.text_input('Valor atual (R$)',
                    value=texto_reais(valor_atual), key=f'meta_atual_{mid}')
                novo_prazo = st.date_input('Prazo', value=meta['prazo'] or date.today(), key=f'prazo_meta_{mid}')
                confirmar_key = f'confirmar_exclusao_meta_{usuario_id}_{mid}'
                if st.session_state.get(confirmar_key, False):
                    st.warning(f"Deseja realmente excluir a meta '{meta['nome']}'? Essa ação não pode ser desfeita.")
                    b1, b2 = st.columns(2)
                    if b1.button('Confirmar exclusão', key=f'confirmar_meta_{mid}', use_container_width=True):
                        deletar_meta(usuario_id, mid)
                        st.session_state.pop(confirmar_key, None)
                        st.success('Meta excluída!')
                        st.rerun()
                    if b2.button('Cancelar', key=f'cancelar_meta_{mid}', use_container_width=True):
                        st.session_state.pop(confirmar_key, None)
                        st.rerun()
                else:
                    b1, b2 = st.columns(2)
                    if b1.button('Salvar', key=f'salvar_meta_{mid}', use_container_width=True):
                        try:
                            novo_valor_meta = interpretar_reais(novo_valor_meta_txt)
                            novo_valor_atual = interpretar_reais(novo_valor_atual_txt)
                            if not novo_nome.strip():
                                st.warning('Informe o nome da meta.')
                            elif novo_valor_meta <= 0:
                                st.warning('O valor da meta deve ser maior que zero.')
                            else:
                                atualizar_meta(usuario_id, mid, novo_nome.strip(), nova_descricao.strip(),
                                    novo_valor_meta, novo_valor_atual, novo_prazo, nova_categoria)
                                st.success('Meta atualizada!')
                                st.rerun()
                        except ValueError as erro:
                            st.warning(str(erro))
                    if b2.button('Excluir', key=f'excluir_meta_{mid}', use_container_width=True):
                        st.session_state[confirmar_key] = True
                        st.rerun()
