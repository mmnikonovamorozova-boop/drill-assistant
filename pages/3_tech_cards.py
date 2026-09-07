import streamlit as st
import json
import os
import requests
import pandas as pd
import io
from datetime import datetime

# Инициализация сессионных переменных и проверка авторизации
if "well_number" not in st.session_state:
    st.session_state["well_number"] = "Скв. № 102, Куст 12"
if "engineer_name" not in st.session_state:
    st.session_state["engineer_name"] = "Иванов И.И."
if "field_name" not in st.session_state:
    st.session_state["field_name"] = "Приобское"

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Выполните авторизацию на главной странице.")
    st.stop()

st.set_page_config(page_title="Технологические карты инцидентов", page_icon="🛠", layout="wide")
st.title("🛠 Технологические карты и Профили инцидентов (DD/MWD)")
st.caption("Автоматизированные чек-листы ликвидации брака, трибологические расчеты и верификация по СТО ИНТИ")
# --- СБОР И СИНХРОНИЗАЦИЯ МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")

well_number = st.sidebar.text_input(
    "Номер скважины / Куст:",
    value=st.session_state["well_number"],
    key="well_input"
)
st.session_state["well_number"] = well_number

engineer_name = st.sidebar.text_input(
    "ФИО Инженера по ННБ:",
    value=st.session_state["engineer_name"],
    key="eng_input"
)
st.session_state["engineer_name"] = engineer_name

field_name = st.sidebar.text_input(
    "Месторождение:",
    value=st.session_state["field_name"],
    key="field_input"
)
st.session_state["field_name"] = field_name

st.sidebar.markdown("---")
st.sidebar.info("💡 Метаданные синхронизированы с модулем Матрицы ЛНД и автоматически попадут во все генерируемые акты.")

# --- ОТКАЗОУСТОЙЧИВАЯ ФУНКЦИЯ ЗАГРУЗКИ ТЕХКАРТ ---
@st.cache_data(ttl=60)
def load_tech_cards_database():
    filename = "tech_requirements.json"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.sidebar.error(f"⚠ Ошибка чтения {filename}: {str(e)}")
            
    # Базовый набор технологических карт по Р-ТС-35 (подробнее см. в полной документации)
    fallback_data = {
        "Наземный тест осциллятора КНБК (Р-ТС-35)": {...},
        "Контроль люфта и угла ВЗД (Р-ТС-35)": {...},
        "Позиционирование резистивиметра LWD (Р-ТС-35)": {...}
    }
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(fallback_data, f, ensure_ascii=False, indent=4)
    except:
        pass
    return fallback_data

tech_data = load_tech_cards_database()
if not tech_data:
    st.error("❌ Критическая ошибка: Не удалось инициализировать базу данных техкарт.")
    st.stop()
