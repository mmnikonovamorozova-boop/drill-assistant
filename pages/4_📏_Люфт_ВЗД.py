import streamlit as st
from datetime import datetime

# --- 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="Калькулятор люфта ВЗД", layout="wide")

st.title("📏 Комплексный расчет износа и люфтов шпинделя ВЗД")
st.caption("МЕТОДИКА КОНТРОЛЯ ИЗНОСА ОПОР ШПИНДЕЛЯ ПО РЕГЛАМЕНТАМ ПОСТАВЩИКОВ И ЗАКАЗЧИКОВ")
st.markdown("---")

# Сдержанная техническая отметка о соответствии стандартам ИНТИ (адаптированная под ВЗД)
st.markdown(
    "<div style='color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #1E3A8A; margin-bottom: 20px; line-height: 1.5; font-family: Arial, sans-serif;'>"
    "<b>Верификация стандартов:</b> Данный модуль контроля осевого и radialьного износа шпиндельной секции ВЗД разработан в строгом соответствии с требованиями отраслевых стандартов "
    "<b>СТО ИНТИ S.QS.7 (п. 7.4.3 «Верификация закупаемой продукции», п. 7.5.1 «Управление производством и предоставлением услуг»)</b> в части проведения обязательной входной инспекции, проверки критических параметров и оценки соответствия забойных двигателей критериям безопасной эксплуатации на устье, "
    "а также <b>СТО ИНТИ S.QS.8 (п. 5.7.2 «Управление оборудованием для мониторинга и измерений»)</b> в части обязательного контроля исправности и метрологического подтверждения применяемого мерительного充 инструмента (индикаторов часового типа ИЧ, нутромеров) на буровой площадке."
    "</div>", 
    unsafe_allow_html=True
)

# --- 2. СБОР МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")
vzd_passport_number = st.sidebar.text_input("Серийный номер ВЗД по паспорту:", value="№ 6677")
selected_client = st.sidebar.selectbox("Заказчик (Недропользователь):", ["ПАО Роснефть", "ПАО Газпром", "ПАО Лукойл", "🔄 Без учета ограничений Заказчика"])

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
report_text = ""

# Инициализация локальной пользовательской базы в сессии
if "custom_vzd" not in st.session_state:
    st.session_state.custom_vzd = {}

# --- 3. НОРМАТИВНЫЕ БАЗЫ ДАННЫХ ---
# Внутренние лимиты крупных Заказчиков (распределены по габаритным группам)
client_limits_db = {
    "ПАО Роснефть": {"малый": {"axial": 3.5, "radial": 1.0}, "средний": {"axial": 4.0, "radial": 1.2}, "большой": {"axial": 5.0, "radial": 1.5}},
    "ПАО Газпром": {"малый": {"axial": 4.0, "radial": 1.2}, "средний": {"axial": 4.5, "radial": 1.5}, "большой": {"axial": 5.0, "radial": 2.0}},
    "ПАО Лукойл": {"малый": {"axial": 4.0, "radial": 1.2}, "средний": {"axial": 5.0, "radial": 1.6}, "большой": {"axial": 5.5, "radial": 2.2}}
}

# Оригинальная встроенная база данных ВЗД
base_vzd = {
    "Радиус-Сервис": {
        "43 мм": 6.0, "54 мм": 6.0, "73 мм": 6.0, "75 мм": 6.0, 
        "95 мм": 8.0, "98 мм": 8.0, "106 мм": 8.0, "120 мм": 8.0, "127 мм": 8.0,
        "165 мм": 10.0, "172 мм": 10.0, "195 мм": 10.0, "210 мм": 10.0, "240 мм": 10.0
    },
    "Гидробур-Сервис": {
        "95 мм": 1.0, "106 мм": 1.0, "120 мм": 1.0, "178 мм": 1.0, "210 мм": 1.0, "240 мм": 1.0
    },
    "NOV": {
        "5'' (Лимит: 5/16'')": 7.94, 
        "6-1/2'' (Лимит: 7/16'')": 11.11, 
        "7'' (Лимит: 7/16'')": 11.11, 
        "8'' (Лимит: 1/2'')": 12.70, 
        "9-5/8'' (Лимит: 11/16'')": 17.46
    },
    "НГТ": {
        "ДР-120.NGT.7/8.43.20.M2": 8.0, "ДР-120.NGT.7/8.59.M2 ТС": 8.0,
        "ДР-165.NGT.7/8.45.38.M1": 9.0, "ДР-178.NGT.7/8.61.45.M25": 9.0,
        "ДР-210.NGT.7/8.60.60.M2": 10.0, "ДР-240.NGT.3/4.62.70.M1": 11.0
    },
    "ВНИИБТ": {
        "Д-43 / 2Д-43 / 2Д-43-01": 1.5, "Д1-43": 2.0, "Д1-55": 3.0,
        "Д-73 / ДР-73 / Д-76М": 3.0, "ДР-73С / ДР-73ОПН": 3.5, "Д-88 / ДР-88": 4.0,
        "ДВ-95 / Д-106 / Д-106ПН / Д3-106МР / ДР3-106МР": 3.0,
        "ДР3-95М / ДР4-95С / ДР5-95С / ДР5-106 / Д1-105 / Д3-106М / ДР3-106М / ДР3-106ТС / ДР4-106 / ДР3-120 / ДР3-120Н / ДР3-120С / ДГР-120ТСЭ / Д3-127М / ДР3-127М": 5.0,
        "ДГР-165 / ДГР-172 / ДГР-172С / ДГР1-172 / ДГР3-172 / ДГР-178М / ДР-178М / ДГР-195М / ДГР-195С / ДГР-240М / ДР1-240М": 6.0,
        "ДГР3-172Н / SM700 / SM.H700 / ДГР-210 / ДГР1-240": 10.0
    }
}

brands_list = list(base_vzd.keys()) + ["➕ НОВЫЙ ПОСТАВЩИК / МОДЕЛЬ"]
selected_brand = st.selectbox("1. Выберите производителя оборудования ВЗД:", brands_list)

limit_wear = 0.0
limit_radial_wear = 1.5  # Базовый дефолтный предел радиального люфта
vzd_model_name = ""
size_group = "средний"   # По умолчанию

# --- 4. ЛОГИКА ДЛЯ АМЕРИКАНСКИХ ВЗД (NOV) ---
if selected_brand == "NOV":
    st.warning("🇺🇸 ВЗД Американского производства (NOV). Паспортные лимиты автоматически пересчитаны в метрическую систему до сотых долей.")
    st.markdown("**🔄 Промысловый конвертер долей дюйма (выберите значения из паспорта):**")
    
    col_num, col_den = st.columns(2)
    with col_num:
        numerator = st.selectbox("Числитель дроби:", [1, 3, 5, 7, 9, 11, 13, 15], index=3)
    with col_den:
        denominator = st.selectbox("Знаменатель дроби:", [2, 4, 8, 16], index=3)
        
    mm_result = (numerator / denominator) * 25.4
    st.success(f"📐 Результат перевода доли **{numerator}/{denominator}''** в метрическую систему: **{mm_result:.2f} мм**")
    st.markdown("---")

# --- 5. ОБРАБОТКА ДОБАВЛЕНИЯ НОВОГО ОБОРУДОВАНИЯ ---
if selected_brand == "➕ НОВЫЙ ПОСТАВЩИК / МОДЕЛЬ":
    st.success("🛠️ Окно добавления нового оборудования в локальную базу данных:")
    custom_brand = st.text_input("Введите название завода/поставщика:", value="Буринтех")
    custom_model = st.text_input("Введите габарит или шифр серии двигателя (например, 172ТС):", value="172 мм")
    custom_limit = st.number_input("Установите предельный осевой люфт по паспорту (мм):", min_value=0.0, max_value=25.0, value=5.5, step=0.1)
    custom_radial_limit = st.number_input("Установите предельный радиальный люфт по паспорту (мм):", min_value=0.0, max_value=10.0, value=1.5, step=0.1)
    custom_group = st.selectbox("Укажите категорию габарита для привязки норм Заказчиков:", ["малый", "средний", "большой"], index=1)
    
    if st.button("💾 Сохранить и внести двигатель в реестр"):
        if custom_brand and custom_model:
            if custom_brand not in st.session_state.custom_vzd:
                st.session_state.custom_vzd[custom_brand] = {}
            st.session_state.custom_vzd[custom_brand][custom_model] = {
                "axial": custom_limit, 
                "radial": custom_radial_limit, 
                "group": custom_group
            }
            st.toast(f"Двигатель {custom_brand} {custom_model} успешно добавлен в списки!", icon="✔️")
            
    vzd_model_name = custom_brand + " " + custom_model
    limit_wear = custom_limit
    limit_radial_wear = custom_radial_limit
    size_group = custom_group

else:
    current_brand_models = base_vzd[selected_brand].copy()
    if selected_brand in st.session_state.custom_vzd:
        current_brand_models.update(st.session_state.custom_vzd[selected_brand])
        
    selected_diameter = st.selectbox("2. Выберите габарит / шифр модели:", list(current_brand_models.keys()))
    vzd_model_name = selected_brand + " " + selected_diameter
    
    # Извлечение данных из реестра (проверка типа данных для кастомных моделей)
    if isinstance(current_brand_models[selected_diameter], dict):
        limit_wear = current_brand_models[selected_diameter]["axial"]
        limit_radial_wear = current_brand_models[selected_diameter]["radial"]
        size_group = current_brand_models[selected_diameter]["group"]
    else:
        limit_wear = current_brand_models[selected_diameter]
        # Парсинг группы из текста для оригинальной базы
        small_markers = ["43", "54", "73", "75", "88", "95", "98", "106", "5''"]
        large_markers = ["195", "210", "240", "8''", "9-5/8''"]
        if any(m in selected_diameter for m in small_markers):
            size_group = "малый"
            limit_radial_wear = 1.0
        elif any(m in selected_diameter for m in large_markers):
            size_group = "большой"
            limit_radial_wear = 2.0
        else:
            size_group = "средний"
            limit_radial_wear = 1.5

# Динамический расчет номинала (зеленая зона приемки на устье)
limit_nominal = limit_wear * 0.35

# --- 6. АЛГОРИТМ СРАВНЕНИЯ И СВЕРКИ С ЗАКАЗЧИКАМИ ---
if selected_client in client_limits_db:
    client_rules = client_limits_db[selected_client][size_group]
    effective_max_axial = min(limit_wear, client_rules["axial"])
    effective_max_radial = min(limit_radial_wear, client_rules["radial"])
    st.info(f"ℹ️ **Нормы контроля:** Паспорт завода = {limit_wear:.2f} мм | Ограничение {selected_client} = {client_rules['axial']:.2f} мм")
    st.warning(f"🎯 **Целевой критерий отбраковки на устье:** Осевой до **{effective_max_axial:.2f} мм** | Радиальный до **{effective_max_radial:.2f} мм**")
else:
    effective_max_axial = limit_wear
    effective_max_radial = limit_radial_wear
    st.info(f"🎯 **Целевой критерий отбраковки (Паспортный):** Осевой до **{effective_max_axial:.2f} мм** | Радиальный до **{effective_max_radial:.2f} мм**")

# --- 7. ВВОД ФАКТИЧЕСКИХ ЗАМЕРОВ ---
st.markdown("---")
st.subheader("📥 3. Фактические замеры на устье скважины")
col_input1, col_input2 = st.columns(2)

with col_input1:
    size_a = st.number_input("Размер 'А' (шпиндель максимально выдвинут), мм:", min_value=0.0, max_value=50.0, value=10.0, step=0.01)
    size_b = st.number_input("Размер 'Б' (шпиндель максимально разгружен), мм:", min_value=0.0, max_value=50.0, value=5.5, step=0.01)
    calculated_delta = size_a - size_b

with col_input2:
    measured_radial = st.number_input("Фактический радиальный люфт по индикатору (ИЧ), мм:", min_value=0.0, max_value=15.0, value=0.4, step=0.01)

