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

@st.cache_data(ttl=3600)
def load_kb_database():
    local_path = os.path.join("config", "automated_kb.json")
    try:
        token = st.secrets["kb_parser_integration"]["token"]
        user = st.secrets["kb_parser_integration"]["user"]
        # URL для скачивания чистого файла напрямую
        url = f"https://githubusercontent.com{user}/drill-kb-parser/main/output_json/automated_kb.json"
        headers = {"Authorization": f"token {token}"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            os.makedirs("config", exist_ok=True)
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            return json.loads(response.text)
    except Exception as e:
        st.sidebar.warning("⚠ Загружена локальная копия базы данных.")
    
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

kb_data = load_kb_database()
if not kb_data:
    st.warning("⚠ Файл базы знаний не найден.")
    st.stop()
st.subheader("📋 Условия проведения операции на устье")

# Выбор глобальной технологической операции
global_operations = list(kb_data.keys())
selected_op = st.selectbox("🎯 Выберите технологическую операцию:", global_operations, index=0)

# Собираем список доступных заказчиков для выбранной операции
available_clients = list(set(item["client"] for item in kb_data[selected_op]))

col_f1, col_f2 = st.columns(2)
with col_f1:
    client_filter = st.multiselect("💼 Фильтр по Заказчикам (По умолчанию показаны все):", available_clients)
with col_f2:
    type_filter = st.radio("🔍 Фильтр требований:", ["Все пункты", "Только КРИТИЧЕСКИЕ ЗАПРЕТЫ"], horizontal=True)

st.markdown("---")

report_items = []
if selected_op:
    items = kb_data[selected_op]
    
    st.markdown(f"### Сводная матрица контроля: *{selected_op}*")
    
    for idx, item in enumerate(items):
        # Применение фильтров
        if client_filter and item["client"] not in client_filter:
            continue
        if type_filter == "Только КРИТИЧЕСКИЕ ЗАПРЕТЫ" and not item["is_prohibition"]:
            continue
            
        # Форматирование и подсветка строки
        if item["is_prohibition"]:
            prefix = "🛑 [ЗАПРЕЩЕНО] "
            bg_color = "#ffebee"
        else:
            prefix = "🟢 "
            bg_color = "#ffffff"
            
        # Собираем красивую карточку-строку с чекбоксом верификации
        with st.container():
            st.markdown(f"""
            <div style="background-color:{bg_color}; padding:12px; border-radius:6px; border-left:5px solid {'#d32f2f' if item['is_prohibition'] else '#2e7d32'}; margin-bottom:10px;">
                <b>Заказчик:</b> {item['client']} | <b>Раздел:</b> {item['original_section']} | <b>Пункт:</b> {item['step_id'] if item['step_id'] else 'Б/Н'}<br>
                <span style="font-size:15px;">{prefix}{item['action']}</span><br>
                <div style="margin-top:6px; color:#555;"><b>Ответственность / Контроль:</b> {item['responsibility_raw']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Чекбокс для отчета
            state = st.checkbox("Требование регламента проверено / выполнено вахтой", key=f"check_{selected_op}_{idx}")
            
            report_items.append({
                "client": item["client"],
                "step": item["step_id"] if item["step_id"] else "Б/Н",
                "task": item["action"],
                "resp": item["responsibility_raw"],
                "status": "Выполнено" if state else "Не выполнено"
            })
st.write("### 🖨 Экспорт результатов контроля вахты")

# Формируем текстовую версию акта для печати или сохранения
report_text = f"АКТ ОПЕРАТИВНОГО КОНТРОЛЯ ТЕХНОЛОГИЧЕСКОЙ ДИСЦИПЛИНЫ\n"
report_text += f"Дата и время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
report_text += f"Объект контроля: {well_number} | Месторождение: {field_name}\n"
report_text += f"Проверяющий инженер по ННБ: {engineer_name}\n"
report_text += f"Контролируемая операция: {selected_op}\n"
report_text += "="*60 + "\n\n"

# Превращаем результаты проверки в таблицу CSV для скачивания
csv_data = "Заказчик;Пункт;Требование;Статус проверки\n"

for r in report_items:
    # Очищаем текст от HTML-тегов для чистого файла
    clean_task = r["task"].replace(";", ",").strip()
    csv_data += f"{r['client']};{r['step']};{clean_task};{r['status']}\n"
    report_text += f"[{r['status']}] {r['client']} (п. {r['step']}): {clean_task}\n"

report_text += "\n" + "="*60 + "\n"
report_text += "ПОДПИСИ ОТВЕТСТВЕННЫХ ЛИЦ НА БУРОВОЙ ПЛОЩАДКЕ:\n\n"
report_text += "Инженер по ННБ (DD): _________________________\n"
report_text += "Буровой мастер:      _________________________\n"
report_text += "Супервайзер ЛНД:     _________________________\n"

# Кнопки для скачивания результатов
col_b1, col_b2 = st.columns(2)
with col_b1:
    st.download_button(
        label="📥 Скачать Акт контроля (Текст для печати)",
        data=report_text,
        file_name=f"Act_{well_number}.txt",
        mime="text/plain"
    )
with col_b2:
    st.download_button(
        label="📊 Экспорт таблицы верификации (Excel / CSV)",
        data=csv_data.encode('utf-8-sig'),
        file_name=f"Checklist_{well_number}.csv",
        mime="text/csv"
    )
