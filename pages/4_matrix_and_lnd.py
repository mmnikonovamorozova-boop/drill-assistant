import streamlit as st
import json
import os
import requests
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Выполните авторизацию.")
    st.stop()

st.set_page_config(page_title="Матрица ответственности ИТР", page_icon="📋", layout="wide")
st.title("📋 Матрица оперативного контроля и ответственности ИТР")
st.caption("Полевой контроль технологической дисциплины, регламентов ЛНД и верификация СМК на устье")
# --- СБОР МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 102, Куст 12")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")
st.sidebar.markdown("---")
st.sidebar.info("💡 Выберите операцию и условия по центру экрана.")

@st.cache_data(ttl=60)
def load_kb_database():
    try:
        token = st.secrets["kb_parser_integration"]["token"]
        user = st.secrets["kb_parser_integration"]["user"].strip().replace("/", "")
        
        # Перестраховываемся и собираем URL максимально жестко
        domain_parts = ["api", "github", "com"]
        base_api = f"https://{'.'.join(domain_parts)}/repos"
        repo_path = "mmnikonovamorozova-boop/drill-kb-parser/contents"
        file_path = "output_json/automated_kb.json"
        url = f"{base_api}/{repo_path}/{file_path}"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.raw"
        }
        
        response = requests.get(url, headers=headers, timeout=10)

        # ВЫВОД ОТЛАДКИ ПРЯМО НА ЭКРАН (Удалим, как только увидим код)
        if response.status_code != 200:
            st.error(f"🛑 Ошибка GitHub API. Статус-код сервера: {response.status_code}")
            st.info(f"Проверяемый URL: {url}")
            if response.status_code == 404:
                st.warning("Код 404 означает: либо репозиторий не найден, либо GitHub-токен не имеет прав на чтение этого приватного репозитория.")
        
        if response.status_code == 200:
            return json.loads(response.text)
            
    except Exception as e:
        st.error(f"❌ Системный сбой при запросе: {str(e)}")
    
    return None

kb_data = load_kb_database()
if not kb_data:
    st.warning("⚠ Файл базы знаний не найден.")
    st.stop()
st.subheader("📋 Условия проведения операции на устье")

# Собираем список верхнеуровневых ключей
global_operations = list(kb_data.keys()) if kb_data else []
selected_op = st.selectbox("🎯 Выберите технологическую операцию:", global_operations, index=0)

# БЕЗОПАСНЫЙ СБОР ЗАКАЗЧИКОВ (Защита от TypeError)
available_clients = []
items = []

if selected_op and isinstance(kb_data.get(selected_op), list):
    # Если структура новая (список объектов)
    items = kb_data[selected_op]
    available_clients = list(set(item.get("client", "Неизвестный") for item in items if isinstance(item, dict)))
else:
    # Если структура старая (словарь, где ключи - подкатегории)
    st.info("🔄 Обнаружена старая структура базы данных. Пожалуйста, загрузите любой PDF в репозиторий парсера для обновления.")
    if selected_op and isinstance(kb_data.get(selected_op), dict):
        available_clients = [selected_op] # В старой структуре это и был заказчик

col_f1, col_f2 = st.columns(2)
with col_f1:
    client_filter = st.multiselect("💼 Фильтр по Заказчикам (По умолчанию показаны все):", available_clients)
with col_f2:
    type_filter = st.radio("🔍 Фильтр требований:", ["Все пункты", "Только КРИТИЧЕСКИЕ ЗАПРЕТЫ"], horizontal=True)

st.markdown("---")

st.markdown("---")

# --- ФОРМИРОВАНИЕ СВОДНОЙ МАТРИЦЫ В ВИДЕ ТАБЛИЦЫ ---
if items and isinstance(items, list):
    table_rows = []
    
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
            
        client_name = item.get("client", "Неизвестный")
        action_text = item.get("action", "")
        resp_raw = item.get("responsibility_raw", "").lower()
        
        # Применение фильтров по заказчикам
        if client_filter and client_name not in client_filter:
            continue
            
        # Интеллектуальное выделение запретов
        is_prohib = item.get("is_prohibition", False)
        if type_filter == "Только КРИТИЧЕСКИЕ ЗАПРЕТЫ" and not is_prohib:
            continue
            
        # Автоматическое распределение зон ответственности по колонкам матрицы
        role_nnb = "Контроль параметров" if any(w in resp_raw for w in ["ннб", "телеметр", "dd", "mwd"]) else "Информирован"
        role_master = "Выполнение / Сборка" if any(w in resp_raw for w in ["мастер", "бурильщик", "подрядчик"]) else "Информирован"
        role_super = "Контроль / Согласование" if any(w in resp_raw for w in ["супервайзер", "усб", "заказчик"]) else "Информирован"
        
        # Точечное извлечение требований конкретно для инженера по ННБ из контекста
        if "ннб" in resp_raw or "телеметр" in resp_raw:
            role_nnb = "❗ КРИТИЧЕСКИЙ КОНТРОЛЬ: " + item.get("responsibility_raw", "")
            
        table_rows.append({
            "Заказчик": client_name,
            "Пункт / Раздел": f"п. {item.get('step_id', 'Б/Н')} ({item.get('original_section', '')})",
            "Технологическое требование / Инструкция": action_text if not is_prohib else f"🛑 ЗАПРЕЩЕНО: {action_text}",
            "Инженер по ННБ (Ваша зона)": role_nnb,
            "Буровой подрядчик / Вахта": role_master,
            "Супервайзер / Контроль ЛНД": role_super
        })

    if table_rows:
        df = pd.DataFrame(table_rows)
        
        st.markdown(f"### 📊 Сводная таблица взаимодействия сторон: *{selected_op}*")
        
        # Выводим красивую интерактивную таблицу на весь экран Streamlit
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Технологическое требование / Инструкция": st.column_config.TextColumn(width="large"),
                "Инженер по ННБ (Ваша зона)": st.column_config.TextColumn(width="medium"),
            }
        )
        
        # Краткий чеклист для генерации акта под таблицей
        st.markdown("### 📝 Верификация выполнения регламентов вахтой")
        verified_tasks = []
        for i, row in enumerate(table_rows[:15]): # Ограничиваем топ-15 пунктами для чеклиста рапорта
            state = st.checkbox(f"{row['Заказчик']} | {row['Пункт / Раздел']}: {row['Технологическое требование / Инструкция'][:80]}...", key=f"chk_{i}")
            if state:
                verified_tasks.append(row)
    else:
        st.warning("Нет пунктов, соответствующих выбранным фильтрам заказчиков.")
else:
    st.info("Пожалуйста, выберите технологическую операцию в верхнем меню.")

