import streamlit as st
import json
import os
import requests
import pandas as pd
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- ПРОВЕРКА АВТОРИЗАЦИИ ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Выполните авторизацию на главной странице.")
    st.stop()

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="Матрица ответственности ИТР", page_icon="📋", layout="wide")
st.title("📋 Матрица оперативного контроля и ответственности ИТР")
st.caption("Полевой контроль технологической дисциплины, регламентов ЛНД и верификация СМК на устье")

# --- ОТКАЗОУСТОЙЧИВАЯ ФУНКЦИЯ ЗАГРУЗКИ (GITHUB + ЛОКАЛЬНЫЙ БЭКАП) ---
@st.cache_data(ttl=60)
def load_kb_database():
    backup_filename = "local_kb_backup.json"
    
    # Попытка №1: Идём в GitHub API за свежим JSON
    try:
        token = st.secrets["kb_parser_integration"]["token"]
        user = st.secrets["kb_parser_integration"]["user"].strip().replace("/", "")
        
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
        
        if response.status_code == 200:
            data = json.loads(response.text)
            # Локально сохраняем самую свежую версию на случай будущих сбоев
            with open(backup_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return data
        else:
            st.sidebar.warning(f"⚠️ GitHub вернул статус {response.status_code}. Переключаюсь на бэкап.")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Ошибка сети при связи с GitHub: {str(e)}. Ищу локальный файл.")

    # Попытка №2: Если GitHub упал, ищем сохранённую ранее копию в памяти
    if os.path.exists(backup_filename):
        try:
            with open(backup_filename, "r", encoding="utf-8") as f:
                st.sidebar.info("🔄 Данные успешно загружены из локального кэша памяти.")
                return json.load(f)
        except Exception as e:
            st.sidebar.error(f"❌ Не удалось прочесть даже локальный бэкап: {str(e)}")
            return None
    else:
        st.sidebar.error("❌ Критическая ошибка: GitHub недоступен, а локальный кэш памяти пуст.")
        return None

# Загружаем базу данных
kb_data = load_kb_database()
if not kb_data:
    st.warning("⚠️ База знаний полностью недоступна. Проверьте подключение.")
    st.stop()
# --- СБОР МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 102, Куст 12")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")
st.sidebar.markdown("---")
st.sidebar.info("💡 Метаданные автоматически попадут в скачиваемый PDF-акт верификации.")
st.subheader("📋 Условия проведения операции на устье")

# Получаем список технологических операций
global_operations = list(kb_data.keys()) if kb_data else []
selected_op = st.selectbox("🎯 Выберите технологическую операцию:", global_operations, index=0)

# Сбор доступных заказчиков
available_clients = []
items = []

if selected_op and isinstance(kb_data.get(selected_op), list):
    items = kb_data[selected_op]
    available_clients = list(set(item.get("client", "Неизвестный") for item in items if isinstance(item, dict)))
else:
    if selected_op and isinstance(kb_data.get(selected_op), dict):
        available_clients = [selected_op]

# Разметка панели управления фильтрами
col_f1, col_f2 = st.columns(2)
with col_f1:
    client_filter = st.multiselect("💼 Фильтр по Заказчикам (По умолчанию все):", available_clients)
with col_f2:
    type_filter = st.radio("🔍 Фильтр требований:", ["Все пункты", "Только КРИТИЧЕСКИЕ ЗАПРЕТЫ"], horizontal=True)

# Дополнительные инструменты инженера ННБ
col_f3, col_f4 = st.columns([2, 1])
with col_f3:
    search_query = st.text_input("🔎 Smart Поиск по ключевому слову (например: опрессовка, гайка, шаблон):", value="")
with col_f4:
    st.markdown("<br>", unsafe_allow_html=True)
    nnb_only_filter = st.toggle("⚡ Только моя зона (ННБ)", value=False)

st.markdown("---")
if items and isinstance(items, list):
    table_rows = []
    
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        client_name = item.get("client", "Неизвестный")
        action_text = item.get("action", "")
        action_upper = action_text.upper()
        
        # Интеллектуальный поиск критических запретов
        is_prohib = any(w in action_upper for w in ["ЗАПРЕЩ", "НЕ ДОПУСК", "🛑", "ЗАПРЕТИТЬ"])
        # Применяем фильтр по Заказчикам
        if client_filter and client_name not in client_filter:
            continue
            
        # Применяем фильтр по запретам
        if type_filter == "Только КРИТИЧЕСКИЕ ЗАПРЕТЫ" and not is_prohib:
            continue
            
        # Применяем текстовый Smart-поиск
        if search_query and search_query.lower() not in action_text.lower():
            continue
        # Фильтр зоны ответственности инженера по ННБ
                # Фильтр зоны ответственности: оставляем ТОЛЬКО статус "Исполнитель"
        nnb_status = item.get("nnb", "Проинформирован")
        if nnb_only_filter and "исполнитель" not in str(nnb_status).lower():
            continue
            
        master_status = item.get("contractor", "Проинформирован")
        super_status = item.get("supervisor", "Проинформирован")

        # Упаковываем данные в строку для датафрейма (УБРАЛИ КОЛОНКУ РАЗДЕЛ)
        table_rows.append({
            "Заказчик": client_name,
            "Пункт": f"п. {item.get('step_id', 'Б/Н')}",
            "Технологическое требование": action_text if not is_prohib else f"🛑 ЗАПРЕЩЕНО: {action_text}",
            "Инженер ННБ": nnb_status,
            "Буровой подрядчик": master_status,
            "Супервайзер": super_status
        })
    if table_rows:
        st.markdown(f"### 📊 Сводная таблица взаимодействия сторон: *{selected_op}*")
        
    # Наводим красоту: центрируем заголовки и расширяем колонки статусов до 13%
        s = "<style>.mt { width:100%; border-collapse:collapse; font-size:14px; }"
        s += ".mt th { background:#f1f3f5; padding:10px; border:1px solid #dee2e6; text-align:center; }"
        s += ".mt td { padding:10px; border:1px solid #dee2e6; vertical-align:top; word-break:break-word; }"
        s += ".pr { background:#ffcccc !important; }</style>"
        
        h = "<table class='mt'><thead><tr>"
        h += "<th style='width:9%;'>Заказчик</th><th style='width:6%;'>Пункт</th>"
        h += "<th style='width:46%; text-align:left;'>Технологическое требование</th>"
        h += "<th style='width:13%;'>Инженер ННБ</th><th style='width:13%;'>Буровой подрядчик</th>"
        h += "<th style='width:13%;'>Супервайзер</th>"
        h += "</tr></thead><tbody>"
        
        html_table = s + h
        for r in table_rows:
            is_p = "🛑 ЗАПРЕЩЕНО" in str(r["Технологическое требование"])
            row_style = " class='pr'" if is_p else ""
            
            row_html = f"<tr{row_style}>"
            row_html += f"<td style='text-align:center;'>{r['Заказчик']}</td>"
            row_html += f"<td style='text-align:center;'>{r['Пункт']}</td>"
            row_html += f"<td>{r['Технологическое требование']}</td>"
            # Центрируем роли участников внутри расширенных ячеек
            row_html += f"<td style='text-align:center;'>{r['Инженер ННБ']}</td>"
            row_html += f"<td style='text-align:center;'>{r['Буровой подрядчик']}</td>"
            row_html += f"<td style='text-align:center;'>{r['Супервайзер']}</td>"
            row_html += "</tr>"
            
            html_table += row_html
            
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)

        for r in table_rows:
            is_p = "🛑 ЗАПРЕЩЕНО" in str(r["Технологическое требование"])
            row_style = " class='pr'" if is_p else ""
            
            # Внутри цикла идет 12 пробелов для сборки строк:
            row_html = f"<tr{row_style}>"
            row_html += f"<td>{r['Заказчик']}</td>"
            row_html += f"<td>{r['Пункт']}</td>"
            row_html += f"<td>{r['Технологическое требование']}</td>"
            row_html += f"<td>{r['Инженер ННБ']}</td>"
            row_html += f"<td>{r['Буровой подрядчик']}</td>"
            row_html += f"<td>{r['Супервайзер']}</td>"
            row_html += "</tr>"
            
            # Возврат на 8 пробелов внутри for:
            html_table += row_html
            
        # Возврат на 4 пробела внутри if:
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)

        # --- ИНТЕРАКТИВНЫЙ ЧЕК-ЛИСТ ВЕРИФИКАЦИИ ---
        st.markdown("---")
        st.markdown("### 📝 Полевой чек-лист верификации регламентов ЛНД")
        st.caption("Отметьте выполненные на устье операции для включения их в официальный рапорт")
        
        verified_tasks = []
        # Выводим пункты для чек-листа
        for i, row in enumerate(table_rows[:15]):
            task_label = f"{row['Заказчик']} | {row['Пункт']}: {row['Технологическое требование'][:80]}..."
            if st.checkbox(task_label, key=f"chk_v_{i}"):
                verified_tasks.append(row)
        # --- КНОПКА ГЕНЕРАЦИИ PDF-АКТА ---
        if verified_tasks:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📄 Сформировать официальный Акт верификации ЛНД"):
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                styles = getSampleStyleSheet()
                # Собираем текстовый рапорт верификации регламентов
                report_txt = "АКТ ПОЛЕВОЙ ВЕРИФИКАЦИИ ТЕХНОЛОГИЧЕСКОЙ ДИСЦИПЛИНЫ\n"
                report_txt += f"Дата проверки: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                report_txt += f"Месторождение: {field_name}\n"
                report_txt += f"Скважина / Куст: {well_number}\n"
                report_txt += f"Инженер по ННБ: {engineer_name}\n"
                report_txt += "========================================\n"
                report_txt += "Перечень проверенных требований регламентов ЛНД:\n\n"
                
                for idx, t in enumerate(verified_tasks, 1):
                    report_txt += f"{idx}. [{t['Заказчик']}] {t['Пункт']}\n Требование: {t['Технологическое требование']}\n\n"
                
                st.success("✅ Акт верификации успешно сформирован!")
                st.download_button(
                    label="📥 Скачать Акт верификации (TXT)",
                    data=report_txt,
                    file_name=f"Verification_Act_{well_number.replace(' ', '_')}.txt",
                    mime="text/plain"
                )


