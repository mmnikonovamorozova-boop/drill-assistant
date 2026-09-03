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

    # Выводим собранный датафрейм на экран
        # Выводим собранный датафрейм на экран
    if table_rows:
        df_matrix = pd.DataFrame(table_rows)
        st.markdown(f"### 📊 Сводная таблица взаимодействия сторон: *{selected_op}*")
        
        # Функция подсветки запретов
        def highlight_prohibitions(row):
            if "🛑 ЗАПРЕЩЕНО" in str(row["Технологическое требование"]):
                return ["background-color: #ffcccc"] * len(row)
            return [""] * len(row)
            
        # Настройка отображения таблицы с принудительным переносом строк (wrap=True)
        st.dataframe(
            df_matrix.style.apply(highlight_prohibitions, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Технологическое требование": st.column_config.TextColumn(
                    width="large",
                    wrap=True
                ),
                "Инженер ННБ": st.column_config.TextColumn(width="medium", wrap=True),
                "Буровой подрядчик": st.column_config.TextColumn(width="medium", wrap=True),
                "Супервайзер": st.column_config.TextColumn(width="medium", wrap=True)
            }

        # --- ИНТЕРАКТИВНЫЙ ЧЕК-ЛИСТ ВЕРИФИКАЦИИ ---
        st.markdown("---")
        st.markdown("### 📝 Полевой чек-лист верификации регламентов ЛНД")
        st.caption("Отметьте выполненные на устье операции для включения их в официальный рапорт")
        
        verified_tasks = []
        # Выводим первые 15 отфильтрованных пунктов для экспресс-контроля
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
                
                # Собираем структуру документа
                story = [
                    Paragraph("<b>АКТ ПОЛЕВОЙ ВЕРИФИКАЦИИ ТЕХНОЛОГИЧЕСКОЙ ДИСЦИПЛИНЫ</b>", styles["Title"]),
                    Spacer(1, 15),
                    Paragraph(f"<b>Дата проверки:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles["Normal"]),
                    Paragraph(f"<b>Месторождение:</b> {field_name}", styles["Normal"]),
                    Paragraph(f"<b>Скважина / Куст:</b> {well_number}", styles["Normal"]),
                    Paragraph(f"<b>Инженер по ННБ:</b> {engineer_name}", styles["Normal"]),
                    Spacer(1, 15),
                    Paragraph("<b>Перечень проверенных требований и регламентов ЛНД:</b>", styles["Heading3"]),
                    Spacer(1, 10)
                ]
                
                # Добавляем отмеченные задачи в PDF
                for t in verified_tasks:
                    bullet = f"• [{t['Заказчик']}] {t['Пункт']} - {t['Технологическое требование']}"
                    story.append(Paragraph(bullet, styles["Normal"]))
                    story.append(Spacer(1, 5))
                    
                story.append(Spacer(1, 20))
                story.append(Paragraph("<b>Подписи сторон:</b>", styles["Heading3"]))
                story.append(Spacer(1, 10))
                story.append(Paragraph("Инженер по ННБ: _______________________", styles["Normal"]))
                story.append(Spacer(1, 10))
                story.append(Paragraph("Буровой мастер / Супервайзер: _______________________", styles["Normal"]))
                
                doc.build(story)
                buffer.seek(0)
                
                st.success("✅ Акт успешно сформирован!")
                st.download_button(
                    label="📥 Скачать Акт верификации (PDF)",
                    data=buffer,
                    file_name=f"Verification_Act_{well_number.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

