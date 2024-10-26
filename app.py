import os
import csv
import re
import streamlit as st
from pycaret.classification import setup, compare_models, pull, save_model
import numpy as np
import pandas as pd
from pandas_profiling import ProfileReport
import io
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# Конфигурация страницы Streamlit
st.set_page_config(layout="wide", page_title="RailGuard", page_icon="🚂")

# Загрузка CSS для кастомного стиля
def load_css(file_path):
    """Загружает CSS для настройки внешнего вида приложения."""
    with open(file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

css_file = 'style.css'
load_css(css_file)

# Боковая панель навигации
with st.sidebar:
    st.title("🚂 RailGuard")
    choice = st.radio("Навигация", ["Загрузка", "Анализ", "Машинное обучение", "Прогнозы", "Экспорт"])
    st.info("🤖 Проект для анализа оттока организаций")

# Приветствие пользователя
st.markdown("<h1 style='color: #d51d29;'>Добро пожаловать в RailGuard! 🚆</h1>", unsafe_allow_html=True)
st.markdown("👋 Мы рады вас видеть! Здесь вы можете загружать данные и запускать модели машинного обучения.")

# Проверка наличия загруженного набора данных
if os.path.exists('./dataset.csv'):
    df = pd.read_csv('dataset.csv', index_col=None)

# Загрузка данных
if choice == "Загрузка":
    st.title("📥 Загрузка данных")
    file = st.file_uploader("Загрузите основной набор данных", type=["csv", "xlsx"])
    additional_file = st.file_uploader("Загрузите дополнительные данные (необязательно)", type=["csv", "xlsx"])
    
    # Основной файл данных
    if file is not None:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, sep=',', index_col=None)
            elif file.name.endswith('.xlsx'):
                df = pd.read_excel(file, index_col=None)
            df.to_csv('dataset.csv', index=None)
            st.dataframe(df)
        except pd.errors.EmptyDataError:
            st.error("🚨 Файл пустой")
        except Exception as e:
            st.error(f"🚨 Произошла ошибка: {e}")
    
    # Загрузка дополнительных данных
    if additional_file is not None:
        try:
            if additional_file.name.endswith('.csv'):
                additional_df = pd.read_csv(additional_file, sep=',', index_col=None)
            elif additional_file.name.endswith('.xlsx'):
                additional_df = pd.read_excel(additional_file, index_col=None)
            df = pd.merge(df, additional_df, how='left', on='Region')  # Объединяем по региону
            df.to_csv('dataset.csv', index=None)
            st.success("Дополнительные данные успешно загружены и объединены!")
        except Exception as e:
            st.error(f"🚨 Ошибка при загрузке дополнительных данных: {e}")

# Анализ данных и отбор признаков
if choice == "Анализ":
    st.title("🔍 Анализ данных и отбор признаков")
    if 'df' in locals():
        st.markdown("### Важность признаков для оттока")
        st.write("Анализируется влияние каждого признака на целевую переменную для лучшего понимания.")
        profile = ProfileReport(df, minimal=True)
        st.components.v1.html(profile.to_html(), height=1000, scrolling=True)
    else:
        st.warning("⚠️ Сначала загрузите данные.")

# Раздел для обучения модели
if choice == "Машинное обучение":
    st.title("🤖 Обучение модели машинного обучения")
    prediction_interval = st.selectbox("Выберите временной интервал для прогноза", ["1 месяц", "3 месяца", "6 месяцев", "1 год"])
    chosen_targets = st.multiselect('🎯 Выберите целевые столбцы', df.columns)
    if st.button('🚀 Запустить обучение'):
        for target in chosen_targets:
            st.subheader(f"🔍 Модель для целевого столбца: {target}")
            df_target = df.dropna(subset=[target])
            setup(df_target, target=target, verbose=False)
            setup_df = pull()
            st.info("🛠️ Параметры эксперимента ML")
            st.dataframe(setup_df.dropna())
            best_model = compare_models()
            compare_df = pull()
            st.info("🏆 Лучшая модель")
            st.dataframe(compare_df.dropna())
            save_model(best_model, f'best_model_{target}')
            st.success(f"Модель для {target} успешно сохранена!")

# Прогнозирование оттока для различных регионов
if choice == "Прогнозы":
    st.title("📈 Прогнозирование оттока по регионам")
    selected_region = st.selectbox("Выберите регион для прогноза", df['Region'].unique())
    st.write(f"Отчет по оттоку для региона {selected_region} на {prediction_interval}")
    st.line_chart(df[df['Region'] == selected_region][['Date', 'Churn_Probability']])

# Экспорт данных в CSV и XML
if choice == "Экспорт":
    st.title("⬇️ Экспорт данных")
    
    # Экспорт в CSV
    csv_data = df.to_csv(index=False)
    st.download_button(label="📂 Скачать данные в формате CSV", data=csv_data, file_name="export_data.csv", mime="text/csv")
    
    # Экспорт в XML
    def to_xml(df):
        """Форматирование данных в XML для экспорта в 1С."""
        root = ET.Element("Data")
        for _, row in df.iterrows():
            entry = ET.SubElement(root, "Entry")
            for col_name, col_value in row.items():
                col_element = ET.SubElement(entry, col_name)
                col_element.text = str(col_value)
        return ET.tostring(root, encoding="utf-8")

    xml_data = to_xml(df)
    st.download_button(label="📂 Скачать данные в формате XML", data=xml_data, file_name="export_data.xml", mime="application/xml")

    st.info("Данные готовы для импорта в 1С в формате CSV и XML.")
