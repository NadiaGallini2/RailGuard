#pip install os-sys
import os
import csv
import re
import streamlit as st
from pycaret.classification import setup, compare_models, pull, save_model
import numpy as np
import pandas as pd
import pandas_profiling
from streamlit_pandas_profiling import st_profile_report
import io
## Начало области настройки подключения стилей
from streamlit.web import cli as stcli

st.set_page_config(layout="wide", page_title="ML", page_icon="🧊")

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
css_file = 'style.css'
load_css(css_file)
## Конец области настройки подключения стилей

with st.sidebar:
    st.title("ML")
    choice = st.radio("Навигация", ["Загрузка", "Анализ", "Машинное обучения", "Скачать"])
    st.info("Это проектное приложение для машинного обучения")


if os.path.exists('./dataset.csv'):
    df = pd.read_csv('dataset.csv', index_col=None)

if choice == "Загрузка":
    st.title("Загрузка данных")
    file = st.file_uploader("Загрузите свой набор данных", type=["csv", "xlsx"])
    if file is not None:
        try:
            # Определяем тип файла и загружаем данные соответствующим образом
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, sep=',', index_col=None)
            elif file.name.endswith('.xlsx'):
                df = pd.read_excel(file, index_col=None)
            df.to_csv('dataset.csv', index=None)  # Сохраняем в CSV для дальнейшего использования
            st.dataframe(df)
        except pd.errors.EmptyDataError:
            st.error("Файл пустой")
        except Exception as e:
            st.error(f"Произошла ошибка: {e}")
            
import pandas_profiling
#pip install pandas_profiling
from streamlit_pandas_profiling import st_profile_report
# pip install https://github.com/pandas-profiling/pandas-profiling/archive/master.zip
if choice == "Анализ":
    st.title("Автоматизированный исследовательский анализ данных")
    profile_df = df.profile_report()
    st_profile_report(profile_df)
    
if choice == "Машинное обучения":
    chosen_targets = st.multiselect('Выберите целевые столбцы', df.columns)
    if st.button('Запустить обучение'): 
        for target in chosen_targets:
            st.subheader(f"Модель для целевого столбца: {target}")
            df_target = df.dropna(subset=[target])
            setup(df_target, target=target, verbose=False)
            setup_df = pull()
            st.info("Это настройка эксперимента ML")
            st.dataframe(setup_df.dropna())
            best_model = compare_models()
            compare_df = pull()
            st.info("Это модель ML")
            st.dataframe(compare_df.dropna())
            best_model
            save_model(best_model, f'best_model_{target}')
    
file_path = 'best_model.pkl'

if choice == "Скачать":
    st.title("Ваша обученная модель скачалась в папку проекта")
    with open(file_path, 'rb') as file:
        st.download_button('Скачать модель', file, file_name="best_model.pkl")