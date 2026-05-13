# MetaFlux Pro

App de controle financeiro em Streamlit com:

- Login e cadastro de usuários
- Senhas protegidas com hash PBKDF2
- Banco SQLite
- Dados separados por usuário
- Dashboard financeiro
- Gastos por mês
- Metas de investimento
- Sonhos/objetivos financeiros
- Gráficos com Plotly
- Exportação CSV

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Usuário inicial de teste:

- usuário: `admin`
- senha: `123`

## Publicar no Streamlit Cloud

1. Envie os arquivos para o GitHub.
2. No Streamlit Cloud, selecione o repositório.
3. Main file path: `app.py`
4. Deploy.

> Observação: para produção definitiva, recomenda-se trocar SQLite por Supabase, Firebase ou PostgreSQL, pois o Streamlit Cloud pode reiniciar o ambiente.
