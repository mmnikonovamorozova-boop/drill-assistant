import streamlit as st
import json
import os
from datetime import datetime

# Импортируем компоненты ReportLab для сборки PDF-актов контроля
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
# 1. Проверка авторизации инженера (в стиле вашего основного приложения)
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Выполните авторизацию.")
    st.stop()

# 2. Настройка конфигурации страницы
st.set_page_config(
    page_title="Матрица ответственности ИТР",
    page_icon="📋",
    layout="wide"
)

# 3. Заголовки страницы
st.title("📋 Матрица оперативного контроля и ответственности ИТР")
st.caption("Полевой контроль технологической дисциплины, регламентов ЛНД и верификация СМК на устье")
# Принудительные CSS-стили для оформления
st.markdown("""
<style>
.report-title {
    font-family: 'Arial', sans-serif;
    color: #000000;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# БЛОК ВЕРИФИКАЦИИ ИНТИ (НАВЕРХУ СТРАНИЦЫ)
# ==============================================================================
st.markdown("<div style='color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #6B7280; margin-bottom: 20px; line-height: 1.5; font-family: Arial, sans-serif;'><b>Верификация стандартами:</b> Модуль контроля разработан в соответствии со стандартами ИНТИ.</div>", unsafe_allow_html=True)

st.markdown("---")
# --- СБОР МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 102, Куст 12")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

st.sidebar.markdown("---")
st.sidebar.info("💡 Выберите Заказчика и операцию по центру экрана.")
@st.cache_data
import requests

@st.cache_data(ttl=3600)  # Кешируем базу на 1 час, чтобы не перегружать запросами GitHub
def load_kb_database():
    local_path = os.path.join("config", "automated_kb.json")
    
    # Пытаемся забрать свежий файл из закрытого репозитория парсера по API
    try:
        # Читаем данные из новой изолированной секции в Secrets
        token = st.secrets["kb_parser_integration"]["token"]
        user = st.secrets["kb_parser_integration"]["user"]
        
        # URL запроса к файлу в приватном репозитории drill-kb-parser
        url = f"https://github.com{user}/drill-kb-parser/contents/output_json/automated_kb.json"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3.raw"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Сохраняем свежую копию локально на сервере на всякий случай
            os.makedirs("config", exist_ok=True)
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            return json.loads(response.text)
    except Exception as e:
        st.sidebar.warning("⚠️ Не удалось обновить базу по API, загружена локальная копия.")
        
    # Если GitHub недоступен (план Б), берем сохраненный ранее локальный файл
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

kb_data = load_kb_database()

if not kb_data:
    st.warning("⚠️ Файл базы знаний не найден.")
    st.stop()
st.subheader("📋 Выбор условий операции")
col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    clients_list = list(kb_data.keys())
    selected_client = st.selectbox("💼 Заказчик (Регламент):", clients_list)

with col_sel2:
    scenarios_list = list(kb_data[selected_client].keys()) if selected_client else []
    selected_scenario = st.selectbox("🚨 Выберите сценарий:", scenarios_list)

st.markdown("---")
if selected_client and selected_scenario:
    scenario_data = kb_data[selected_client][selected_scenario]
    st.success(f"**Применимый стандарт:** `{scenario_data['regulations']['standard']}`")
    
    # Кнопки быстрого перехода в смежный расчетный модуль техкарт
    if "КНБК" in selected_scenario or "СПО" in selected_scenario:
        if st.button("🔧 Открыть техкарту КНБК"):
            st.switch_page("pages/3_tech_cards.py")
            
    elif "посадк" in selected_scenario.lower() or "затяжк" in selected_scenario.lower():
        if st.button("🛑 Открыть техкарту действий"):
            st.switch_page("pages/3_tech_cards.py")
            
    st.markdown("---")
    # Создаем три колонки для разделения ответственности ИТР
    col_dd, col_master, col_supervisor = st.columns(3)
    roles_data = scenario_data.get("roles", {})
    
    # Список для аккумулирования статусов (потребуется для генерации PDF-отчета)
    report_items = []
    
    # --- КОЛОНКА 1: ИНЖЕНЕР ПО ННБ ---
    with col_dd:
        st.markdown("<div style='background-color:#e6f3ff; padding:10px; border-radius:5px; font-weight:bold; color:#004080; text-align:center;'>🤠 Инженер по ННБ (DD)</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        tasks_dd = roles_data.get("Инженер по ННБ (DD)", [])
        if tasks_dd:
            for idx, task in enumerate(tasks_dd):
                state = st.checkbox(task, key=f"dd_{selected_client}_{idx}")
                report_items.append({"role": "Инженер по ННБ (DD)", "task": task, "status": "Выполнено" if state else "Не выполнено"})
        else:
            st.caption("Специфических требований для DD не найдено.")
    # --- КОЛОНКА 2: БУРОВОЙ МАСТЕР ---
    with col_master:
        st.markdown("<div style='background-color:#fff2cc; padding:10px; border-radius:5px; font-weight:bold; color:#b78103; text-align:center;'>👷 Буровой мастер</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        tasks_bm = roles_data.get("Буровой мастер", [])
        if tasks_bm:
            for idx, task in enumerate(tasks_bm):
                state = st.checkbox(task, key=f"bm_{selected_client}_{idx}")
                report_items.append({"role": "Буровой мастер", "task": task, "status": "Выполнено" if state else "Не выполнено"})
        else:
            st.caption("Специфических требований для Бурового мастера не найдено.")
    # --- КОЛОНКА 3: СУПЕРВАЙЗЕР / ИНЖЕНЕР ПО БУРЕНИЮ ---
    with col_supervisor:
        st.markdown("<div style='background-color:#e2f0d9; padding:10px; border-radius:5px; font-weight:bold; color:#385723; text-align:center;'>🧐 Супервайзер / ИТР</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        tasks_sv = roles_data.get("Супервайзер / Инженер по бурению", [])
        if tasks_sv:
            for idx, task in enumerate(tasks_sv):
                state = st.checkbox(task, key=f"sv_{selected_client}_{idx}")
                report_items.append({"role": "Супервайзер / ИТР", "task": task, "status": "Выполнено" if state else "Не выполнено"})
        else:
            st.caption("Специфических требований для Супервайзера не найдено.")

    st.markdown("---")
    # ==============================================================================
    # БЛОК ЭКСПОРТА И ГЕНЕРАЦИИ PDF-ОТЧЕТА (REPORTLAB)
    # ==============================================================================
    st.write("### 🖨️ Экспорт результатов контроля вахты")
    
    def generate_pdf_report(data):
        pdf_filename = "checklist_report.pdf"
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=14, spaceAfter=12)
        text_style = ParagraphStyle('TextStyle', parent=styles['Normal'], fontSize=10, spaceAfter=4)
        
        story = []
        # Формирование контента и текстовой шапки официального акта
        story.append(Paragraph(f"<b>АКТ ОПЕРАТИВНОГО КОНТРОЛЯ ТЕХНОЛОГИЧЕСКОЙ ДИСЦИПЛИНЫ</b>", title_style))
        story.append(Paragraph(f"<b>Дата и время формирования:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", text_style))
        story.append(Paragraph(f"<b>Объект контроля:</b> {well_number} | <b>Месторождение:</b> {field_name}", text_style))
        story.append(Paragraph(f"<b>Инженер по ННБ (Проверяющий):</b> {engineer_name}", text_style))
        story.append(Paragraph(f"<b>Регламент Заказчика:</b> {selected_client}", text_style))
        story.append(Paragraph(f"<b>Контролируемый сценарий:</b> {selected_scenario}", text_style))
        story.append(Spacer(1, 15))
        
        table_content = [["Роль ИТР", "Технологическое требование регламента ЛНД", "Статус"]]
        for row in data:
            task_p = Paragraph(row["task"], styles['Normal'])
            table_content.append([row["role"], task_p, row["status"]])
            
        t = Table(table_content, colWidths=[120, 360, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t)
        
        story.append(Spacer(1, 30))
        story.append(Paragraph("<b>ПОДПИСИ ОТВЕТСТВЕННЫХ ЛИЦ НА БУРОВОЙ ПЛОЩАДКЕ:</b>", text_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Инженер по ННБ (DD): _________________________", text_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph("Буровой мастер: _________________________", text_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph("Супервайзер Заказчика: _________________________", text_style))
        
        doc.build(story)
        return pdf_filename
    if st.button("⚙️ Сформировать печатную версию Акта контроля"):
        with st.spinner("Сборка печатной формы..."):
            generated_file = generate_pdf_report(report_items)
            with open(generated_file, "rb") as f:
                st.download_button(
                    label="📥 Скачать готовый Акт контроля (PDF)",
                    data=f,
                    file_name=f"Act_{selected_client.replace(' ', '_')}_{well_number.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key="download_lnd_report_btn"
                )
