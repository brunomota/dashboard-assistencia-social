import altair as alt
import streamlit as st
import pandas as pd
from PIL import Image
import json
import os
import numpy as np
import subprocess
import gdown
import time
import tempfile
import streamlit.components.v1 as components

# Desabilitanto o limite de 5.000 linhas de df do Altair
alt.data_transformers.enable('default', max_rows=None)

st.set_page_config(layout="wide")

# Definindo o diretório onde os arquivos serão salvos
dataset_dir = 'dataset'


# Exibindo um spinner enquanto o aplicativo é carregado
with st.spinner("Carregando arquivos..."):
    progress_text = "Aguarde..."
    my_bar = st.progress(0, text=progress_text)
    arquivos_para_baixar = {
        'municipios.csv': {
            'url': 'https://docs.google.com/uc?export=download&id=1NJ61uT7DjRNjq2T5hPLX325QCjgX0v_8',
            'nome_completo': os.path.join(dataset_dir, 'municipios.csv')
        },
        'cadunico.csv': {
            'url': 'https://docs.google.com/uc?export=download&id=1rQcmgk4YIDKBxP8ibgPN6ieHLWlxIk6w',
            'nome_completo': os.path.join(dataset_dir, 'cadunico.csv')
        },
        'Brasil.json': {
            'url': 'https://docs.google.com/uc?export=download&id=1W-9gmx9Rd9uXuYc6i9UO0Puiqz_HW97l',
            'nome_completo': os.path.join(dataset_dir, 'Brasil.json')
        },
        'ibge_populacao.csv': {
            'url': 'https://docs.google.com/uc?export=download&id=1am2PX_1fHyMN4GJDL2O7neMWPIR3d-3c',
            'nome_completo': os.path.join(dataset_dir, 'ibge_populacao.csv')
        },
        'logo.png':{
            'url': 'https://docs.google.com/uc?export=download&id=1DLW0mlRix4Gzd9h_TAnLN2v5Ht2YnX2e',
            'nome_completo': os.path.join('logo.png')	
        }
    }

    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)
        st.write(f" ${dataset_dir} já criado ")
    # Itera sobre o dicionário de arquivos para download
    total_arquivos = len(arquivos_para_baixar)+2
    for idx, (arquivo, info) in enumerate(arquivos_para_baixar.items(), 1):
        arquivo_path = info['nome_completo']
        url = info['url']
        # Calcula a porcentagem concluída
        porcentagem_concluida = int((idx / total_arquivos) * 100)

        # Verifica se o arquivo já existe, senão faz o download
        if not os.path.exists(arquivo_path):
            gdown.download(url, arquivo_path, quiet=False)
            print(f'Arquivo {arquivo} baixado para {dataset_dir}.')
        else:
            print(f'Arquivo {arquivo} já existe em {dataset_dir}.')

        my_bar.progress(value=porcentagem_concluida, text=arquivo)

    my_bar.progress(value=99, text="git clone https://github.com/luizpedone/municipal-brazilian-geodata")

    # Executa o comando shell
    if not os.path.exists("municipal-brazilian-geodata"):
        resultado = subprocess.run("git clone https://github.com/luizpedone/municipal-brazilian-geodata", shell=True, capture_output=True, text=True)

    my_bar.progress(value=99, text="git clone https://github.com/tbrugz/geodata-br.git")

    if not os.path.exists("geodata-br"):
        resultado = subprocess.run("git clone https://github.com/tbrugz/geodata-br", shell=True, capture_output=True, text=True)

    with open('geodata-br/geojson/geojs-100-mun.json', encoding='utf-8') as f:
        geo_data_mun = json.load(f)

    # Exibindo o restante do aplicativo após o carregamento
    st.empty()
    my_bar.empty()


# Função para ler o arquivo CSV
@st.cache_data  # Use st.cache_data para dados que não mudam com o tempo
def carregar_arquivos():

    df_mun = pd.read_csv("dataset/municipios.csv")
    df_cadunico = pd.read_csv("dataset/cadunico.csv")
    df_populacao = pd.read_csv("dataset/ibge_populacao.csv")

    # Ajustar o código do município para ter apenas seis dígitos
    df_mun['CD_MUN_TRUNC'] = df_mun['CD_MUN'].astype(str).str[:-1].astype(int)

    # Seu código para mesclar os dataframes
    df_temp = pd.merge(df_mun, df_populacao, how='left', right_on=['uf', 'nome_municipio'], left_on=['SIGLA_UF', 'NM_MUN'])

    # Preencher valores ausentes com zero
    df_temp['populacao'].fillna(0.0, inplace=True)
    df_temp['cod_municipio'].fillna(0, inplace=True)
    df_temp['nome_municipio'].fillna('', inplace=True)
    df_temp['uf'].fillna('', inplace=True)

    df_dados = pd.merge(df_temp, df_cadunico, how='inner', left_on='CD_MUN_TRUNC', right_on='codigo_ibge')

    # Remover a coluna redundante
    df_dados.drop('codigo_ibge', axis=1, inplace=True)
    df_dados.drop('CD_MUN_TRUNC', axis=1, inplace=True)
    df_dados.drop('uf', axis=1, inplace=True)
    df_dados.drop('nome_municipio', axis=1, inplace=True)
    df_dados.drop('cod_municipio', axis=1, inplace=True)

    # Dividir a coluna AnoMes em Ano e Mês
    df_dados['Ano'] = (df_dados['anomes_s'] // 100).astype(str)
    df_dados['Mes'] = df_dados['anomes_s'] % 100

    # Renomear colunas
    df_dados.rename(columns={
        'NM_MUN': 'nome_municipio',
        'SIGLA_UF': 'sigla_UF',
        'AREA_KM2': 'area_km2',
        'CD_MUN': 'codigo_IBGE',
        'anomes_s': 'AnoMes',
        'cadun_qtd_pessoas_cadastradas_pobreza_pbf_i': 'Qtd_Programa_Bolsa_Familia',
        'cadun_qtd_pessoas_cadastradas_baixa_renda_i': 'Qtd_Baixa_Renda',
        'cadun_qtd_pessoas_cadastradas_rfpc_ate_meio_sm_i': 'Qtd_RFPC_Ate_Metade_SM',
        'cadun_qtd_pessoas_cadastradas_rfpc_acima_meio_sm_i': 'Qtd_RFPC_Acima_Metade_SM'
    }, inplace=True)

    # Calcula a soma dos Cadastros
    df_dados['Qtd_Cadastros'] = df_dados[['Qtd_RFPC_Ate_Metade_SM',
                               'Qtd_RFPC_Acima_Metade_SM']].abs().sum(axis=1)

    # Encontrando o valor máximo em cada linha
    valor_maximo = df_dados[['Qtd_RFPC_Ate_Metade_SM', 'Qtd_RFPC_Acima_Metade_SM']].sum(axis=1)

    # Verificar se a população é zero antes de calcular a porcentagem
    df_dados['Perc_Cadastros'] = np.where(df_dados['populacao'] == 0, 0, ((valor_maximo / df_dados['populacao']) * 100))
    df_dados['Perc_Cadastros'] = df_dados['Perc_Cadastros'].astype(int)

    return df_dados

# Ler os arquivos CSV e o dado em memória
df = carregar_arquivos()



# Exibir o logo e os filtros no topo do aplicativo
with st.sidebar:
    st.subheader('Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome')
    logo_teste = Image.open('logo.png')  # Certifique-se de que 'logo.png' esteja no mesmo diretório
    st.image(logo_teste, use_column_width=True)
    st.subheader('Seleção de Filtros')
    fAno = st.selectbox(
        "Selecione o Ano:",
        options=df['Ano'].unique()
    )


dados_ano = df.loc[
    (df['Ano'] == fAno) & (df['Mes'] == 12 )
]

# ****************  Top 20 cidades *****************

# Top 20 cidades
# Filtrando o DataFrame para incluir apenas as linhas onde o valor da coluna "Mes" seja igual a 12
dados_filtrados = df.loc[df['Mes'] == 12]

df_aggregated = dados_filtrados.groupby(['Ano', 'codigo_IBGE', 'nome_municipio', 'sigla_UF']).agg({
        'Qtd_Cadastros': 'sum'
    }).reset_index()
# Agrupa os dados por código IBGE, calculando a soma dos valores absolutos e renomeia a coluna resultante
grouped = df_aggregated.groupby(['codigo_IBGE']).agg(Qtd_Cadastros_sum=('Qtd_Cadastros', 'sum'))
# Ordena o resultado pela soma absoluta em ordem decrescente
grouped_sorted = grouped.sort_values(by='Qtd_Cadastros_sum', ascending=False)

# Seleciona os NN primeiros códigos IBGE distintos
top_codes = grouped_sorted.head(20).reset_index()

# Merge dos DataFrames
df_top_cidades = pd.merge(df_aggregated, top_codes, how='inner', left_on='codigo_IBGE', right_on='codigo_IBGE')

grafico_top20_cidades = alt.Chart(df_top_cidades).mark_line().encode(
    alt.X('Ano:N', title="Ano"),
    alt.Y('Qtd_Cadastros:Q', scale=alt.Scale(type='log'), title="Quantidades de Cadastros"),
    alt.Color('nome_municipio:N')
).properties(
        title='Top 20 cidades em quantidades de Cadastros',
        width=600,
        height=400
    )
# FIM   Top 20 cidades *****************


#  Distribuicao entre os estados

df_distribuicao_uf = dados_ano.query("Mes == 12")
# Agregar os dados por município e somar a quantidade de cadastrados em todos os programas sociais
df_distribuicao_uf = df_distribuicao_uf.groupby(['sigla_UF']).agg({
    'Qtd_Programa_Bolsa_Familia': 'sum',
    'Qtd_Baixa_Renda': 'sum',
    'Qtd_RFPC_Ate_Metade_SM': 'sum',
    'Qtd_RFPC_Acima_Metade_SM': 'sum'
}).reset_index()


# Melt do DataFrame para tornar os dados longos
df_distribuicao_uf = df_distribuicao_uf.melt(id_vars='sigla_UF', var_name='Programa', value_name='Quantidade')

# Gráfico de barras empilhadas
grafico_df_distribuicao_uf = alt.Chart(df_distribuicao_uf).mark_bar().encode(
    x=alt.X('sigla_UF:N', title='Estado'),
    y=alt.Y('Quantidade:Q', title='Quantidade de Cadastrados', scale=alt.Scale(domain=[0, 26000000])),
    color='Programa:N',
    tooltip=['sigla_UF', 'Programa', 'Quantidade']
).properties(
    title='Quantidade de Cadastrados por Programa Social e Estado - '+fAno,
    width=600,
    height=400)

#  FIM Distribuicao entre os estados

# Evolução pelo Período

meses = {
    ano * 100 + mes: str(ano * 100 + mes) if mes == 1 else ''
    for ano in range(2013, 2024)
    for mes in range(1, 13)
}

# select a point for which to provide details-on-demand
label = alt.selection_single(
    encodings=['x'], # limit selection to x-axis value
    on='mouseover',  # select on mouseover events
    nearest=True,    # select data point nearest the cursor
    empty='none'     # empty selection includes no data points
)
# Agregar os dados por município e somar a quantidade de cadastrados em todos os programas sociais
df_evolucao = df.groupby(['AnoMes']).agg({
    'Qtd_Programa_Bolsa_Familia': 'sum',
    'Qtd_Baixa_Renda': 'sum',
    'Qtd_RFPC_Ate_Metade_SM': 'sum',
    'Qtd_RFPC_Acima_Metade_SM': 'sum'
}).reset_index()

# Realizar o "melt" nos dados para torná-los longos
df_evolucao = df_evolucao.melt(id_vars='AnoMes', var_name='Programa', value_name='Cadastros')

# Converter o número do mês para o nome do mês
df_evolucao['Nome_Mes'] = df_evolucao['AnoMes'].map(meses)


# Gráfico de barras empilhadas
grafico_evolucao = alt.Chart(df_evolucao).mark_line().encode(
    x=alt.X('AnoMes:N', title='AnoMes', axis=alt.Axis(labelOverlap=True), sort=list(meses.values())),
    y=alt.Y('Cadastros:Q', title='Cadastros', scale=alt.Scale(type='log')),
    color='Programa:N',
    tooltip=[ 'Programa', 'Cadastros']
).properties(
    title='volução dos Cadastros dos Programas Sociais ao longo do período',
    width=600,
    height=400
)

alt.layer(
    grafico_evolucao,

    # add a rule mark to serve as a guide line
    alt.Chart().mark_rule(color='#aaa').encode(
        x='AnoMes:N'
    ).transform_filter(label),

    # add circle marks for selected time points, hide unselected points
    grafico_evolucao.mark_circle().encode(
        opacity=alt.condition(label, alt.value(1), alt.value(0))
    ).add_selection(label),

    # add text labels for stock prices
    grafico_evolucao.mark_text(align='left', dx=5, dy=-5).encode(text='Cadastros:Q' ).transform_filter(label),

    data=df_evolucao
).properties(
    title='Evolução dos Cadastros dos Programas Sociais ao longo do período',
    width=600,
    height=400
)

# Fim da Evolução pelo Período



# Mapa por municipios

df_mapa = dados_ano.query("Mes == 12")
# Agregar os dados por 'codigo_IBGE' e 'populacao' e calcular a média de 'Perc_Cadastros' arredondada
df_mapa = df_mapa.groupby(['codigo_IBGE', 'populacao']).agg({
    'Perc_Cadastros': lambda x: min(round(x.mean(), 1), 100),
}).reset_index()

@st.cache_data()
def load_geometry():
    return (
        alt.Data(
            url="https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json",
            format=alt.DataFormat(property='features')
        )
    )

geometry = load_geometry()

altair_map = alt.Chart(geometry).mark_geoshape(
    stroke='white',
    strokeWidth=0.1
).encode(
    color=alt.Color('Perc_Cadastros:Q', title='Percentual',
                    scale=alt.Scale(type='linear', scheme='blueorange')),
     tooltip=[
         alt.Tooltip('properties.name:N', title='Município '),
         alt.Tooltip('Perc_Cadastros:Q', title='Média %'),
         alt.Tooltip('populacao:Q', title='Populacao'),
     ]
).transform_lookup(
    lookup='properties.id',
    from_=alt.LookupData(df_mapa, 'codigo_IBGE', ['Perc_Cadastros','populacao'])
).properties(
    title='Média do Percentual Anual para Quantidade de Cadastros versus População',
    width=700,
    height=500
)


# Fim do Mapa por Municipios


# Exibir os dados filtrados
st.header('Pessoas por faixa de renda no Cadastro Único - MI Social')
st.markdown('**Ano Selecionado:** '+ fAno)



A, B, C, D = st.tabs(["Top 20 Cidades", "Cadastros dos Programas Sociais", "Evolução ao Longo do Período","Mapa de Aproprição por Municípios"])
with A:
    st.session_state["selected_tab"] = "Top 20 Cidades"
    st.altair_chart(grafico_top20_cidades)
with B:
    st.session_state["selected_tab"] = "Cadastros dos Programas Sociais"
    st.altair_chart(grafico_df_distribuicao_uf)
with C:
    st.session_state["selected_tab"] = "Evolução ao Longo do Período"
    st.altair_chart(grafico_evolucao)
with D:
    st.session_state["selected_tab"] = "Mapa de Aproprição por Municípios"
    st.altair_chart(altair_map)




