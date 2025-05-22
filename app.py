
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Autenticação com Google Sheets
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credencial.json", scope)
client = gspread.authorize(creds)

# Abrir as planilhas
planilha = client.open("sistema_estoque")
usuarios_sheet = planilha.worksheet("usuarios")
produtos_sheet = planilha.worksheet("produtos")
movimentacoes_sheet = planilha.worksheet("movimentacoes")

# Funções
def login(login_usuario, senha):
    usuarios = usuarios_sheet.get_all_records()
    for user in usuarios:
        if user['login'] == login_usuario and str(user['senha']) == str(senha):
            return user['nome']
    return None

def cadastrar_usuario(id, nome, login_usuario, senha):
    usuarios_sheet.append_row([id, nome, login_usuario, senha])

def cadastrar_produto(id, nome, quantidade, preco):
    produtos_sheet.append_row([id, nome, quantidade, preco])

def entrada_estoque(produto_id, quantidade, usuario):
    produtos = produtos_sheet.get_all_records()
    for i, produto in enumerate(produtos):
        if str(produto['id']) == str(produto_id):
            nova_quantidade = int(produto['quantidade']) + int(quantidade)
            produtos_sheet.update_cell(i + 2, 3, nova_quantidade)
            registrar_movimentacao("entrada", produto_id, quantidade, usuario)
            return f"Entrada realizada. Novo estoque de {produto['nome']}: {nova_quantidade}"
    return "Produto não encontrado."

def saida_estoque(produto_id, quantidade, usuario):
    produtos = produtos_sheet.get_all_records()
    for i, produto in enumerate(produtos):
        if str(produto['id']) == str(produto_id):
            estoque_atual = int(produto['quantidade'])
            if estoque_atual >= int(quantidade):
                nova_quantidade = estoque_atual - int(quantidade)
                produtos_sheet.update_cell(i + 2, 3, nova_quantidade)
                registrar_movimentacao("saida", produto_id, quantidade, usuario)
                return f"Saída realizada. Novo estoque de {produto['nome']}: {nova_quantidade}"
            else:
                return "Estoque insuficiente!"
    return "Produto não encontrado."

def registrar_movimentacao(tipo, produto_id, quantidade, usuario):
    data = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    movimentacoes = movimentacoes_sheet.get_all_values()
    id_mov = len(movimentacoes)
    movimentacoes_sheet.append_row([id_mov, tipo, produto_id, quantidade, data, usuario])

def listar_produtos():
    return produtos_sheet.get_all_records()

def listar_movimentacoes():
    return movimentacoes_sheet.get_all_records()

# Interface Streamlit
st.set_page_config(page_title="Sistema de Estoque", page_icon="📦")
st.title("📦 Sistema de Estoque - Web")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.subheader("🔑 Login")
    login_usuario = st.text_input("Login")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        usuario = login(login_usuario, senha)
        if usuario:
            st.success(f"Bem-vindo, {usuario}!")
            st.session_state.usuario = usuario
        else:
            st.error("Login ou senha inválidos.")
else:
    st.sidebar.title(f"Olá, {st.session_state.usuario}")
    menu = st.sidebar.selectbox("Menu", ["📦 Produtos", "➕➖ Movimentações", "📑 Relatórios", "👥 Usuários", "🚪 Logout"])

    if menu == "📦 Produtos":
        st.subheader("Cadastro e Listagem de Produtos")
        with st.form("Cadastro de Produto"):
            id = st.text_input("ID do Produto")
            nome = st.text_input("Nome do Produto")
            quantidade = st.number_input("Quantidade", min_value=0, step=1)
            preco = st.number_input("Preço", min_value=0.0, step=0.01)
            submitted = st.form_submit_button("Cadastrar")
            if submitted:
                cadastrar_produto(id, nome, quantidade, preco)
                st.success("Produto cadastrado com sucesso!")

        st.subheader("📄 Produtos cadastrados:")
        produtos = listar_produtos()
        st.table(produtos)

    if menu == "➕➖ Movimentações":
        st.subheader("Movimentar Estoque")
        tipo = st.selectbox("Tipo", ["entrada", "saida"])
        produto_id = st.text_input("ID do Produto")
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        if st.button("Registrar"):
            if tipo == "entrada":
                msg = entrada_estoque(produto_id, quantidade, st.session_state.usuario)
            else:
                msg = saida_estoque(produto_id, quantidade, st.session_state.usuario)
            st.info(msg)

    if menu == "📑 Relatórios":
        st.subheader("📦 Estoque Atual")
        produtos = listar_produtos()
        st.table(produtos)

        st.subheader("🗂️ Movimentações")
        movimentacoes = listar_movimentacoes()
        st.table(movimentacoes)

    if menu == "👥 Usuários":
        st.subheader("Cadastro de Usuários")
        with st.form("Cadastro de Usuário"):
            id = st.text_input("ID do Usuário")
            nome = st.text_input("Nome")
            login_user = st.text_input("Login")
            senha_user = st.text_input("Senha")
            submitted = st.form_submit_button("Cadastrar Usuário")
            if submitted:
                cadastrar_usuario(id, nome, login_user, senha_user)
                st.success("Usuário cadastrado com sucesso!")

    if menu == "🚪 Logout":
        st.session_state.usuario = None
        st.success("Logout realizado.")
