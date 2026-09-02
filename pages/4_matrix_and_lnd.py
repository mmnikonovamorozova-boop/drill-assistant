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
        
        # Строим красивую HTML-матрицу с автоматическим переносом текста без скроллбаров
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
                padding: 6px 10px;
                border-radius: 4px;
                color: #c62828;
                font-weight: 500;
            }
            .instruction-cell {
                color: #2c3e50;
            }
            .role-active {
                background-color: #e8f5e9;
                color: #2e7d32;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            }
            .role-info {
                color: #7f8c8d;
                font-size: 13px;
            }
        </style>
        <table class="matrix-table">
            <thead>
                <tr>
                    <th style="width: 12%;">Заказчик</th>
                    <th style="width: 15%;">Пункт / Раздел</th>
                    <th style="width: 43%;">Технологическое требование / Инструкция</th>
                    <th style="width: 10%;">Инженер ННБ</th>
                    <th style="width: 10%;">Буровая вахта</th>
                    <th style="width: 10%;">Супервайзер</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for row in table_rows:
            # Стилизуем текст инструкции или запрета
            if "🛑 ЗАПРЕЩЕНО:" in row["Технологическое требование / Инструкция"]:
                clean_text = row["Технологическое требование / Инструкция"].replace("🛑 ЗАПРЕЩЕНО:", "").strip()
                action_html = f'<div class="prohib-cell"><b>🛑 ЗАПРЕЩЕНО:</b> {clean_text}</div>'
            else:
                action_html = f'<div class="instruction-cell">🟢 {row["Технологическое требование / Инструкция"]}</div>'
                
            # Стилизуем отображение ролей ИТР
            style_nnb = f'<div class="role-active">{row["Инженер по ННБ (Ваша зона)"]}</div>' if "КРИТИЧЕСКИЙ" in row["Инженер по ННБ (Ваша зона)"] else f'<div class="role-info">{row["Инженер по ННБ (Ваша зона)"]}</div>'
            style_master = f'<div class="role-active">{row["Буровой подрядчик / Вахта"]}</div>' if "Выполнение" in row["Буровой подрядчик / Вахта"] else f'<div class="role-info">{row["Буровой подрядчик / Вахта"]}</div>'
            style_super = f'<div class="role-active">{row["Супервайзер / Контроль ЛНД"]}</div>' if "Контроль" in row["Супервайзер / Контроль ЛНД"] else f'<div class="role-info">{row["Супервайзер / Контроль ЛНД"]}</div>'
            
            html_table += f"""
                <tr>
                    <td><b>{row['Заказчик']}</b></td>
                    <td><small>{row['Пункт / Раздел']}</small></td>
                    <td>{action_html}</td>
                    <td>{style_nnb}</td>
                    <td>{style_master}</td>
                    <td>{style_super}</td>
                </tr>
            """
            
        html_table += "</tbody></table>"
        
        # Выводим готовую чистую матрицу без скроллбаров прямо на экран
        st.write(html_table, unsafe_allow_html=True)
        
        # Дальше идет ваш существующий блок чек-боксов "Верификация выполнения регламентов вахтой"...


