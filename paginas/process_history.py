import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from functions.functions import *
from config.auth import *

# Simulação de dados do banco

def process_history():
    conn_user, cursor_user = conect_database_with_user()
    df_process = make_db_process(cursor_user)
    df_estados, df_class_process, df_path_process, df_datajud_endpoints = make_db_register(cursor_user)

    topbar("Histórico de Processos") #função fo estilo do topo do site

    tab1, tab2 = st.tabs(["Todos os Processos", "Atualização de Processo"])

    with tab1:
        st.subheader("Cadastro Manual")
        # Selecionar processo para editar
        opcoes = ["Todos"]
        opcoes_df = df_process["NUMERO_PROCESSO"].tolist()
        opcoes_list = opcoes + opcoes_df
        selecionado = st.selectbox("Selecione um processo para editar:", opcoes_list)

        if selecionado == "Todos":
            st.dataframe(df_process, use_container_width=True)
        else:
            df_selecionado = df_process[df_process["NUMERO_PROCESSO"] == selecionado]
            if not df_selecionado.empty:
                st.dataframe(df_selecionado, use_container_width=True)
            else:
                st.warning("Nenhum processo encontrado com o número selecionado.")

        # Dados do processo selecionado
        #processo = df_process[df_process["NUMERO_PROCESSO"] == selecionado].iloc[0]



    with tab2:
        opcoes_df = df_process["NUMERO_PROCESSO"].tolist()
        path_process_list = df_path_process['CAMINHO_PROCESSUAL'].tolist()
        selecionado = st.selectbox("Selecione um processo para editar:", opcoes_df)
        df_selecionado = df_process[df_process["NUMERO_PROCESSO"] == selecionado].reset_index(drop=True)
        with st.form("editar_processo"):
            st.markdown("### Editar Processo")
            indice_padrao = path_process_list.index(df_selecionado['CAMINHO_PROCESSUAL'][0])
            process_path = st.selectbox("Escolha o Caminho Processual:", path_process_list, index=indice_padrao)
            valor_causa_raw = df_selecionado["VALOR_CAUSA"][0]
            case_value = st.text_input("Valor da Causa", str(0 if pd.isna(valor_causa_raw) else valor_causa_raw))
            def_case_value_raw = df_selecionado["VALOR_DEFERIDO_CAUSA"][0]
            def_case_value = st.text_input("Valor Deferido da Causa:", str(0 if pd.isna(def_case_value_raw) else def_case_value_raw))
            payed_value_raw = df_selecionado["VALOR_PAGO_CAUSA"][0]
            payed_value = st.text_input("Valor Pago pela Causa:", str(0 if pd.isna(payed_value_raw) else payed_value_raw))
            judge_name = st.text_input("Nome do Juiz:", df_selecionado["NOME_JUIZ"][0])
            obs = st.text_area("Observações sobre o Caso:", df_selecionado["OBSERVACOES_CLOB"][0])

            salvar = st.form_submit_button("Salvar Alterações")

            if salvar:
                # Aqui você atualizaria o banco de dados com os novos valores
                dict_edit_process(conn_user, cursor_user, process_path, case_value, def_case_value, payed_value, judge_name, obs, selecionado)
                st.success("Processo atualizado com sucesso!")
    
