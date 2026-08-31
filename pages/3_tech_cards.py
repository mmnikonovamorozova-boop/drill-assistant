import streamlit as st

# Проверка авторизации инженера
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Выполните авторизацию.")
    st.stop()

st.set_page_config(page_title="Технологические карты КНБК", page_icon="🔧", layout="wide")
st.title("🔩 Интерактивные технологические карты сборки КНБК")
st.caption("Полевой контроль технологической дисциплины и верификация СМК")

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

# Экспорт в PDF / Печать
if st.button("🖨 Распечатать сценарий (Ctrl + P)"):
    st.components.v1.html("<script>window.print();</script>", height=0, width=0)

st.markdown("---")

# ==============================================================================
# ЛОГИКА ТЕХНОЛОГИЧЕСКИХ СЦЕНАРИЕВ И ВЫВОД ПРЕДПРОСМОТРА
# ==============================================================================
st.subheader("📄 ГОТОВЫЙ БЛАНК ДЛЯ ПЕЧАТИ (ТЕХНОЛОГИЧЕСКАЯ КАРТА ИНЦИДЕНТА)")

# Формируем визуальную рамку А4 без создания блоков вложенности в коде
st.markdown('<div class="print-preview">', unsafe_allow_html=True)

col_b1, col_b2 = st.columns(2)
with col_b1:
    st.write(f"**Месторождение:** {field_name}")
    st.write(f"**Скважина / Куст:** {well_number}")
with col_b2:
    st.write(f"**Проект (Заказчик):** {selected_client}")
    st.write(f"**Инженер по ННБ:** {engineer_name}")

st.markdown("---")

# Проверяем, что выбранный инцидент есть в нашей JSON базе знаний
if problem_type in tech_knowledge_base:
    scenario_data = tech_knowledge_base[problem_type]
    
    st.subheader("📄 ГОТОВЫЙ БЛАНК ДЛЯ ПЕЧАТИ (ТЕХНОЛОГИЧЕСКАЯ КАРТА ИНЦИДЕНТА)")
    
    # Открываем визуальную рамку для печати
    st.markdown('<div class="print-preview">', unsafe_allow_html=True)
    
    # Выводим метаданные рапорта в две колонки
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.write(f"**Месторождение:** {field_name}")
        st.write(f"**Скважина / Куст:** {well_number}")
    with col_b2:
        st.write(f"**Проект (Заказчик):** {selected_client}")
        st.write(f"**Инженер по ННБ:** {engineer_name}")
    st.markdown("---")
    # Выводим динамический заголовок акта и стандарт из JSON
    st.markdown(f"### {scenario_data['title']}")
    st.markdown(f"**Применимый стандарт:** `{scenario_data['regulations']['standard']}`")
    st.info(scenario_data['regulations']['rule'])
    st.markdown("---")
    
    # Выводим пошаговый базовый регламент действий на роторе
    st.markdown("#### 1. Регламент первоочередных действий на роторе:")
    for step in scenario_data["mandatory_steps"]:
        st.write(step)
    st.markdown("---")
    st.markdown("#### 2. Технологический маршрут верификации параметров:")
    nodes = scenario_data.get("interactive_nodes", {})
    
    # Развилка для сценария ОПРЕССОВКИ
    if "Опрессовка" in problem_type:
        pumps_state = st.radio(
            "⚙ Режим работы буровых насосов (СТО ИНТИ S.QS.8):",
            [nodes.get("pumps_normal"), nodes.get("pumps_fail")],
            key="pumps_opt"
        )
        if "СБОЙ" in pumps_state:
            st.error("🚨 ЗАФИКСИРОВАНА ОСТАНОВКА ТЕСТА: Давление не наведено наземным комплексом буровой.")
            
        damage_state = st.radio(
            "📐 Результат дефектоскопии и ВИК резьбового соединения (СТО ИНТИ S.30.13):",
            [nodes.get("inspection_pass"), nodes.get("inspection_fail")],
            key="damage_opt"
        )
        if "Брак" in damage_state:
            st.error("🚨 МАРШРУТ ОТБРАКОВКИ И ОСТАНОВКИ ИНСТРУМЕНТА")

    # Развилка для сценария СМАЗКИ
    elif "смазки" in problem_type.lower():
        lubricant_type = st.radio(
            "🔩 Тип применяемой резьбовой смазки (СТО ИНТИ S.QS.7):",
            [nodes.get("lub_standard"), nodes.get("lub_special")],
            key="lub_opt"
        )
        if "снижения" in lubricant_type:
            st.error("🚨 ВЕТКА Б: КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ КРУТЯЩЕГО МОМЕНТА")
            
    st.markdown("---")
    # Выводим физические законы и риски инцидента из JSON
    st.markdown("#### 3. Физика процесса и сопутствующие риски:")
    st.write(f"**Физический эффект:** *{scenario_data['physics']['effect']}*")
    st.write(scenario_data["physics"]["description"])
    st.markdown("---")
    
    # Динамический контроль требований Заказчика
    st.markdown("#### 4. Ограничения Заказчика (ЛНД проекта):")
    client_rules = scenario_data.get("clients", {})
    
    if selected_client in client_rules:
        client_text = client_rules[selected_client]
        # Если в тексте есть жесткие стоп-слова, подсвечиваем красным, иначе — желтым
        if "ЗАПРЕТ" in client_text or "КРИТИЧЕСКОЕ" in client_text:
            st.error(client_text)
        else:
            st.warning(client_text)
    else:
        # Если для этого заказчика нет особых ЛНД, выводим дефолтное правило
        st.info(client_rules.get("default", "Элемент признан несоответствующим требованиям стандарта ИНТИ."))
    st.markdown("---")
    st.info("💡 **Инструкция по фиксации акта:** Нажмите комбинацию клавиш **`Ctrl + P`**... [полный код элемента управления доступен в исходных материалах]")
    
    # Подвал бланка с копирайтом и разработчиком
    st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 30px;'><b>Разработчик цифрового модуля:</b> Старший инженер по качеству Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ © 2026</div>", unsafe_allow_html=True)
    
    # Закрываем HTML-тег рамки печати
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Защитный блок на случай, если сценария нет в базе tech_requirements.json
    st.error("🚨 КРИТИЧЕСКАЯ ОШИБКА БАЗЫ ЗНАНИЙ: Выбранный технологический сценарий не найден в конфигурационном файле JSON.")

