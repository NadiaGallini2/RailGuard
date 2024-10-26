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
    st.info("🤖 Проект для анализа оттока")

# Приветствие пользователя
st.markdown("<h1 style='color: #d51d29;'>Добро пожаловать в RailGuard! 🚆</h1>", unsafe_allow_html=True)
st.markdown("👋 Мы рады вас видеть! Здесь вы можете загружать данные и запускать модели машинного обучения.")

# Проверка наличия загруженного набора данных
if os.path.exists('./dataset.csv'):
    df = pd.read_csv('dataset.csv', index_col=None)

if choice == "Загрузка":
    st.title("📥 Загрузка данных")
    files = st.file_uploader("Загрузите набор данных (можно загрузить несколько файлов)", type=["csv", "xlsx", "xls"], accept_multiple_files=True)

    # Функция для чтения файлов
    def read_file(uploaded_file):
        try:
            if uploaded_file.name.endswith('.csv'):
                return pd.read_csv(uploaded_file, sep=',', index_col=None)
            else:
                return pd.read_excel(uploaded_file, index_col=None)
        except pd.errors.EmptyDataError:
            st.error("🚨 Файл пустой")
        except Exception as e:
            st.error(f"🚨 Произошла ошибка при загрузке {uploaded_file.name}: {e}")
        return None

    # Список для хранения загруженных датафреймов
    dataframes = []

    # Загрузка всех файлов
    if files:
        for file in files:
            df = read_file(file)
            if df is not None:
                dataframes.append(df)
                st.success(f"Файл {file.name} успешно загружен!")

        # Объединение всех загруженных датафреймов по столбцу 'ID'
        if dataframes:
            try:
                # Проверяем наличие столбца 'ID' в каждом датафрейме
                if all('ID' in df.columns for df in dataframes):
                    combined_df = dataframes[0]
                    for additional_df in dataframes[1:]:
                        combined_df = pd.merge(combined_df, additional_df, how='left', on='ID')
                    
                    # Сохраняем объединённый датафрейм в новый файл
                    combined_file_name = 'combined_dataset.csv'
                    combined_df.to_csv(combined_file_name, index=None)
                    
                    st.success("Все данные успешно объединены по 'ID' и сохранены в файл: combined_dataset.csv")

                    # Кнопка для скачивания файла
                    st.download_button(
                        label="Скачать объединённый файл",
                        data=combined_df.to_csv(index=False).encode('utf-8'),
                        file_name='combined_dataset.csv',
                        mime='text/csv'
                    )

                    # Сохраняем объединенный датафрейм в локальное состояние
                    st.session_state.combined_df = combined_df
                else:
                    st.error("🚨 Один или несколько загруженных файлов не содержат столбца 'ID'.")

            except Exception as e:
                st.error(f"🚨 Ошибка при объединении данных: {e}")
                
# Анализ данных и отбор признаков
if choice == "Анализ":
    st.title("🔍 Анализ данных и отбор признаков")
    if 'combined_df' in st.session_state:
        df = st.session_state.combined_df  # Получаем объединенный датафрейм из состояния
        st.markdown("### Важность признаков для оттока")
        st.write("Анализируется влияние каждого признака на целевую переменную для лучшего понимания.")
        profile = ProfileReport(df, minimal=True)
        st.components.v1.html(profile.to_html(), height=1000, scrolling=True)
    else:
        st.warning("⚠️ Сначала загрузите данные.")

if choice == "Машинное обучение":
    st.title("🤖 Обучение модели машинного обучения")
    
    # Убедитесь, что объединенный датафрейм доступен
    if 'combined_df' in st.session_state:
        df = st.session_state.combined_df
    else:
        st.error("🚨 Объединенный файл не загружен. Пожалуйста, загрузите данные.")
        st.stop()
    
    # Выбор временного интервала для прогноза
    prediction_interval = st.selectbox("Выберите временной интервал для прогноза", ["1 месяц", "3 месяца", "6 месяцев", "1 год"])
    
    # Выбор целевых столбцов
    chosen_targets = st.multiselect('🎯 Выберите целевые столбцы', df.columns)

    # Кнопка для запуска обучения
    if st.button('🚀 Запустить обучение'):
        for target in chosen_targets:
            st.subheader(f"🔍 Модель для целевого столбца: {target}")
            
            # Удаление строк с пропущенными значениями в целевом столбце
            df_target = df.dropna(subset=[target])
            
            # Определяем целевые переменные и фичи
            X = df_target.drop(columns=[target, 'ID', 'ОКПО', 'причина_оттока'])  # Убедитесь, что эти столбцы есть в вашем объединенном файле
            y = df_target[target]
            
            # Настройка модели
            setup(X, target=y, verbose=False)
            setup_df = pull()
            st.info("🛠️ Параметры эксперимента ML")
            st.dataframe(setup_df.dropna())
            
            # Обучение модели
            best_model = compare_models()
            compare_df = pull()
            st.info("🏆 Лучшая модель")
            st.dataframe(compare_df.dropna())

            # Сохранение модели
            save_model(best_model, f'best_model_{target}')
            st.success(f"Модель для {target} успешно сохранена!")

            # Прогнозирование вероятности оттока
            predictions = best_model.predict_proba(X)[:, 1]  # Получаем вероятности оттока
            df_target['Вероятность оттока'] = predictions
            
            # Вывод результатов
            results = df_target[['ID', 'ОКПО', 'причина_оттока', 'Вероятность оттока']]
            st.subheader("Результаты прогноза оттока")
            st.dataframe(results)

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
