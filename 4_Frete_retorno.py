import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar

st.set_page_config(layout="wide")

def carregar_dados():
    st.sidebar.subheader("📂 Upload da Base de Dados (opcional)")
    arquivo = st.sidebar.file_uploader("Envie o arquivo Excel (.xlsx)", type=["xlsx"])

    if arquivo is not None:
        df = pd.read_excel(arquivo, index_col=0)
    else:
        df = pd.read_excel('Frete Retorno.xlsx', index_col=0)  # base padrão no repo

    df = df.rename(columns={"Grupo": "Cliente"})

    for col in ['Data Demanda', 'Data Carregamento', 'ETA Chegada Cliente', 'Saida do Cliente']:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    df['TempoCarregameto_x_Demanda (Dia)'] = (
        (df['Data Carregamento'] - df['Data Demanda']).dt.days)
    df['TempoETA_x_Carregamento (Dia)'] = (
        (df['ETA Chegada Cliente'] - df['Data Carregamento']).dt.days)
    df['Permanencia_cliente (Hora)'] = (
        np.floor((df['Saida do Cliente'] - df['ETA Chegada Cliente']).dt.total_seconds() / 3600)
        .fillna(0).astype(int))

    return df

def classificar_faixa(valor):
    if pd.isna(valor):
        return 'Inválido'
    elif valor < 0:
        return 'A - < 0'
    elif 0 <= valor <= 2:
        return 'B - [1-2]'
    elif 2 < valor <= 4:
        return 'C - [3-4]'
    elif 4 < valor <= 6:
        return 'D - [5-6]'
    elif 6 < valor <= 8:
        return 'E - [7-8]'
    elif 8 < valor <= 10:
        return 'F - [9-10]'
    else:
        return 'G - > 10'

# --- Carregamento ---
df = carregar_dados()

# --- Filtros ---
st.sidebar.header("Filtros")
anos = df["Data Demanda"].dt.year.dropna().unique()
ano_selecionado = st.sidebar.selectbox("Ano", sorted(anos, reverse=True))

meses = df[df["Data Demanda"].dt.year == ano_selecionado]["Data Demanda"].dt.month.dropna().unique()
mes_opcoes = ["Todos"] + sorted(meses)
mes_selecionado = st.sidebar.selectbox("Mês", mes_opcoes)

clientes = df["Cliente"].dropna().unique()
cliente_selecionado = st.sidebar.multiselect("Clientes", options=clientes)

regioes = df["Perimetro"].dropna().unique()
regiao_selecionado = st.sidebar.multiselect("Região", options=regioes)

# --- Aplicando Filtros ---
df_filtrada = df[df['Data Demanda'].dt.year == ano_selecionado].copy()
if mes_selecionado != "Todos":
    df_filtrada = df_filtrada[df_filtrada['Data Demanda'].dt.month == int(mes_selecionado)]
if cliente_selecionado:
    df_filtrada = df_filtrada[df_filtrada['Cliente'].isin(cliente_selecionado)]

# --- Criando Faixas ---
df_filtrada['Faixa_TempoCarregamento'] = df_filtrada['TempoCarregameto_x_Demanda (Dia)'].apply(classificar_faixa)
df_filtrada['Faixa_TempoEntrega'] = df_filtrada['TempoETA_x_Carregamento (Dia)'].apply(classificar_faixa)
df_filtrada['Faixa_TempoPermanencia'] = df_filtrada['Permanencia_cliente (Hora)'].apply(classificar_faixa)

# --- Dashboard ---
st.title("Dashboard Frete Retorno")

# Linha 1: Pizza e Card Total Pedidos
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Volume por Produto")
    produto_x_volume = df_filtrada.groupby('Produto')['Volume'].sum().sort_values(ascending=False).replace(",",".")
    

    # Cores: verde para maior, amarelo para menor
    cores_personalizadas = ['#008000' if i == 0 else '#FFD700' for i in range(len(produto_x_volume))]

    fig_pizza = go.Figure(data=[
        go.Pie(
            labels=produto_x_volume.index,
            values=produto_x_volume.values,
            hole=0.4,
            textinfo='label+percent+value',
            marker=dict(colors=cores_personalizadas)
        )
    ])
    fig_pizza.update_layout(title='Distribuição de Volume por Produto')
    st.plotly_chart(fig_pizza, use_container_width=True)

with col2:
    total_pedidos = df_filtrada.shape[0]
    valor_formatado = format(total_pedidos, ",").replace(",",".")
    st.metric(label="Total de Pedidos", value=valor_formatado)

# Linha 2: Clientes Diretos
st.subheader("Top 10 Clientes Diretos")
valores = df_filtrada['Cliente'].value_counts().head(10)
fig_clientes = go.Figure(data=[
    go.Bar(x=valores.index, y=valores.values, text=valores.values, textposition='auto', marker_color='#008000')
])
fig_clientes.update_layout(title="Top 10 Clientes Diretos")
st.plotly_chart(fig_clientes, use_container_width=True)

# Linha 3: Bases, SLA 2, Status
col3, col4, col5 = st.columns(3)

with col3:
    st.subheader("Bases de Carregamento")
    valores = df_filtrada['Base Carregamento'].value_counts()
    fig_base = go.Figure(data=[
        go.Bar(x=valores.index, y=valores.values, text=valores.values, textposition='auto', marker_color='#008000')
    ])
    st.plotly_chart(fig_base, use_container_width=True)

with col4:
    st.subheader("Solicitações em Tempo")
    valores = df_filtrada['SLA 2'].value_counts()
    fig_sla = go.Figure(data=[
        go.Bar(x=valores.index, y=valores.values, text=valores.values, textposition='auto', marker_color='#008000')
    ])
    st.plotly_chart(fig_sla, use_container_width=True)

with col5:
    st.subheader("Status da Entrega")
    valores = df_filtrada['Status da Entrega'].value_counts()
    fig_status = go.Figure(data=[
        go.Bar(x=valores.index, y=valores.values, text=valores.values, textposition='auto', marker_color='#008000')
    ])
    st.plotly_chart(fig_status, use_container_width=True)

# Linha 4: Faixas lado a lado
col6, col7, col8 = st.columns(3)
ordem_faixas = ['A - < 0', 'B - [1-2]', 'C - [3-4]', 'D - [5-6]', 'E - [7-8]', 'F - [9-10]', 'G - > 10']

with col6:
    st.subheader("Faixa de Carregamento")
    dados = df_filtrada.groupby('Faixa_TempoCarregamento')['TempoCarregameto_x_Demanda (Dia)'].count().reindex(ordem_faixas, fill_value=0)
    fig = go.Figure([go.Bar(x=dados.index, y=dados.values, text=dados.values, textposition='auto', marker_color='#008000')])
    st.plotly_chart(fig, use_container_width=True)

with col7:
    st.subheader("Faixa de Entrega")
    dados = df_filtrada.groupby('Faixa_TempoEntrega')['TempoETA_x_Carregamento (Dia)'].count().reindex(ordem_faixas, fill_value=0)
    fig = go.Figure([go.Bar(x=dados.index, y=dados.values, text=dados.values, textposition='auto', marker_color='#008000')])
    st.plotly_chart(fig, use_container_width=True)

with col8:
    st.subheader("Faixa de Permanência")
    dados = df_filtrada.groupby('Faixa_TempoPermanencia')['Permanencia_cliente (Hora)'].count().reindex(ordem_faixas, fill_value=0)
    fig = go.Figure([go.Bar(x=dados.index, y=dados.values, text=dados.values, textposition='auto', marker_color='#008000')])
    st.plotly_chart(fig, use_container_width=True)

# Linha 5: Evolução Mensal
st.subheader("Evolução de Volume por Mês")

df_volume_mensal = df[df['Data Demanda'].dt.year == ano_selecionado].copy()
df_volume_mensal['Mes'] = df_volume_mensal['Data Demanda'].dt.month

volume_mensal = df_volume_mensal.groupby('Mes')['Volume'].sum().reset_index()
volume_mensal['Nome_Mes'] = volume_mensal['Mes'].apply(lambda x: calendar.month_name[x])
volume_mensal = volume_mensal.sort_values('Mes')

fig_linha = px.line(volume_mensal, x='Nome_Mes', y='Volume', markers=True,
                    title=f'Volume Total por Mês - {ano_selecionado}',
                    line_shape='linear')
fig_linha.update_traces(line_color='#008000',
                        text=volume_mensal['Volume'],
                        textposition='top center')

st.plotly_chart(fig_linha, use_container_width=True)
