import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from functions.functions import *
from config.auth import *

ETAPAS_ENCERRADAS = ['Sentença', 'Apelação']
COR_PRIMARIA = '#0B046E'
COR_SECUNDARIA = '#4B44C4'
PALETA = [
    '#0B046E', '#4B44C4', '#7B75E0', '#A89FF0',
    '#C8C4F8', '#E8E6FF', '#F4A300', '#F97B2C'
]


def _formata_reais(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def _classifica_status(row):
    if row['VALOR_PAGO_CAUSA'] > 0:
        return 'Encerrado com recebimento'
    if row['VALOR_DEFERIDO_CAUSA'] > 0:
        return 'Deferido — aguardando pagamento'
    if row['CAMINHO_PROCESSUAL'] in ETAPAS_ENCERRADAS and row['VALOR_CAUSA'] == 0:
        return 'Encerrado sem valor monetário'
    return 'Em aberto'


def financial_area():
    conn_user, cursor_user = conect_database_with_user()
    df_raw = make_db_process(cursor_user)

    topbar("Área Financeira")

    if df_raw is None or df_raw.empty:
        st.info("Nenhum processo cadastrado ainda. Cadastre processos para visualizar os dados financeiros.")
        return

    # --- Preparação dos dados ---
    df = df_raw.copy()
    for col in ['VALOR_CAUSA', 'VALOR_DEFERIDO_CAUSA', 'VALOR_PAGO_CAUSA']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'DATA_CADASTRO' in df.columns:
        df['DATA_CADASTRO'] = pd.to_datetime(df['DATA_CADASTRO'], errors='coerce')
        df['MES_CADASTRO'] = df['DATA_CADASTRO'].dt.to_period('M').astype(str)
    else:
        df['MES_CADASTRO'] = 'Sem data'

    df['STATUS'] = df.apply(_classifica_status, axis=1)

    total_causa     = df['VALOR_CAUSA'].sum()
    total_deferido  = df['VALOR_DEFERIDO_CAUSA'].sum()
    total_pago      = df['VALOR_PAGO_CAUSA'].sum()
    total_aberto    = df[df['STATUS'] == 'Em aberto']['VALOR_CAUSA'].sum()
    n_processos     = len(df)
    n_encerrados    = df[df['VALOR_PAGO_CAUSA'] > 0].shape[0]

    # ================================================================
    # CARDS DE RESUMO
    # ================================================================
    st.markdown("### Resumo Geral")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total de Processos", n_processos)
    c2.metric("Valor Total em Causa", _formata_reais(total_causa))
    c3.metric("Total Deferido", _formata_reais(total_deferido))
    c4.metric("Total Recebido", _formata_reais(total_pago))
    c5.metric("Em Aberto (causa)", _formata_reais(total_aberto))

    st.divider()

    # ================================================================
    # LINHA 1 — Pizza de rentabilidade + Barras por área
    # ================================================================
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Participação por Área Jurídica (% do valor em causa)")

        df_pizza = (
            df.groupby('CLASSE_PROCESSO', as_index=False)['VALOR_CAUSA']
            .sum()
            .rename(columns={'VALOR_CAUSA': 'VALOR'})
        )
        df_pizza['VALOR'] = df_pizza['VALOR'].clip(lower=0.01)

        fig_pizza = px.pie(
            df_pizza,
            names='CLASSE_PROCESSO',
            values='VALOR',
            color_discrete_sequence=PALETA,
            hole=0.35,
        )
        fig_pizza.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>%{percent}<extra></extra>',
        )
        fig_pizza.update_layout(
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=340,
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_b:
        st.markdown("#### Valores por Área (Causa × Deferido × Recebido)")

        df_barras = (
            df.groupby('CLASSE_PROCESSO', as_index=False)
            .agg(
                Causa=('VALOR_CAUSA', 'sum'),
                Deferido=('VALOR_DEFERIDO_CAUSA', 'sum'),
                Recebido=('VALOR_PAGO_CAUSA', 'sum'),
            )
            .sort_values('Causa', ascending=False)
        )

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Valor em Causa',   x=df_barras['CLASSE_PROCESSO'], y=df_barras['Causa'],    marker_color=COR_PRIMARIA))
        fig_bar.add_trace(go.Bar(name='Valor Deferido',   x=df_barras['CLASSE_PROCESSO'], y=df_barras['Deferido'], marker_color=COR_SECUNDARIA))
        fig_bar.add_trace(go.Bar(name='Valor Recebido',   x=df_barras['CLASSE_PROCESSO'], y=df_barras['Recebido'], marker_color='#F4A300'))
        fig_bar.update_layout(
            barmode='group',
            xaxis_tickangle=-30,
            yaxis_tickprefix='R$ ',
            yaxis_tickformat=',.0f',
            legend=dict(orientation='h', y=-0.3),
            margin=dict(t=10, b=10, l=10, r=10),
            height=340,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ================================================================
    # LINHA 2 — Progressão mensal + Status dos processos
    # ================================================================
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("#### Evolução Mensal de Valores")

        if 'DATA_CADASTRO' in df.columns and df['DATA_CADASTRO'].notna().any():
            df_mensal = (
                df.groupby('MES_CADASTRO', as_index=False)
                .agg(
                    Causa=('VALOR_CAUSA', 'sum'),
                    Deferido=('VALOR_DEFERIDO_CAUSA', 'sum'),
                    Recebido=('VALOR_PAGO_CAUSA', 'sum'),
                )
                .sort_values('MES_CADASTRO')
            )
            df_mensal['Causa_acum']    = df_mensal['Causa'].cumsum()
            df_mensal['Deferido_acum'] = df_mensal['Deferido'].cumsum()
            df_mensal['Recebido_acum'] = df_mensal['Recebido'].cumsum()

            fig_linha = go.Figure()
            fig_linha.add_trace(go.Scatter(
                x=df_mensal['MES_CADASTRO'], y=df_mensal['Causa_acum'],
                name='Causa acumulada', mode='lines+markers',
                line=dict(color=COR_PRIMARIA, width=2),
            ))
            fig_linha.add_trace(go.Scatter(
                x=df_mensal['MES_CADASTRO'], y=df_mensal['Deferido_acum'],
                name='Deferido acumulado', mode='lines+markers',
                line=dict(color=COR_SECUNDARIA, width=2, dash='dash'),
            ))
            fig_linha.add_trace(go.Scatter(
                x=df_mensal['MES_CADASTRO'], y=df_mensal['Recebido_acum'],
                name='Recebido acumulado', mode='lines+markers',
                line=dict(color='#F4A300', width=2),
                fill='tozeroy', fillcolor='rgba(244,163,0,0.08)',
            ))
            fig_linha.update_layout(
                yaxis_tickprefix='R$ ',
                yaxis_tickformat=',.0f',
                xaxis_title='Mês',
                legend=dict(orientation='h', y=-0.3),
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
            )
            st.plotly_chart(fig_linha, use_container_width=True)
        else:
            st.info("Data de cadastro não disponível para gerar evolução mensal.")

    with col_d:
        st.markdown("#### Processos por Status Financeiro")

        df_status = df.groupby('STATUS', as_index=False).size().rename(columns={'size': 'Quantidade'})
        cores_status = {
            'Encerrado com recebimento':       '#0B046E',
            'Deferido — aguardando pagamento': '#4B44C4',
            'Encerrado sem valor monetário':   '#A89FF0',
            'Em aberto':                       '#F4A300',
        }
        df_status['Cor'] = df_status['STATUS'].map(cores_status).fillna('#CCCCCC')

        fig_status = px.bar(
            df_status,
            x='Quantidade',
            y='STATUS',
            orientation='h',
            color='STATUS',
            color_discrete_map=cores_status,
            text='Quantidade',
        )
        fig_status.update_traces(textposition='outside')
        fig_status.update_layout(
            showlegend=False,
            xaxis_title='Nº de processos',
            yaxis_title='',
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig_status, use_container_width=True)

    st.divider()

    # ================================================================
    # LINHA 3 — Taxa de êxito + Processos por justiça
    # ================================================================
    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown("#### Taxa de Êxito por Área")

        df_exito = df.groupby('CLASSE_PROCESSO').apply(
            lambda g: pd.Series({
                'Total': len(g),
                'Com recebimento': (g['VALOR_PAGO_CAUSA'] > 0).sum(),
            })
        ).reset_index()
        df_exito['Taxa (%)'] = (df_exito['Com recebimento'] / df_exito['Total'] * 100).round(1)
        df_exito = df_exito[df_exito['Total'] > 0].sort_values('Taxa (%)', ascending=True)

        fig_exito = px.bar(
            df_exito,
            x='Taxa (%)',
            y='CLASSE_PROCESSO',
            orientation='h',
            text='Taxa (%)',
            color='Taxa (%)',
            color_continuous_scale=[[0, '#E8E6FF'], [1, COR_PRIMARIA]],
            range_color=[0, 100],
        )
        fig_exito.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_exito.update_layout(
            coloraxis_showscale=False,
            xaxis_range=[0, 110],
            xaxis_title='% processos com recebimento',
            yaxis_title='',
            margin=dict(t=10, b=10, l=10, r=10),
            height=300,
        )
        st.plotly_chart(fig_exito, use_container_width=True)

    with col_f:
        st.markdown("#### Distribuição por Ramo da Justiça")

        df_justica = (
            df.groupby('JUSTICA', as_index=False)
            .agg(Processos=('NUMERO_PROCESSO', 'count'), Valor=('VALOR_CAUSA', 'sum'))
        )
        fig_jus = px.treemap(
            df_justica,
            path=['JUSTICA'],
            values='Processos',
            color='Valor',
            color_continuous_scale=[[0, '#C8C4F8'], [1, COR_PRIMARIA]],
            hover_data={'Valor': ':,.2f'},
        )
        fig_jus.update_coloraxes(colorbar_title='Valor R$')
        fig_jus.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=300,
        )
        st.plotly_chart(fig_jus, use_container_width=True)

    st.divider()

    # ================================================================
    # TABELA DETALHADA
    # ================================================================
    st.markdown("#### Detalhamento por Processo")

    colunas_exibir = ['NUMERO_PROCESSO', 'CLASSE_PROCESSO', 'NOME_CLIENTE_EMPRESA',
                      'CAMINHO_PROCESSUAL', 'VALOR_CAUSA', 'VALOR_DEFERIDO_CAUSA',
                      'VALOR_PAGO_CAUSA', 'STATUS']
    colunas_disponiveis = [c for c in colunas_exibir if c in df.columns]
    df_tabela = df[colunas_disponiveis].copy()

    df_tabela = df_tabela.rename(columns={
        'NUMERO_PROCESSO':       'Nº Processo',
        'CLASSE_PROCESSO':       'Classe',
        'NOME_CLIENTE_EMPRESA':  'Cliente/Empresa',
        'CAMINHO_PROCESSUAL':    'Etapa',
        'VALOR_CAUSA':           'Valor Causa (R$)',
        'VALOR_DEFERIDO_CAUSA':  'Valor Deferido (R$)',
        'VALOR_PAGO_CAUSA':      'Valor Recebido (R$)',
        'STATUS':                'Status',
    })

    st.dataframe(
        df_tabela.style.format({
            'Valor Causa (R$)':    'R$ {:,.2f}',
            'Valor Deferido (R$)': 'R$ {:,.2f}',
            'Valor Recebido (R$)': 'R$ {:,.2f}',
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Totais da tabela
    t1, t2, t3 = st.columns(3)
    t1.metric("Total Causa",    _formata_reais(df_tabela['Valor Causa (R$)'].sum()))
    t2.metric("Total Deferido", _formata_reais(df_tabela['Valor Deferido (R$)'].sum()))
    t3.metric("Total Recebido", _formata_reais(df_tabela['Valor Recebido (R$)'].sum()))
