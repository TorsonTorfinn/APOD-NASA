import requests
import streamlit as st
from datetime import date
import json
from translate import Translator 
import re 
import os

# Чтение переводов из JSON-файла
with open('translations.json', 'r', encoding='utf-8') as file:
    translations = json.load(file)

# API ключ из secrets.toml
API_KEY = st.secrets["general"]["api_key"]

base_url = f"https://api.nasa.gov/planetary/apod"

# Функция для разбиения текста по предложениям (по точкам)
def split_by_sentences(text):
    return re.split(r'(?<=[.!?]) +', text)  # Разбиваем текст по точкам, восклицательным или вопросительным знакам

# Выбор языка в боковой панели
selected_language = st.sidebar.selectbox("🌎 Select Language | Выберите язык", ['en', 'ru'], index=0)
t = translations[selected_language]  # Получение перевода на выбранном языке

# Заголовок приложения
st.sidebar.header(t['select_language'])
st.title(t['header'])

# Выбор режима запроса
query_mode = st.sidebar.radio(t['select_mode'], [t['single_image'], t['date_range'], t['random_images']])

# Обработка режимов на основе выбранного языка
if query_mode == t['single_image']:
    selected_date = st.sidebar.date_input(t['select_date'], date.today())
    adop_url = f"{base_url}?api_key={API_KEY}&date={selected_date}"

elif query_mode == t['date_range']:
    start_date = st.sidebar.date_input(t['start_date'], date.today().replace(day=1))
    end_date = st.sidebar.date_input(t['end_date'], date.today())
    if start_date > end_date:
        st.sidebar.error(t['image_warning'])
    adop_url = f"{base_url}?api_key={API_KEY}&start_date={start_date}&end_date={end_date}"

elif query_mode == t['random_images']:
    count = st.sidebar.slider(t['number_of_images'], min_value=1, max_value=10, value=1)
    adop_url = f"{base_url}?api_key={API_KEY}&count={count}"

# Выполнение запроса к API
st.sidebar.markdown(f"[Запрос к NASA]({adop_url})")
r1 = requests.get(adop_url)

if r1.status_code != 200:
    st.error(t['api_error'])
else:
    data = r1.json()

    # Определяем язык, на который нужно переводить
    target_language = 'ru' if selected_language == 'ru' else 'en'
    translator = Translator(to_lang=target_language)  # Устанавливаем целевой язык для перевода

    # Обработка и отображение данных в зависимости от режима
    if isinstance(data, dict):
        img_title = data.get('title', t['header'])
        img_explanation = data.get('explanation', t['explanation'])
        img_url = data.get('url', '')
        media_type = data.get('media_type', 'image')
        author = data.get('copyright', t['author'])

        # Перевод заголовка и пояснения, если выбран русский язык
        if target_language == 'ru':
            img_title = translator.translate(img_title)

            # Разбиение объяснения на предложения и перевод каждого предложения
            explanation_sentences = split_by_sentences(img_explanation)
            img_explanation_translated = ' '.join([translator.translate(sentence) for sentence in explanation_sentences])
        else:
            img_explanation_translated = img_explanation

        st.subheader(img_title)
        if author:
            st.write(f"{t['author']}: {author}")
        if media_type == "video":
            st.video(img_url)
        else:
            image_path = 'image.png'
            r2 = requests.get(img_url)
            with open(image_path, 'wb') as image_file:
                image_file.write(r2.content)
            st.image(image_path)
        st.info(f"{t['explanation']}: {img_explanation_translated}")
    else:
        # Обработка списка изображений для диапазона дат или случайного выбора
        for item in data:
            img_title = item.get('title', t['header'])
            img_explanation = item.get('explanation', t['explanation'])
            img_url = item.get('url', '')
            media_type = item.get('media_type', 'image')
            author = item.get('copyright', t['author'])

            # Перевод заголовка и пояснения
            if target_language == 'ru':
                img_title = translator.translate(img_title)
                
                # Разбиение объяснения на предложения и перевод каждого предложения
                explanation_sentences = split_by_sentences(img_explanation)
                img_explanation_translated = ' '.join([translator.translate(sentence) for sentence in explanation_sentences])
            else:
                img_explanation_translated = img_explanation

            st.header(img_title)
            if author:
                st.write(f"{t['author']}: {author}")
            if media_type == "video":
                st.video(img_url)
            else:
                r2 = requests.get(img_url)
                # Получаем абсолютный путь к папке проекта
                project_dir = os.path.dirname(os.path.abspath(__file__))
                image_dir = os.path.join(project_dir, 'images')

                # Создаем папку images, если она не существует
                if not os.path.exists(image_dir):
                    os.makedirs(image_dir)

                image_path = os.path.join(image_dir, f"image_{img_title}.png")

                with open(image_path, 'wb') as image_file:
                    image_file.write(r2.content)

                st.image(image_path)
            st.info(f"{t['explanation']}: {img_explanation_translated}")
