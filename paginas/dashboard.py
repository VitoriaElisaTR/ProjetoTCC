import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from functions.functions import *
from config.auth import *

COR_PRIMARIA   = '#0B046E'
COR_SECUNDARIA = '#4B44C4'
PALETA = [
    '#0B046E','#4B44C4','#7B75E0','#A89FF0',
    '#C8C4F8','#F4A300','#F97B2C','#E8E6FF',
]
ETAPAS_ORDEM = [
    'Petição Inicial','Intimação','Notificação',
    'Contestação','Conciliação','Sentença','Apelação',
]


def _pct(n, total):
    return round(n / total * 100, 1) if total else 0


def _taxa_exito(g):
    total = len(g)
    ganhos = (g['VALOR_PAGO_CAUSA'] > 0).sum()
    deferidos = (g['VALOR_DEFERIDO_CAUSA'] > 0).sum()
    return pd.Series({
        'Total': total,
        'Com recebimento': int(ganhos),
        'Deferidos': int(deferidos),
        'Em aberto': int(total - ganhos - deferidos + (deferidos if ganhos == 0 else 0)),
    })


def dashboard():
    conn_user, cursor_user = conect_database_with_user()
    df_raw = make_db_process(cursor_user)

    topbar("Dashboard")

    if df_raw is None or df_raw.empty:
        st.info("Nenhum processo cadastrado ainda.")
        return

    df = df_raw.copy()
    for col in ['VALOR_CAUSA', 'VALOR_DEFERIDO_CAUSA', 'VALOR_PAGO_CAUSA']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'DATA_CADASTRO' in df.columns:
        df['DATA_CADASTRO'] = pd.to_datetime(df['DATA_CADASTRO'], errors='coerce')
        df['MES'] = df['DATA_CADASTRO'].dt.to_period('M').astype(str)
    else:
        df['MES'] = 'Sem data'

    total = len(df)
    encerrados  = int((df['VALOR_PAGO_CAUSA'] > 0).sum())
    deferidos   = int(((df['VALOR_DEFERIDO_CAUSA'] > 0) & (df['VALOR_PAGO_CAUSA'] == 0)).sum())
    em_aberto   = total - encerrados - deferidos
    taxa_global = _pct(encerrados, total)

    # ================================================================
    # CARDS GERAIS
    # ================================================================
    st.markdown("### Visão Geral")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total de Processos", total)
    c2.metric("Em Aberto", em_aberto)
    c3.metric("Deferidos", deferidos)
    c4.metric("Encerrados c/ Recebimento", encerrados)
    c5.metric("Taxa de Êxito Global", f"{taxa_global}%")

    st.divider()

    # ================================================================
    # LINHA 1 — Pizza de área + Barras por área
    # ================================================================
    st.markdown("### Distribuição por Área Jurídica")
    col_a, col_b = st.columns(2)

    df_area = df.groupby('CLASSE_PROCESSO', as_index=False).size().rename(columns={'size': 'Quantidade'})
    df_area['Percentual'] = df_area['Quantidade'].apply(lambda x: _pct(x, total))

    with col_a:
        st.markdown("#### % de Processos por Área")
        fig_pizza = px.pie(
            df_area, names='CLASSE_PROCESSO', values='Quantidade',
            color_discrete_sequence=PALETA, hole=0.38,
        )
        fig_pizza.update_traces(
            textposition='inside', textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>%{value} processos (%{percent})<extra></extra>',
        )
        fig_pizza.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10), height=340)
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_b:
        st.markdown("#### Quantidade de Processos por Área")
        df_area_s = df_area.sort_values('Quantidade', ascending=True)
        fig_area = px.bar(
            df_area_s, x='Quantidade', y='CLASSE_PROCESSO', orientation='h',
            text='Quantidade', color='Quantidade',
            color_continuous_scale=[[0,'#C8C4F8'],[1, COR_PRIMARIA]],
        )
        fig_area.update_traces(textposition='outside')
        fig_area.update_layout(
            coloraxis_showscale=False, xaxis_title='Processos',
            yaxis_title='', margin=dict(t=10,b=10,l=10,r=10), height=340,
        )
        st.plotly_chart(fig_area, use_container_width=True)

    st.divider()

    # ================================================================
    # LINHA 2 — Por etapa processual + evolução mensal
    # ================================================================
    st.markdown("### Etapa Processual e Evolução Temporal")
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("#### Processos por Etapa Processual")
        df_etapa = df.groupby('CAMINHO_PROCESSUAL', as_index=False).size().rename(columns={'size': 'Quantidade'})
        ordem_valida = [e for e in ETAPAS_ORDEM if e in df_etapa['CAMINHO_PROCESSUAL'].values]
        df_etapa['CAMINHO_PROCESSUAL'] = pd.Categorical(
            df_etapa['CAMINHO_PROCESSUAL'], categories=ordem_valida, ordered=True
        )
        df_etapa = df_etapa.sort_values('CAMINHO_PROCESSUAL')

        fig_etapa = px.funnel(
            df_etapa, x='Quantidade', y='CAMINHO_PROCESSUAL',
            color_discrete_sequence=[COR_PRIMARIA],
        )
        fig_etapa.update_layout(
            yaxis_title='', margin=dict(t=10,b=10,l=10,r=10), height=320,
        )
        st.plotly_chart(fig_etapa, use_container_width=True)

    with col_d:
        st.markdown("#### Novos Processos por Mês")
        if df['MES'].nunique() > 1:
            df_mensal = df.groupby('MES', as_index=False).size().rename(columns={'size': 'Novos'})
            df_mensal = df_mensal.sort_values('MES')
            df_mensal['Acumulado'] = df_mensal['Novos'].cumsum()

            fig_mensal = make_subplots(specs=[[{"secondary_y": True}]])
            fig_mensal.add_trace(
                go.Bar(x=df_mensal['MES'], y=df_mensal['Novos'], name='Novos no mês',
                       marker_color=COR_SECUNDARIA),
                secondary_y=False,
            )
            fig_mensal.add_trace(
                go.Scatter(x=df_mensal['MES'], y=df_mensal['Acumulado'], name='Acumulado',
                           mode='lines+markers', line=dict(color=COR_PRIMARIA, width=2)),
                secondary_y=True,
            )
            fig_mensal.update_layout(
                legend=dict(orientation='h', y=-0.25),
                margin=dict(t=10,b=10,l=10,r=10), height=320,
            )
            fig_mensal.update_yaxes(title_text='Novos processos', secondary_y=False)
            fig_mensal.update_yaxes(title_text='Total acumulado', secondary_y=True)
            st.plotly_chart(fig_mensal, use_container_width=True)
        else:
            st.info("Dados insuficientes para evolução mensal (processos em apenas 1 mês).")

    st.divider()

    # ================================================================
    # LINHA 3 — Por juiz + por tribunal
    # ================================================================
    st.markdown("### Distribuição por Juiz e Tribunal")
    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown("#### Top 10 — Processos por Juiz")
        df_juiz = (
            df.groupby('NOME_JUIZ', as_index=False).size()
            .rename(columns={'size': 'Quantidade'})
            .sort_values('Quantidade', ascending=False)
            .head(10)
            .sort_values('Quantidade', ascending=True)
        )
        fig_juiz = px.bar(
            df_juiz, x='Quantidade', y='NOME_JUIZ', orientation='h',
            text='Quantidade', color='Quantidade',
            color_continuous_scale=[[0,'#C8C4F8'],[1, COR_PRIMARIA]],
        )
        fig_juiz.update_traces(textposition='outside')
        fig_juiz.update_layout(
            coloraxis_showscale=False, yaxis_title='',
            margin=dict(t=10,b=10,l=10,r=10), height=340,
        )
        st.plotly_chart(fig_juiz, use_container_width=True)

    with col_f:
        st.markdown("#### Processos por Tribunal")
        df_trib = (
            df.groupby('TRIBUNAL', as_index=False).size()
            .rename(columns={'size': 'Quantidade'})
            .sort_values('Quantidade', ascending=False)
            .head(12)
        )
        fig_trib = px.treemap(
            df_trib, path=['TRIBUNAL'], values='Quantidade',
            color='Quantidade',
            color_continuous_scale=[[0,'#C8C4F8'],[1, COR_PRIMARIA]],
        )
        fig_trib.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=10,b=10,l=10,r=10), height=340,
        )
        st.plotly_chart(fig_trib, use_container_width=True)

    st.divider()

    # ================================================================
    # LINHA 4 — Taxa de êxito por área + por rito
    # ================================================================
    st.markdown("### Análise de Probabilidade e Êxito")
    col_g, col_h = st.columns(2)

    with col_g:
        st.markdown("#### Taxa de Êxito por Área (%)")
        df_ex = df.groupby('CLASSE_PROCESSO').apply(_taxa_exito, include_groups=False).reset_index()
        df_ex['Taxa (%)'] = (df_ex['Com recebimento'] / df_ex['Total'] * 100).round(1)
        df_ex = df_ex.sort_values('Taxa (%)', ascending=True)

        fig_ex = px.bar(
            df_ex, x='Taxa (%)', y='CLASSE_PROCESSO', orientation='h',
            text='Taxa (%)', color='Taxa (%)',
            color_continuous_scale=[[0,'#E8E6FF'],[0.5,'#4B44C4'],[1,'#0B046E']],
            range_color=[0,100],
        )
        fig_ex.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_ex.update_layout(
            coloraxis_showscale=False, xaxis_range=[0,115],
            xaxis_title='% com recebimento', yaxis_title='',
            margin=dict(t=10,b=10,l=10,r=10), height=320,
        )
        st.plotly_chart(fig_ex, use_container_width=True)

    with col_h:
        st.markdown("#### Probabilidade de Êxito por Rito Processual")

        df_rito = df.groupby('RITO_PROCESSO').apply(
            lambda g: pd.Series({
                'Total': len(g),
                'Com recebimento': int((g['VALOR_PAGO_CAUSA'] > 0).sum()),
            }), include_groups=False
        ).reset_index()
        df_rito['Taxa (%)'] = (df_rito['Com recebimento'] / df_rito['Total'] * 100).round(1)

        fig_rito = go.Figure()
        fig_rito.add_trace(go.Bar(
            name='Total', x=df_rito['RITO_PROCESSO'], y=df_rito['Total'],
            marker_color='#C8C4F8',
        ))
        fig_rito.add_trace(go.Bar(
            name='Com recebimento', x=df_rito['RITO_PROCESSO'], y=df_rito['Com recebimento'],
            marker_color=COR_PRIMARIA,
            text=[f"{t}%" for t in df_rito['Taxa (%)']],
            textposition='outside',
        ))
        fig_rito.update_layout(
            barmode='overlay',
            legend=dict(orientation='h', y=-0.25),
            yaxis_title='Processos', xaxis_title='Rito',
            margin=dict(t=10,b=10,l=10,r=10), height=320,
        )
        st.plotly_chart(fig_rito, use_container_width=True)

    st.divider()

    # ================================================================
    # LINHA 5 — Mapa de calor etapa × área + estado
    # ================================================================
    st.markdown("### Análises Cruzadas")
    col_i, col_j = st.columns(2)

    with col_i:
        st.markdown("#### Mapa de Calor — Área × Etapa Processual")
        df_heat = (
            df.groupby(['CLASSE_PROCESSO','CAMINHO_PROCESSUAL'], as_index=False)
            .size().rename(columns={'size': 'Qtd'})
        )
        df_pivot = df_heat.pivot(index='CLASSE_PROCESSO', columns='CAMINHO_PROCESSUAL', values='Qtd').fillna(0)
        cols_ord = [c for c in ETAPAS_ORDEM if c in df_pivot.columns]
        df_pivot = df_pivot[cols_ord]

        fig_heat = px.imshow(
            df_pivot, text_auto=True,
            color_continuous_scale=[[0,'#FFFFFF'],[1, COR_PRIMARIA]],
            aspect='auto',
        )
        fig_heat.update_layout(
            xaxis_title='Etapa', yaxis_title='',
            coloraxis_showscale=False,
            margin=dict(t=10,b=10,l=10,r=10), height=320,
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_j:
        st.markdown("#### Processos por Estado (UF)")
        df_uf = (
            df.groupby('ESTADO_PROCESSO', as_index=False).size()
            .rename(columns={'size': 'Quantidade'})
            .sort_values('Quantidade', ascending=False)
        )
        fig_uf = px.bar(
            df_uf, x='ESTADO_PROCESSO', y='Quantidade',
            text='Quantidade', color='Quantidade',
            color_continuous_scale=[[0,'#C8C4F8'],[1, COR_PRIMARIA]],
        )
        fig_uf.update_traces(textposition='outside')
        fig_uf.update_layout(
            coloraxis_showscale=False,
            xaxis_title='Estado', yaxis_title='Processos',
            margin=dict(t=10,b=10,l=10,r=10), height=320,
        )
        st.plotly_chart(fig_uf, use_container_width=True)

    st.divider()

    # ================================================================
    # LINHA 6 — Probabilidade bayesiana simples + Tabela resumo
    # ================================================================
    st.markdown("### Probabilidade Estimada de Êxito")

    st.caption(
        "Estimativa baseada no histórico de processos encerrados com recebimento no escritório. "
        "Quanto mais processos cadastrados, mais precisa a estimativa."
    )

    df_prob = df.groupby('CLASSE_PROCESSO').apply(
        lambda g: pd.Series({
            'Processos': len(g),
            'Encerrados c/ ganho': int((g['VALOR_PAGO_CAUSA'] > 0).sum()),
            'Deferidos': int(((g['VALOR_DEFERIDO_CAUSA'] > 0) & (g['VALOR_PAGO_CAUSA'] == 0)).sum()),
            'Em aberto': int(((g['VALOR_PAGO_CAUSA'] == 0) & (g['VALOR_DEFERIDO_CAUSA'] == 0)).sum()),
            'Valor médio em causa (R$)': round(g['VALOR_CAUSA'].mean(), 2),
            'Valor médio recebido (R$)': round(g.loc[g['VALOR_PAGO_CAUSA'] > 0, 'VALOR_PAGO_CAUSA'].mean() if (g['VALOR_PAGO_CAUSA'] > 0).any() else 0, 2),
        }), include_groups=False
    ).reset_index()

    encerrados_total = df_prob['Encerrados c/ ganho'].sum()
    processos_total  = df_prob['Processos'].sum()

    # prior bayesiano: proporção global de êxito como prior
    prior = encerrados_total / processos_total if processos_total > 0 else 0.5

    def prob_bayesiana(row):
        n   = row['Processos']
        k   = row['Encerrados c/ ganho']
        # estimativa de Laplace suavizada com prior global
        alpha = prior * 5
        beta  = (1 - prior) * 5
        return round((k + alpha) / (n + alpha + beta) * 100, 1)

    df_prob['Prob. Êxito (%)'] = df_prob.apply(prob_bayesiana, axis=1)
    df_prob['Valor médio em causa (R$)'] = df_prob['Valor médio em causa (R$)'].apply(
        lambda v: f"R$ {v:,.2f}".replace(',','X').replace('.',',').replace('X','.')
    )
    df_prob['Valor médio recebido (R$)'] = df_prob['Valor médio recebido (R$)'].apply(
        lambda v: f"R$ {v:,.2f}".replace(',','X').replace('.',',').replace('X','.')
    )

    col_k, col_l = st.columns([2, 1])

    with col_k:
        st.markdown("#### Tabela de Probabilidade por Área")
        st.dataframe(
            df_prob.rename(columns={'CLASSE_PROCESSO': 'Área Jurídica'}),
            use_container_width=True, hide_index=True,
        )

    with col_l:
        st.markdown("#### Probabilidade Estimada — Gauge")
        area_selecionada = st.selectbox(
            "Selecione a área:",
            df_prob['CLASSE_PROCESSO'].tolist(),
            key='gauge_area'
        )
        prob_val = float(df_prob.loc[
            df_prob['CLASSE_PROCESSO'] == area_selecionada, 'Prob. Êxito (%)'
        ].values[0])

        cor_gauge = (
            '#2ecc71' if prob_val >= 60 else
            '#F4A300' if prob_val >= 35 else
            '#e74c3c'
        )

        fig_gauge = go.Figure(go.Indicator(
            mode='gauge+number+delta',
            value=prob_val,
            number={'suffix': '%', 'font': {'size': 36, 'color': COR_PRIMARIA}},
            delta={'reference': taxa_global, 'suffix': '%', 'relative': False},
            title={'text': f"<b>{area_selecionada}</b><br><span style='font-size:11px'>vs. média geral {taxa_global}%</span>"},
            gauge={
                'axis': {'range': [0, 100], 'ticksuffix': '%'},
                'bar': {'color': cor_gauge},
                'steps': [
                    {'range': [0,  35], 'color': '#fdecea'},
                    {'range': [35, 60], 'color': '#fff8e1'},
                    {'range': [60,100], 'color': '#e8f5e9'},
                ],
                'threshold': {
                    'line': {'color': COR_PRIMARIA, 'width': 3},
                    'thickness': 0.75,
                    'value': taxa_global,
                },
            },
        ))
        fig_gauge.update_layout(
            margin=dict(t=60,b=10,l=20,r=20), height=280,
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()

    # ================================================================
    # TABELA FINAL — todos os processos
    # ================================================================
    st.markdown("### Todos os Processos")
    cols_tabela = ['NUMERO_PROCESSO','CLASSE_PROCESSO','NOME_CLIENTE_EMPRESA',
                   'CAMINHO_PROCESSUAL','NOME_JUIZ','ESTADO_PROCESSO','JUSTICA','TRIBUNAL']
    cols_ok = [c for c in cols_tabela if c in df.columns]
    st.dataframe(
        df[cols_ok].rename(columns={
            'NUMERO_PROCESSO':     'Nº Processo',
            'CLASSE_PROCESSO':     'Classe',
            'NOME_CLIENTE_EMPRESA':'Cliente/Empresa',
            'CAMINHO_PROCESSUAL':  'Etapa',
            'NOME_JUIZ':           'Juiz',
            'ESTADO_PROCESSO':     'UF',
            'JUSTICA':             'Justiça',
            'TRIBUNAL':            'Tribunal',
        }),
        use_container_width=True, hide_index=True,
    )
