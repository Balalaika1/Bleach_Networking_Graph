import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import pandas as pd
import plotly.graph_objects as go
import numpy as np

from PIL import Image
import base64
from io import BytesIO
import os
import ast
import math
from functools import lru_cache

# Загрузка данных
df = pd.read_excel('characters_main.xlsx')
df['found_names'] = df['found_names'].apply(ast.literal_eval)
df['num_arc'] = df['arc_order'].astype(str)+ " " + df['arc'].astype(str)

df_info = df.drop_duplicates(subset='base_name', keep='first')

df_images = pd.read_excel('images.xlsx')

# Создание списка имен для фильтрации
with st.sidebar:

    st.sidebar.image("lable_bleach.png", use_column_width=True)

    name_options = df['base_name'].unique()
    selected_name = st.multiselect("Выберите персонажа", name_options, default = 'Ichigo Kurosaki')

    arc_options = df['num_arc'].unique()
    selected_arc = st.multiselect("Выберите Арку", arc_options,key='1 agent of the shinigami arc')
    if not selected_arc:
        selected_arc = arc_options
    
    graph_range = st.slider("Select a step for the graph", 1, 100, 1)

# Фильтрация данных по выбранному имени
if selected_name:
    filtered_df = df[(df['base_name'].isin(selected_name))&df['num_arc'].isin(selected_arc)]
else:
    filtered_df = df  # Если персонаж не выбран, показываем всех

# Функция графика
def binned_data(df, id_to_highlight, range_one, name_column):
    df_bined = df.copy()
    min_value = int(np.floor(df[name_column].min()))
    max_value = int(np.ceil(df[name_column].max()))

    bins = range(min_value, max_value + range_one, range_one)

    # Определяем значение высоты для id_to_highlight
    height_value = df_bined.loc[df_bined['pageid'] == id_to_highlight, name_column].values[0]
    highlight_bin = pd.cut([height_value], bins=bins, right=False)[0]

    # Используем pd.cut для всех случаев, чтобы логика была единообразной
    df_bined['Binned'] = pd.cut(df_bined[name_column], bins=bins, right=False)

    binned_df = df_bined['Binned'].value_counts().reset_index()
    binned_df.columns = ['Binned', 'Count']
    binned_df = binned_df.sort_values(by='Binned')

    colors = ['lightslategray'] * len(binned_df)

    # Обновляем цвет бина, который нужно выделить
    for i, binned_value in enumerate(binned_df['Binned']):
        if binned_value == highlight_bin:
            colors[i] = 'red'  # Выделяем красным цветом

    fig = go.Figure(data=[go.Bar(x=binned_df['Binned'].astype(str), y=binned_df['Count'], marker_color=colors)])

    # Показываем график
    return fig


def binned_data_episodes(df, id_to_highlight, range_one, name_column):

    df_bined = df.copy()
    min_value = int(np.floor(df[name_column].min()))
    max_value = int(np.ceil(df[name_column].max()))

    bins = range(min_value, max_value + range_one, range_one)

    # Определяем значение высоты для id_to_highlight
    height_value = df_bined.loc[df_bined['pageid'] == id_to_highlight, name_column].values[0]
    highlight_bin = pd.cut([height_value], bins=bins, right=False)[0]

    # Используем pd.cut для всех значений, чтобы логика была единообразной
    df_bined['Binned'] = pd.cut(df_bined[name_column], bins=bins, right=False)

    binned_df = df_bined['Binned'].value_counts().reset_index()
    binned_df.columns = ['Binned', 'Count']
    binned_df = binned_df.sort_values(by='Binned')

    colors = ['lightslategray'] * len(binned_df)

    # Обновляем цвет бина, который нужно выделить
    for i, binned_value in enumerate(binned_df['Binned']):
        if binned_value == highlight_bin:
            colors[i] = 'red'  # Выделяем красным цветом

    # Сопоставляем бины с названиями арок
    arc_labels = {
    "Agent of the Shinigami Arc": {
        "episodes": list(range(1, 21)),  # Серии с 1 по 20
        "description": "Начальная арка, где Ичиго становится заместителем шинигами."
    },
    "Soul Society Arc": {
        "episodes": list(range(21, 64)),  # Серии с 21 по 63
        "description": "Арка, в которой Ичиго и его друзья отправляются в Общество душ, чтобы спасти Рукию."
    },
    "Bount Arc": {
        "episodes": list(range(64, 109)),  # Серии с 64 по 109
        "description": "Филлерная арка про Баунтов — существа, питающиеся душами."
    },
    "Arrancar Arc": {
        "episodes": list(range(110, 168)),  # Серии с 110 по 167
        "description": "Ичиго сталкивается с арранкарами и начинает тренироваться для встречи с Айдзеном."
    },
    "The New Captain Shusuke Amagai Arc": {
        "episodes": list(range(168, 190)),  # Серии с 168 по 189 (филлерная арка)
        "description": "Филлерная арка о новом капитане Шусуке Амагае."
    },
    "Hueco Mundo Arc": {
        "episodes": list(range(190, 206)),  # Серии с 190 по 205
        "description": "Ичиго и его союзники проникают в Уэко Мундо, чтобы спасти Орихиме."
    },
    "Karakura-Raizer Mini-Arc": {
        "episodes": [206, 207],  # Серии 206 и 207
        "description": "Мини-арка про супергероев Каракура Райзер."
    },
    "Turn Back the Pendulum Arc": {
        "episodes": list(range(208, 213)),  # Серии с 208 по 212
        "description": "Предыстория Визардов и инцидента с Айдзеном."
    },
    "Fake Karakura Town Arc": {
        "episodes": list(range(213, 227)),  # Серии с 213 по 226
        "description": "Айдзен и его арранкары сражаются с Готэй 13 в поддельном городе Каракура."
    },
    "Zanpakuto Unknown Tales Arc": {
        "episodes": list(range(227, 266)),  # Серии с 227 по 265
        "description": "Филлерная арка о мятеже занпакто."
    },
    "Beast Swords Arc": {
        "episodes": list(range(266, 317)),  # Серии с 266 по 316
        "description": "Подарка про пробужденные занпакто и продолжение мятежа занпакто."
    },
    "Gotei 13 Invading Army Arc": {
        "episodes": list(range(317, 343)),  # Серии с 317 по 342
        "description": "Филлерная арка о клонировании Готэй 13 и вторжении в Общество душ."
    },
    "The Lost Substitute Shinigami Arc": {
        "episodes": list(range(343, 367)),  # Серии с 343 по 366
        "description": "Возвращение Ичиго как заместителя шинигами и противостояние с новыми врагами."
    },
    "The Thousand-Year Blood War Arc": {
        "episodes": list(range(368, 500)),  # Эта арка пока не полностью адаптирована, она идет в новой серии.
        "description": "Арка войны с Квинси."
    },
    "Echoing Jaws of Hell Arc": {
        "episodes": [],  # Это недавняя арка, на данный момент она в манге.
        "description": "Арка, которая следует за войной с Квинси и касается Врат ада."
    },
    "New Breathes From Hell Arc": {
        "episodes": [],  # Появляется в манге как часть специальной главы.
        "description": "Арка о мире Ада."
    }
    }

    # Формируем подписи оси X, добавляя названия арок
    x_labels = []
    for binned_value in binned_df['Binned']:
        label = str(binned_value)
        for arc, info in arc_labels.items():
            if any(ep >= binned_value.left and ep < binned_value.right for ep in info['episodes']):
                label = f"{binned_value} ({arc})"
                break
        x_labels.append(label)

    fig = go.Figure(data=[go.Bar(x=x_labels, y=binned_df['Count'], marker_color=colors)])

    # Показываем график
    return fig


def binned_data_zodiac_horizontal(df, id_to_highlight, name_column):

    df_bined = df.copy()

    # Проверяем, есть ли нужное значение для выделения
    highlight_signs = df_bined.loc[df_bined['base_name'] == id_to_highlight, name_column]
    
    # Проверяем, пустой ли результат
    if highlight_signs.empty:
        highlight_sign = None  # Устанавливаем значение по умолчанию, если ничего не найдено
    else:
        highlight_sign = highlight_signs.values[0]

    # Подсчет количества каждого знака зодиака
    binned_df = df_bined[name_column].value_counts().reset_index()
    binned_df.columns = [name_column, 'Count']
    binned_df = binned_df.sort_values(by='Count')

    # Определяем цвета для гистограммы, выделяем выбранный знак зодиака
    colors = ['lightslategray'] * len(binned_df)
    for i, zodiac in enumerate(binned_df[name_column]):
        if zodiac == highlight_sign:
            colors[i] = 'red'  # Выделяем красным цветом

    print(highlight_signs)
    print(colors)

    # Создание горизонтальной гистограммы
    fig = go.Figure(data=[go.Bar(
        y=binned_df[name_column], 
        x=binned_df['Count'], 
        orientation='h', 
        marker_color=colors,
        text=binned_df['Count'],
        textfont=dict(color='white'),  # Добавляем значения как метки данных
        textposition='inside'
    )])

    # Настройка макета
    fig.update_layout(
        # title='Распределение персонажей по знакам зодиака с выделением',
        # xaxis_title='Количество',
        # yaxis_title='Знак зодиака',
        # margin=dict(t=0, l=200, r=0, b=0),
        # width=600,
        # height=800,
        yaxis=dict(automargin=True, tickfont=dict(size=10)),
        xaxis=dict(tickfont=dict(size=12))
        
    )

    # Возвращаем фигуру для отображения
    return fig

def binned_data_gender_horizontal(df, id_to_highlight, name_column):
    df_bined = df.copy()

    # Группируем данные по полу и считаем количество записей
    binned_df = df_bined[name_column].value_counts().reset_index()
    binned_df.columns = [name_column, 'Count']

    # Сортировка по убыванию количества
    binned_df = binned_df.sort_values(by='Count')

    # Получаем значение 'Gender' для выделения
    highlight_genders = df_bined.loc[df_bined['base_name'] == id_to_highlight, name_column]

    # Проверяем, пустой ли результат
    if highlight_genders.empty:
        highlight_gender = None  # Устанавливаем значение по умолчанию, если ничего не найдено
    else:
        highlight_gender = highlight_genders.values[0]

    # Определяем цвета для круговой диаграммы, выделяем выбранный пол
    colors = ['lightslategray'] * len(binned_df)
    for i, gender in enumerate(binned_df[name_column]):
        if gender == highlight_gender:
            colors[i] = 'red'  # Выделяем красным цветом

    # Создание круговой диаграммы
    fig = go.Figure(data=[go.Pie(
        labels=binned_df[name_column], 
        values=binned_df['Count'], 
        marker=dict(colors=colors),
        textinfo='label+percent', 
        insidetextorientation='radial'
    )])

    # Возвращаем фигуру для отображения
    return fig


# Функция для вычисления суммы значений в found_names
def calculate_total(found_names):
    total = sum(found_names.values())
    return math.log1p(total) * 5

# Функция для преобразования изображения в base64
@lru_cache(maxsize=None)
def image_change(image_path):
    try:
        img = Image.open(image_path).convert("RGBA")  # Convert to RGBA
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        img_url = f"data:image/png;base64,{img_str}"
        return img_url
    except Exception as e:
        st.error(f"Ошибка при загрузке изображения: {e}")
        return None

# Функция для поиска изображения
def img_find(pageid):
    image_path = os.path.join('downloaded_images', f'{pageid}.png')
    if os.path.exists(image_path):
        return image_change(image_path)
    else:
        return None

# Создание уникального набора узлов и списка ребер
node_ids = set()
nodes = []
edges = []

for _, row in filtered_df.iterrows():
    # Используйте pageid для нахождения изображения
    pageid = row.get('pageid')
    image_url = img_find(pageid)

    # Добавляем узел для base_name, если его еще нет в наборе
    if row['base_name'] not in node_ids:
        nodes.append(Node(id=row['base_name'], label=row['base_name'], size=15, color='blue', shape="circularImage", image=image_url))
        node_ids.add(row['base_name'])

    # Добавляем узел для arc с другим цветом, если его еще нет в наборе
    if row['arc'] not in node_ids:
        nodes.append(Node(id=row['arc'], label=row['arc'], size=10, color='green'))
        node_ids.add(row['arc'])

    # Добавляем ребро между name и arc
    edges.append(Edge(source=row['base_name'], target=row['arc'], width=2))

    # Добавляем узлы и ребра для found_names, если их еще нет в наборе
    for name, value in row['found_names'].items():
        if name not in node_ids:
            size = calculate_total(row['found_names'])
            # Поиск изображения для found_names на основе pageid
            found_name_pageid = df_images.loc[df_images['base_name'] == name, 'pageid'].values[0]
            image_url = img_find(found_name_pageid)
            mention_count = value
            label = f"{name} ({mention_count})"
            nodes.append(Node(id=name, label=name, size=size, color='red', shape="circularImage", image=image_url))
            node_ids.add(name)
        edges.append(Edge(source=row['arc'], target=name))

# Конфигурация графа
config = Config(
    # directed=False,
    # nodeHighlightBehavior=True,
    # highlightColor="#F7A7A6",
    # collapsible=True,
    # node={'labelProperty': 'label'},
    # link={'labelProperty': 'label', 'renderLabel': True},
    # d3={'gravity': -250}  # Увеличиваем силу отталкивания
)

id_to_highlight = df_info[df_info['base_name'].isin(selected_name)]['pageid'].values[0]
num_height = df_info[df_info['base_name'].isin(selected_name)]['Height'].values[0]
num_weight = df_info[df_info['base_name'].isin(selected_name)]['Weight'].values[0]
num_episodes = df_info[df_info['base_name'].isin(selected_name)]['First Appearance - Anime'].values[0]
gender_data = df_info[df_info['base_name'].isin(selected_name)]['Gender'].values[0]
birthday_day = df_info[df_info['base_name'].isin(selected_name)]['Birthday'].values[0]
race_group = df_info[df_info['base_name'].isin(selected_name)]['Race'].values[0]
id_to_highlight2 = df[df['base_name'].isin(selected_name)]['base_name'].values[0] # Номер для Знака зодиака

# Использование одного столбца и ограничение ширины
col1 = st.columns(1)  # Центрируем, используя три колонки, где средняя шире

agraph(nodes=nodes, edges=edges, config=config)

tab1, tab2, tab3,tab4,tab5,tab6 = st.tabs(["Пол", "Вес", "Рост",'Появление в аниме','Знак зодиака','Группа персонажа'])
with tab1:
    st.write("**Пол**")
    st.write(f"Пол персонажа: {gender_data if gender_data else 'Все персонажи'}")
    st.plotly_chart(binned_data_gender_horizontal(df_info, id_to_highlight2,'Gender'))
with tab2:
    st.write("**Вес**")
    st.write(f"Вес персонажа: {num_weight if num_weight else 'Все персонажи'} кг")
    # weight_range = st.slider("Select a step for the graph", 1, 100, 1)
    st.plotly_chart(binned_data(df_info, id_to_highlight,graph_range,'Weight'))
with tab3:
    st.write("**Рост**")
    st.write(f"Рост персонажа: {num_height if num_height else 'Все персонажи'} см")
    # height_range = st.slider("Select a step for the graph", 1, 100, 1, key = 'height_range')
    st.plotly_chart(binned_data(df_info, id_to_highlight,graph_range,'Height'))
with tab4:
    st.write("**Появление в аниме**")
    st.write(f"Впервые появился в : {int(num_episodes) if int(num_episodes) else 'Все персонажи'} эп")
    # height_range = st.slider("Select a step for the graph", 1, 100, 1, key = 'height_range')
    st.plotly_chart(binned_data_episodes(df_info, id_to_highlight,graph_range,'First Appearance - Anime'))
with tab5:
    st.write("**Знак зодиака**")
    st.write(f"Родился: {birthday_day if birthday_day else 'Все персонажи'}")
    # weight_range = st.slider("Select a step for the graph", 1, 100, 1)
    st.plotly_chart(binned_data_zodiac_horizontal(df_info, id_to_highlight2, 'Zodiac Sign'))
with tab6:
    st.write("**Группа персонажа**")
    st.write(f"Группа персонажа: {race_group if race_group else 'Все персонажи'}")
    # weight_range = st.slider("Select a step for the graph", 1, 100, 1)
    st.plotly_chart(binned_data_zodiac_horizontal(df_info, id_to_highlight2, 'Race'))

st.dataframe(df_info.drop(columns=['Unnamed: 0']))