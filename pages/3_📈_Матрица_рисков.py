import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="Матрица рисков устья", layout="wide")
st.title("📈 Матрица технологических рисков и осложнений на устье")
st.caption("ЭКСПЕРТНАЯ СИСТЕМА ПРЕДОТВРАЩЕНИЯ БРАКА И НПВ ПРИ СБОРКЕ И ОПРЕССОВКЕ КНБК")
st.markdown("---")

# Техническая отметка о соответствии стандартам ИНТИ
st.markdown(
    '<div style="color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #1E3A8A; margin-bottom: 20px;">'
    '<b>Верификация стандартами:</b> СТО ИНТИ S.QS.7 и СТО ИНТИ S.QS.8.'
    '</div>', 
    unsafe_allow_html=True
)

# --- 2. СБОР МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")
current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

# --- 3. ИНТЕРФЕЙС КАТЕГОРИЙ АНАЛИЗА ---
section = st.radio(
    "Выберите технологический этап контроля:",
    ["🔧 1. Сборка и ВИК КНБК", "💦 2. Опрессовка КНБК и MWD"]
)
st.markdown("---")

# Инициализация переменных для Акта
risk_color = "#16A34A"
risk_level = "НИЗКИЙ (ШТАТНЫЙ)"
verdict_text = "Технологический этап выполнен в соответствии с регламентом."
recommendations = ["Продолжить плановые работы."]
defect_name = "Отклонений не выявлено"

# --- ЭТАП 1: СБОРКА И ВИК ---
if section == "🔧 1. Сборка и ВИК КНБК":
    defect_type = st.selectbox(
        "Выберите отклонение/дефект:",
        ["Не выбрано", "Овальность замка ('Яйцо')", "Избыток смазки", "Зажим статора ВЗД", "Задиры резьбы"]
    )
    # [Логика обработки дефектов сборки: Овальность, Смазка, ВЗД, Задиры]
    if defect_type == "Овальность замка ('Яйцо')":
        defect_name = "Овальность замка муфты КНБК ('Яйцо')"
        st.error("⚠️ СУТЬ РИСКА: Сминание муфты сухарями, риск промыва.")
        ans = st.radio("Обнаружены радиальные наплывы?", ["Нет", "Да (Брак)"])
        if ans == "Да (Брак)":
            risk_color, risk_level, verdict_text, recommendations = "#DC2626", "КРИТИЧЕСКИЙ", "СВИНЧИВАНИЕ ЗАПРЕЩЕНО!", ["Отбраковка", "Резерв"]
        else: verdict_text = "Зазор в норме."

    elif defect_type == "Избыток смазки":
        defect_name = "Риск гидроклина"
        st.error("⚠️ СУТЬ РИСКА: Ложный момент затяжки.")
        ans = st.radio("Смазка нанесена плотным комком?", ["Нет", "Да, избыток"])
        if ans == "Да, избыток":
            risk_color, risk_level, verdict_text, recommendations = "#D97706", "ПОВЫШЕННЫЙ", "СТОП РАБОТЫ!", ["Удалить смазку", "Перенанести по регламенту"]

    elif defect_type == "Зажим статора ВЗД":
        defect_name = "Ошибочный зажим статора ВЗД"
        st.error("⚠️ СУТЬ РИСКА: Смятие корпуса, отслоение резины.")
        ans = st.radio("Зажим на крашеную часть?", ["Нет", "Да, зажим"])
        if ans == "Да, зажим":
            risk_color, risk_level, verdict_text, recommendations = "#DC2626", "КРИТИЧЕСКИЙ", "СВИНЧИВАНИЕ ЗАПРЕЩЕНО!", ["Освободить", "Проверить ВЗД"]

    elif defect_type == "Задиры резьбы":
        defect_name = "Задиры резьбы"
        ans = st.radio("Возможна зачистка?", ["Нет", "Да, зачистка"])
        if ans == "Да, зачистка":
            risk_color, risk_level, verdict_text, recommendations = "#D97706", "ПОВЫШЕННЫЙ", "Требуется ремонт.", ["Зачистка", "Повторная смазка"]
        elif ans == "Нет":
            risk_color, risk_level, verdict_text, recommendations = "#DC2626", "КРИТИЧЕСКИЙ", "ОТБРАКОВКА!", ["Акт дефектации", "Резерв"]

# --- ЭТАП 2: ОПРЕССОВКА И MWD (С НОВЫМ РИСКОМ) ---
elif section == "💦 2. Опрессовка КНБК и MWD":
    p_type_2 = st.selectbox(
        "Выберите отклонение:",
        ["Не выбрано", "Течь КНБК", "Низкое давление (Риск ложной отбраковки)"]
    )
    
    if p_type_2 == "Течь КНБК":
        defect_name = "Негерметичность КНБК"
        st.warning("СТОП насосы!")
        ans = st.radio("Локализация:", ["Замок", "Корпус ВЗД/MWD"])
        if ans == "Замок":
            risk_color, risk_level, verdict_text, recommendations = "#D97706", "ПОВЫШЕННЫЙ", "Недотяг.", ["Докрепить", "Повторный тест"]
        else:
            risk_color, risk_level, verdict_text, recommendations = "#DC2626", "КРИТИЧЕСКИЙ", "БРАК!", ["Демонтаж", "Резерв"]

    elif p_type_2 == "Низкое давление (Риск ложной отбраковки)":
        defect_name = "Риск ложной отбраковки MWD (Низкое давление)"
        st.error("⚠️ НОВЫЙ РИСК: Ложная отбраковка MWD из-за насосов (< 25% давления).")
        ans = st.radio("Стабилен ли расход?", ["Да, MWD молчит", "Нет, насосы стучат"])
        if ans == "Нет, насосы стучат":
            risk_color, risk_level, verdict_text, recommendations = "#D97706", "ВЫСОКИЙ (ВНЕШНИЙ РИСК)", "СТОП ОТБРАКОВКА!", ["Ревизия насосов", "Переход на насос №2"]
        elif ans == "Да, MWD молчит":
            risk_color, risk_level, verdict_text, recommendations = "#DC2626", "КРИТИЧЕСКИЙ", "ОТКАЗ MWD", ["Разрот", "Замена MWD"]

# --- 4. ГЕНЕРАЦИЯ HTML-КАРТЫ (С ПОДДЕРЖКОЙ ТЕМНОЙ ТЕМЫ) ---
if risk_color == "#DC2626": 
    header_title = "🚨 КАРТА РИСКОВ — ЗАПРЕТ СВИНЧИВАНИЯ / РАБОТ"
    bg_verdict = "#FEE2E2" # Светло-красный фон для аварийного вердикта
    text_verdict = "#991B1B" # Темно-красный текст
elif risk_color == "#D97706": 
    header_title = "⚠️ КАРТА РИСКОВ — ПЛАН ПРЕВЫШЕНИЯ ПОТЕРЬ"
    bg_verdict = "#FEF3C7" # Светло-желтый фон
    text_verdict = "#92400E" # Темно-оранжевый текст
else: 
    header_title = "🏆 КАРТА РИСКОВ — СООТВЕТСТВИЕ СТАНДАРТУ"
    bg_verdict = "#D1FAE5" # Светло-зеленый фон
    text_verdict = "#065F46" # Темно-зеленый текст

# Формируем список рекомендаций в виде HTML-строк
rec_html_lines = "".join([f"<li style='margin: 4px 0;'>{r}</li>" for r in recommendations])

html_risk_act = f"""
<div style="border:3px solid {risk_color}; padding:20px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#111827; line-height:1.5;">
    <h2 style="text-align:center; color:#1E3A8A; margin-top:0; font-size:20px;">ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>
    <h3 style="text-align:center; color:#4B5563; margin-top:-10px; font-size:16px;">КАРТА ПРЕВЕНТИВНОГО МОНИТОРИНГА РИСКОВ НА УСТЬЕ</h3>
    <hr style="border:1px solid #1E3A8A; margin-bottom:15px;">
    
    <p style="margin: 6px 0; font-size:14px;"><b>Дата/Время:</b> {current_time} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> {field_name}</p>
    <p style="margin: 6px 0; font-size:14px;"><b>Объект / Скважина:</b> {well_number} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> {engineer_name}</p>
    <p style="margin: 6px 0; font-size:14px;"><b>Контролируемый фактор:</b> <span style="color:#1E3A8A; font-weight:bold;">{defect_name}</span> | <b>Уровень угрозы ОСМК:</b> <span style="color:{risk_color}; font-weight:bold;">{risk_level}</span></p>
    
    <div style="background-color:{bg_verdict}; border:1px solid {risk_color}; padding:12px; border-radius:6px; margin:15px 0;">
        <h4 style="color:{text_verdict}; margin:0; text-align:center; font-size:15px;">📋 ВЕРДИКТ ЭКСПЕРТНОЙ СИСТЕМЫ: {verdict_text}</h4>
    </div>
    
    <h4 style="color:#1E3A8A; margin-top:15px; margin-bottom:5px; border-bottom:1px solid #D1D5DB; padding-bottom:3px; font-size:14px;">НЕОБХОДИМЫЕ ПРЕВЕНТИВНЫЕ МЕРОПРИЯТИЯ (СТО ИНТИ):</h4>
    <ul style="margin: 0; padding-left: 20px; font-size:13px; color:#374151;">
        {rec_html_lines}
    </ul>
    
    <p style="font-size:11px; color:#6B7280; text-align:center; margin-top:25px; border-top:1px dashed #D1D5DB; padding-top:8px; margin-bottom:0;">Сгенерировано в цифровом модуле • Для печати нажмите Ctrl + P</p>
</div>
"""

st.markdown("---")
st.subheader("📥 Официальный бланк Карты рисков для включения в суточный рапорт:")

# Выводим через сейф-контейнер с запасом высоты под списки
components.html(html_risk_act, height=400, scrolling=True)

components.html(html_risk_act, height=450, scrolling=True)

# --- 5. ФУТЕР ---
st.info("💡 Нажмите **`Ctrl + P`** для сохранения в PDF.")
