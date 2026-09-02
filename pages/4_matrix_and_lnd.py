import streamlit as st
import json
import os
import requests
import pandas as pd
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

        # Новая структура матрицы, на 100% повторяющая ваш шаблон из Word
        html_table = """
        <style>
            .matrix-table {
                width: 100%;
                border-collapse: collapse;
                font-family: 'Segoe UI', sans-serif;
                margin-bottom: 25px;
                font-size: 14px;
            }
            .matrix-table th {
                background-color: #2c3e50;
                color: white;
                padding: 12px;
                text-align: left;
                border: 1px solid #bdc3c7;
                font-weight: 600;
            }
            .matrix-table td {
                padding: 12px;
                border: 1px solid #bdc3c7;
                vertical-align: top;
                line-height: 1.5;
                word-wrap: break-word;
            }
            .matrix-table tr:nth-child(even) {
                background-color: #f8f9fa;
            }
            .prohib-cell {
                background-color: #ffebee;
                border-left: 4px solid #c62828 !important;
                padding: 8px 12px;
                border-radius: 4px;
                color: #c62828;
                font-weight: 500;
            }
            .instruction-cell {
                color: #2c3e50;
            }
            .status-resp {
                background-color: #e8f5e9;
                color: #2e7d32;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
                text-align: center;
            }
            .status-control {
                background-color: #fff3e0;
                color: #e65100;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
                text-align: center;
            }
            .status-info {
                color: #7f8c8d;
                font-size: 13px;
                text-align: center;
            }
        </style>
        <table class="matrix-table">
            <thead>
                <tr>
                    <th style="width: 10%;">Заказчик</th>
                    <th style="width: 12%;">Пункт / Раздел</th>
                    <th style="width: 38%;">Технологическое требование / Инструкция</th>
                    <th style="width: 10%; text-align: center;">Инженер ННБ</th>
                    <th style="width: 10%; text-align: center;">Буровой подрядчик</th>
                    <th style="width: 10%; text-align: center;">Супервайзер</th>
                    <th style="width: 10%; text-align: center;">Подрядчик по растворам</th>
                </tr>
            </thead>
            <tbody>
        """

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
                
            client_name = item.get("client", "Неизвестный")
            action_text = item.get("action", "")
            
            # Фильтрация по выбранным заказчикам
            if client_filter and client_name not in client_filter:
                continue
                
            # Проверяем, является ли пункт запретом
            is_prohib = "ЗАПРЕЩАЕТСЯ" in action_text.upper() or "🛑" in action_text
            if type_filter == "Только КРИТИЧЕСКИЕ ЗАПРЕТЫ" and not is_prohib:
                continue

            # Форматируем текст ячейки требования
            if is_prohib:
                clean_req = action_text.replace("ЗАПРЕЩАЕТСЯ:", "").replace("🛑", "").strip()
                action_html = f'<div class="prohib-cell"><b>🛑 ЗАПРЕЩАЕТСЯ:</b> {clean_req}</div>'
            else:
                action_html = f'<div class="instruction-cell">🟢 {action_text}</div>'

            # Функция для красивой цветовой стилизации статусов RACI из ИИ
            def style_status(status_text):
                st_low = str(status_text).lower()
                if "ответствен" in st_low:
                    return f'<div class="status-resp">Ответственный</div>'
                elif "контрол" in st_low:
                    return f'<div class="status-control">Контроль</div>'
                return f'<div class="status-info">Проинформирован</div>'

            # Извлекаем статусы ролей, которые разметил ИИ-аналитик
            nnb_html = style_status(item.get("nnb", "Проинформирован"))
            contractor_html = style_status(item.get("contractor", "Проинформирован"))
            supervisor_html = style_status(item.get("supervisor", "Проинформирован"))
            mud_html = style_status(item.get("mud_service", "Проинформирован"))

            html_table += f"""
                <tr>
                    <td><b>{client_name}</b></td>
                    <td><small>п. {item.get('step_id', 'Б/Н')}<br><i style="color:#7f8c8d;">{item.get('original_section', '')[:20]}...</i></small></td>
                    <td>{action_html}</td>
                    <td>{nnb_html}</td>
                    <td>{contractor_html}</td>
                    <td>{supervisor_html}</td>
                    <td>{mud_html}</td>
                </tr>
            """

        html_table += "</tbody></table>"
        
        # Выводим готовую интерактивную матрицу ИТР на экран
        st.html(html_table)

        # --- БЛОК СБОРА МЕТАДАННЫХ ДЛЯ ВЕРИФИКАЦИИ ---
        st.markdown("### 📝 Верификация выполнения регламентов вахтой")
        verified_tasks = []
        for i, item in enumerate(items[:10]):
            if client_filter and item.get("client") not in client_filter:
                continue
            task_title = item.get("action", "")[:90] + "..."
            state = st.checkbox(f"{item.get('client')} | п. {item.get('step_id', 'Б/Н')}: {task_title}", key=f"chk_v_{i}")
            if state:
                verified_tasks.append(item)
