import streamlit as st

# Проверка авторизации инженера
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Выполните авторизацию.")
    st.stop()

st.set_page_config(page_title="Технологические карты КНБК", page_icon="🔧", layout="wide")
st.title("🔩 Интерактивные технологические карты сборки КНБК")
st.caption("Полевой контроль технологической дисциплины и верификация СМК")
# Принудительные CSS-стили для корректного вывода бланка на печать в PDF
st.markdown("""
<style>
    /* Делаем так, чтобы при прямой генерации документа не было лишних полей */
    @page {
        size: A4;
        margin: 20mm;
    }
    .print-preview {
        font-family: 'Arial', sans-serif;
        color: #000000 !important;
        background-color: #ffffff !important;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# БЛОК ВЕРИФИКАЦИИ ИНТИ (НАВЕРХУ СТРАНИЦЫ)
# ==============================================================================
st.markdown("<div style='color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #6B7280; margin-bottom: 20px; line-height: 1.5; font-family: Arial, sans-serif;'><b>Верификация стандартами:</b> Данный интерактивный модуль оперативного контроля технологической дисциплины на устье разработан в строгом соответствии с требованиями отраслевых стандартов <b>СТО ИНТИ S.30.13</b> в части проведения визуально-измерительного контроля резьбовых соединений и регламентации гидроиспытаний, <b>СТО ИНТИ S.QS.7 (п. 7.4.2 «Верификация закупаемой продукции», п. 7.5.1 «Управление производством и предоставлением услуг»)</b> в части обеспечения персонала четкими документированными инструкциями, регламентации процессов нанесения резьбовых смазок и контроля крутящих моментов свинчивания КНБК, а также <b>СТО ИНТИ S.QS.8 (п. 5.3.1 «Управление процессами. Контроль параметров» и п. 5.7.2 «Управление оборудованием для мониторинга и измерений»)</b> в части обязательного вывода буровых насосов на регламентный режим расхода при опрессовке (не менее 25% от рабочего) и контроля исправности, калибровки и метрологического подтверждения применяемых на буровой площадке гидравлических ключей и манометров устьевого манифольда.</div>", unsafe_allow_html=True)

st.markdown("---")

# --- 3. СБОР МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

st.subheader("📋 Выбор условий инцидента")
selected_client = st.selectbox(
    "💼 Заказчик (Проект):",
    ["ПАО Роснефть", "ПАО Газпром нефть", "ПАО ЛУКОЙЛ", "Независимый оператор (ИНТИ)"]
)
problem_type = st.selectbox(
    "🚨 Выберите возникший инцидент/сценарий:",
    [
        "Опрессовка: Течь/падение давления в замковом стыке КНБК",
        "Сборка: Избыточное нанесение резьбовой смазки",
        "Крепление: Неверное позиционирование ключа на корпусе ВЗД/ТБ"
    ]
)

st.markdown("---")

# ==============================================================================
# 📥 АВТОМАТИЧЕСКАЯ ЗАГРУЗКА БАЗЫ ТРЕБОВАНИЙ ИЗ JSON-ФАЙЛА
# ==============================================================================
import json

@st.cache_data  # Кэшируем функцию, чтобы файл не перечитывался с диска при каждом клике инженера
def load_tech_requirements():
    with open("tech_requirements.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Инициализируем нашу базу знаний динамически из файла
tech_knowledge_base = load_tech_requirements()
# ==============================================================================

st.markdown("---")

# Формируем контент для экспорта без элементов управления Streamlit
export_html = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>{scenario_data['title'] if 'scenario_data' in locals() else 'Технологическая карта'}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 30px; line-height: 1.6; color: #333; }}
        .header {{ margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .meta-table {{ width: 100%; margin-bottom: 20px; }}
        .meta-table td {{ width: 50%; padding: 5px; }}
        .section {{ margin-top: 20px; margin-bottom: 10px; font-weight: bold; font-size: 16px; border-bottom: 1px solid #ddd; }}
        .info-box {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #0284c7; margin: 10px 0; }}
        .step {{ margin-bottom: 8px; }}
        .footer {{ text-align: center; color: #999; font-size: 11px; margin-top: 50px; border-top: 1px solid #ddd; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>📄 ТЕХНОЛОГИЧЕСКАЯ КАРТА ЛИКВИДАЦИИ ИНЦИДЕНТА</h2>
    </div>
    <table class="meta-table">
        <tr>
            <td><b>Месторождение:</b> {field_name}</td>
            <td><b>Проект (Заказчик):</b> {selected_client}</td>
        </tr>
        <tr>
            <td><b>Скважина / Куст:</b> {well_number}</td>
            <td><b>Инженер по ННБ:</b> {engineer_name}</td>
        </tr>
    </table>
"""

# Если сценарий выбран, дописываем в файл только полезные текстовые данные
if problem_type in tech_knowledge_base:
    s_data = tech_knowledge_base[problem_type]
    export_html += f"""
    <div class="section">📋 {s_data['title']}</div>
    <div><b>Применимый стандарт:</b> {s_data['regulations']['standard']}</div>
    <div class="info-box"><b>Базовый регламент:</b> {s_data['regulations']['rule']}</div>
    
    <div class="section">1. Регламент первоочередных действий на роторе:</div>
    """
    for step in s_data["mandatory_steps"]:
        export_html += f'<div class="step">{step}</div>'
        
    export_html += f"""
    <div class="section">2. Физика процесса и сопутствующие риски:</div>
    <div><b>Физический эффект:</b> <i>{s_data['physics']['effect']}</i></div>
    <div class="section">3. Требования Заказчика (ЛНД проекта):</div>
    <div>{s_data['clients'].get(selected_client, s_data['clients']['default'])}</div>
    """

export_html += """
    <div class="footer">
        <b>Разработчик модуля:</b> Старший инженер по качеству Никонова-Морозова М.М. • СТО ИНТИ © 2026
    </div>
</body>
</html>
"""

# Кнопка для скачивания готового документа
st.download_button(
    label="💾 Скачать готовый рапорт для печати",
    data=export_html,
    file_name=f"Tech_Card_{well_number.replace(' ', '_')}.html",
    mime="text/html",
    key="download_report_btn"
)

# ==============================================================================
# ЛОГИКА ТЕХНОЛОГИЧЕСКИХ СЦЕНАРИЕВ И ВЫВОД ПРЕДПРОСМОТРА
# ==============================================================================
# Проверим наличие инцидента в базе знаний
if problem_type in tech_knowledge_base:
    scenario_data = tech_knowledge_base[problem_type]
    
    # === ЗОНА ПЕЧАТИ 1: Шапка и первоочередной регламент ===
    st.markdown('<div class="print-preview">', unsafe_allow_html=True)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.write(f"**Месторождение:** {field_name}")
        st.write(f"**Скважина / Куст:** {well_number}")
    with col_b2:
        st.write(f"**Проект (Заказчик):** {selected_client}")
        st.write(f"**Инженер по ННБ:** {engineer_name}")
    st.markdown("---")
    
    # Выводим заголовок акта и стандарт из JSON
    st.markdown(f"### {scenario_data['title']}")
    st.markdown(f"**Применимый стандарт:** `{scenario_data['regulations']['standard']}`")
    st.info(scenario_data['regulations']['rule'])
    st.markdown("---")
    
    # Выводим пошаговые действия
    st.markdown("#### 1. Регламент первоочередных действий на роторе:")
    for step in scenario_data["mandatory_steps"]:
        st.write(step)
    st.markdown("---")
    st.markdown('</div>', unsafe_allow_html=True)
    # === КОНЕЦ ЗОНЫ ПЕЧАТИ 1 ===

    # ТЕХНОЛОГИЧЕСКИЙ МАРШРУТ (Остается на экране, не идет на печать)
    st.markdown("#### 2. Маршрут верификации параметров:")
    nodes = scenario_data.get("interactive_nodes", {})
    
    if "Опрессовка" in problem_type:
        p_opts = [nodes.get("pumps_normal", "Штатно"), nodes.get("pumps_fail", "Сбой")]
        pumps_state = st.radio("⚙ Режим работы насосов:", p_opts, key="p_opt")
        if pumps_state == p_opts[1]:
            st.error("🚨 ЗАФИКСИРОВАНА ОСТАНОВКА ТЕСТА")
            
        d_opts = [nodes.get("inspection_pass", "Норма"), nodes.get("inspection_fail", "Брак")]
        damage_state = st.radio("📐 Результат дефектоскопии:", d_opts, key="d_opt")
        if damage_state == d_opts[1]:
            st.error("🚨 МАРШРУТ ОТБРАКОВКИ ИНСТРУМЕНТА")
            
        elif "смазки" in problem_type.lower():
        l_opts = [nodes.get("lub_standard", "Стандарт"), nodes.get("lub_special", "Специальная")]
        lubricant_type = st.radio("🔩 Тип применяемой резьбовой смазки (СТО ИНТИ S.QS.7):", l_opts, key="l_opt")
        
        st.markdown("##### 🧮 Расчет момента затяжки для гидроключа УМК:")
        
        # Простой, понятный и изолированный ввод базового момента
        nominal_torque = st.number_input(
            "Введите номинальный момент свинчивания по паспорту резьбы КНБК (кН·м):", 
            min_value=0.0, 
            value=15.0, 
            step=0.5
        )
        
        # Математика трибологии ЛНД: расчет снижения на безметалловой смазке
        if lubricant_type == l_opts[1]:
            st.error("🚨 ВЕТКА Б: КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ КРУТЯЩЕГО МОМЕНТА (БЕЗМЕТАЛЛОВАЯ СМАЗКА)")
            corrected_torque = round(nominal_torque * 0.875, 2)
            st.write(f"⚠️ **Внимание инженера:** Из-за сверхнизкого коэффициента трения безметалловой смазки крутящий момент затяжки на гидроключе снижен до: **`{corrected_torque} кН·м`** (минус 12.5% от номинала).")
        else:
            st.success(f"✅ Финальную затяжку КНБК проводить стандартным номинальным моментом: **`{nominal_torque} кН·м`**")
            
    st.markdown("---")

    # === ЗОНА ПЕЧАТИ 2: Физика процесса и ЛНД Заказчика ===
    st.markdown('<div class="print-preview">', unsafe_allow_html=True)
    st.markdown("#### 3. Физика процесса и сопутствующие риски:")
    st.write(f"**Физический эффект:** *{scenario_data['physics']['effect']}*")
    st.write(scenario_data["physics"]["description"])
    st.markdown("---")
    
    st.markdown("#### 4. Ограничения Заказчика (ЛНД проекта):")
    client_rules = scenario_data.get("clients", {})
    if selected_client in client_rules:
        client_text = client_rules[selected_client]
        if "ЗАПРЕТ" in client_text or "КРИТИЧЕСКОЕ" in client_text:
            st.error(client_text)
        else:
            st.warning(client_text)
    else:
        st.info(client_rules.get("default", "Действуют стандартные правила ИНТИ."))
        
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 30px;'><b>Разработчик цифрового модуля:</b> Старший инженер по качеству Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ © 2026</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    # === КОНЕЦ ЗОНЫ ПЕЧАТИ 2 ===

else:
    st.error("🚨 КРИТИЧЕСКАЯ ОШИБКА: Сценарий не найден в конфигурационном файле JSON.")

