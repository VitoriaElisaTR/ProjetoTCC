import streamlit as st

from config.auth import *
from functions.functions import *


def user_profile():
    conn_user, cursor_user = conect_database_with_user()
    df_login_user_data, df_user_bd = make_db_highq_login(cursor_user)
    username = st.session_state.username
    line_user = df_login_user_data[df_login_user_data['EMAIL'] == username].reset_index(drop=True)
    
    topbar("Perfil do usuário") #função fo estilo do topo do site

    # Simulação de dados do usuário
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    if "user_data" not in st.session_state:
        st.session_state.user_data = {
            "nome": line_user['NAME'][0],
            "email": line_user['EMAIL'][0],
            "oab": line_user['NUM_OAB'][0],
            "senha": line_user['LOGIN_PASSWORD'][0]
        }



    # Campos de dados
    nome = st.text_input("Nome", st.session_state.user_data["nome"], disabled=not st.session_state.edit_mode)
    email = st.text_input("Email", st.session_state.user_data["email"], disabled=True)
    oab = st.text_input("Número da OAB", st.session_state.user_data["oab"], disabled=not st.session_state.edit_mode)
    senha = st.text_input("Senha", st.session_state.user_data["senha"], type="password", disabled=not st.session_state.edit_mode)

    # Botão para editar
    if st.button("Editar" if not st.session_state.edit_mode else "Cancelar"):
        st.session_state.edit_mode = not st.session_state.edit_mode

    # Botão de salvar
    if st.session_state.edit_mode:
        if st.button("Salvar"):
            new_data_dict = {
                "nome": nome,
                "oab": oab,
                "senha": senha,
                "email": email
            }
            st.session_state.user_data.update()
            update_user_data(conn_user, cursor_user, new_data_dict)
            st.success("Dados atualizados com sucesso!")
            st.session_state.edit_mode = False
