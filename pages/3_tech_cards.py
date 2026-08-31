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

        # === ТЕХНОЛОГИЧЕСКИЙ МАРШРУТ (БЕЗ ПЕЧАТИ) ===
    st.markdown("#### 2. Маршрут верификации параметров:")
    nodes = scenario_data.get("interactive_nodes", {})
    
    if problem_type == "Опрессовка: Течь/падение давления в замковом стыке КНБК":
        p_opts = [nodes.get("pumps_normal", "Штатно"), nodes.get("pumps_fail", "Сбой")]
        pumps_state = st.radio("⚙ Режим работы насосов:", p_opts, key="p_opt")
        if pumps_state == p_opts[1]:
            st.error("🚨 ЗАФИКСИРОВАНА ОСТАНОВКА ТЕСТА")
            
        d_opts = [nodes.get("inspection_pass", "Норма"), nodes.get("inspection_fail", "Брак")]
        damage_state = st.radio("📐 Результат дефектоскопии:", d_opts, key="d_opt")
        if damage_state == d_opts[1]:
            st.error("🚨 МАРШРУТ ОТБРАКОВКИ ИНСТРУМЕНТА")
    elif problem_type == "Сборка: Избыточное нанесение резьбовой смазки":
        l_opts = [nodes.get("lub_standard", "Стандарт"), nodes.get("lub_special", "Специальная")]
        lubricant_type = st.radio("🔩 Тип применяемой резьбовой смазки (СТО ИНТИ S.QS.7):", l_opts, key="l_opt")
        
        st.markdown("##### 🧮 Расчет момента затяжки для гидроключа УМК:")
        nominal_torque = st.number_input(
            "Введите номинальный момент свинчивания по паспорту резьбы КНБК (кН·м):",
            min_value=0.0, value=15.0, step=0.5
        )
        
                # Математика трибологии ЛНД: расчет снижения на безметалловой смазке
        if lubricant_type == l_opts[1]:
            st.warning("⚠️ **ВНИМАНИЕ:** Зафиксировано применение специализированной безметалловой смазки.")
            corrected_torque = round(nominal_torque * 0.875, 2)
            
            # Выводим скорректированный момент крупным читаемым шрифтом
            st.markdown(f"""
            <div style="background-color: #fef2f2; padding: 15px; border-radius: 6px; border-left: 5px solid #ef4444; margin-top: 10px;">
                <span style="color: #991b1b; font-size: 14px; font-weight: bold; display: block; margin-bottom: 5px;">🔧 СКОРРЕКТИРОВАННЫЙ МОМЕНТ ДЛЯ КЛЮЧА УМК (СТО ИНТИ S.QS.7):</span>
                <span style="color: #b91c1c; font-size: 28px; font-weight: 900;">{corrected_torque} кН·м</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"✅ Финальную затяжку КНБК проводить стандартным номинальным моментом: **`{nominal_torque} кН·м`**")
            
        st.markdown("---")
        
        # Полный код формирования export_html и кнопки скачивания доступен в исходных материалах [INDEX].
        # Здесь подключается генерация HTML-отчета с данными по скважине, шагам регламента и трибологическому расчету.


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
            
        # === ГЕНЕРАЦИЯ ОТЧЕТА И КНОПКА СКАЧИВАНИЯ ===
        st.markdown("---")
        current_lub = st.session_state.get("l_opt", "Стандарт")
        rep_torque = f"{round(15.0 * 0.875, 2)} кН·м (Снижен на 12.5%)" if "Специальная" in current_lub else "15.0 кН·м (Номинал)"
        # Код сборки HTML-отчета и скачивания через st.sidebar.download_button

    else:
        st.info(client_rules.get("default", "Действуют стандартные правила ИНТИ."))
        
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 30px;'><b>Разработчик цифрового модуля:</b> Старший инженер по качеству Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ © 2026</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    # === КОНЕЦ ЗОНЫ ПЕЧАТИ 2 ===

else:
    st.error("🚨 КРИТИЧЕСКАЯ ОШИБКА: Сценарий не найден в конфигурационном файле JSON.")

