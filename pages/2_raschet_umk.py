import streamlit as st
import numpy as np
import pandas as pd
import json
import os

# =========================================================================
# БЛОК 0 — АВТЕНТИФИКАЦИЯ И СЛУЖЕБНЫЕ НАСТРОЙКИ СТРАНИЦЫ
# =========================================================================
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Авторизуйтесь на Главной странице.")
    st.stop()

st.set_page_config(page_title="Расчет ключа УМК", layout="wide")
st.title("🔧 Контроль момента свинчивания и калибровки ключей УМК")

# =========================================================================
# БЛОК 1 — ИНИЦИАЛИЗАЦИЯ И ПАСПОРТ ВЕРИФИКАЦИИ СТО ИНТИ
# Функционал: Защита резьбовых соединений от промывов и перекрутов,
# трибологическая верификация по стандартам СТО ИНТИ S.QS.7 и S.QS.8.
# =========================================================================
with st.expander("🔰 Паспорт верификации СТО ИНТИ (Момент свинчивания)", expanded=False):
    st.markdown(
        "<div style='font-family: Arial, sans-serif; font-size: 13px; color: #374151; line-height: 1.5;'> "
        "<b>1. СТО ИНТИ S.QS.7 (Раздел 4.2):</b> Контроль надежности элементов бурильной колонны. "
        "Расчет минимизирует риски возникновения промывов замковой резьбы и обрывов труб из-за усталостных напряжений.<br>"
        "<b>2. СТО ИНТИ S.QS.8 (Раздел 6.1.4):</b> Метрологическое обеспечение затяжки резьбовых соединений. "
        "Математическая модель учитывает поправку на угол натяжения каната (утерю плеча рычага) и "
        "трибологические свойства применяемых резьбовых смазок (мультипликатор трения K_смазки)."
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("---")

# =========================================================================
# МОДУЛЬ РАСШИРЕНИЯ БАЗЫ КЛЮЧЕЙ (ДИНАМИЧЕСКИЙ РЕЕСТР ПЛАТФОРМЫ)
# =========================================================================
# Путь к файлу базы данных в корне проекта
DB_FILE_PATH = "keys_db.json"

# Базовые модели ключей на случай отсутствия файла
DEFAULT_KEYS = {
    "УМК-10/1 (L = 0.615 м | зажим Ø 89-114 мм)": 0.615,
    "УМК-35 (L = 0.900 м | зажим Ø 114-168 мм)": 0.900,
    "УМК-48 (L = 1.100 м | зажим Ø 146-245 мм)": 1.100,
    "УМК-75 (L = 1.400 м | зажим Ø 168-324 мм)": 1.400,
    "УМК-90 (L = 1.400 м | зажим Ø 168-324 мм)": 1.400,
}

def load_keys():
    """Загрузка базы ключей из JSON-файла"""
    if not os.path.exists(DB_FILE_PATH):
        with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_KEYS, f, ensure_ascii=False, indent=4)
        return DEFAULT_KEYS
    try:
        with open(DB_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_KEYS

def save_key(name, length):
    """Сохранение нового ключа в JSON-файл"""
    current_db = load_keys()
    current_db[name] = length
    with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(current_db, f, ensure_ascii=False, indent=4)

# Чтение актуальной базы при каждой отрисовке страницы
active_keys_db = load_keys()

# Компактный инпут для добавления нестандартного инструмента
with st.expander("➕ Добавить новую/кастомную модель ключа УМК в базу"):
    c_add1, c_add2 = st.columns(2)
    with c_add1:
        new_key_name = st.text_input("Название/Маркировка ключа:", value="УМК-50 Модернизированный")
    with c_add2:
        new_key_length = st.number_input("Длина плеча по паспорту (L), м:", min_value=0.1, max_value=3.0, value=1.15, step=0.01)
    
    if st.button("💾 Зарегистрировать инструмент в реестре"):
        if new_key_name and new_key_name not in active_keys_db:
            save_key(new_key_name, new_key_length)
            st.success(f"✅ Инструмент '{new_key_name}' успешно внесен в JSON-базу данных.")
            # Перерисовываем страницу, чтобы данные обновились в selectbox
            st.rerun()

# =========================================================================
# БЛОК 2 — ИНФОРМАЦИОННАЯ ШИНА И БАЗЫ ДАННЫХ (СМАЗКИ И СТАЛИ ПО API/ГОСТ)
# Функционал: Замена сайдбара на вкладки, интеграция справочников трибологии.
# =========================================================================

# --- 2.1. Пассивная шторка метаданных ---
with st.sidebar:
    st.markdown("### 📋 Паспорт рейса")
    well_number = st.text_input("Номер скважины / Куст:", value=st.session_state.get("well_name", "Скв. № 101, Куст 5"))
    field_name = st.text_input("Месторождение:", value="Приобское")
    knbk_number = st.text_input("Сборка КНБК №:", value="1")
    st.markdown("---")
    st.caption(f"📍 Недропользователь: {st.session_state.get('main_page_company', 'Роснефть')}")

# --- 2.2. Развертывание центральных вкладок ---
st.markdown("### 🛠 Входные параметры крепления резьбовых соединений")
tab_tongs, tab_pipe, tab_tribology = st.tabs(["🔧 Ключ УМК", "🛢 Параметры трубы и замка", "🧴 Смазка и Трибология"])

# Вкладка 1: Конфигурация рычажной системы ключа УМК
# Вместо старого st.session_state.keys_db.keys() пишем:
   # Вкладка 1: Конфигурация рычажной системы ключа УМК
with tab_tongs:
    # Вместо старого st.session_state.keys_db.keys() пишем:
    menu_options = list(active_keys_db.keys())
    selected_key = st.selectbox("Выберите модель ключа УМК:", menu_options)
    passport_length = active_keys_db[selected_key]
    
    # Новый переключатель типа измерения
    control_type = st.radio(
        "Тип контроля момента на буровой:",
        ["🪢 Электронный (натяжение троса ИВЭ-50)", "💧 Гидравлический (встроенный манометр ключа)"]
    )
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        fact_l = st.number_input("Фактическая длина плеча рычага (Lфакт), м:", min_value=0.1, max_value=3.0, value=passport_length, step=0.005)
    with col_t2:
        if "Электронный" in control_type:
            tros_d = st.number_input("Толщина натяжного троса, мм:", min_value=0.0, max_value=50.0, value=16.0, step=1.0)
        else:
            # Для гидравлики нужен паспортный коэффициент пересчета (кН·м / МПа)
            k_hydr = st.number_input("Коэффициент пересчета ключа (кН·м на 1 МПа) по паспорту:", min_value=0.1, max_value=20.0, value=5.25, step=0.05, help="Показывает, сколько кН·м момента выдает ключ при давлении 1 МПа.")

# Вкладка 2: Прочностные характеристики резьбового соединения труб
with tab_pipe:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        pipe_steel_group = st.selectbox("Группа прочности стали бурильной трубы (ГОСТ/API):", ["Д (Предел текучести 373 МПа)", "К (Предел текучести 490 МПа)", "Е (Предел текучести 539 МПа)", "Л (Предел текучести 637 МПа)", "М (Предел текучести 735 МПа)"])
    with col_p2:
        p_moment = st.number_input("Номинальный крутящий момент резьбы по паспорту, кН·м:", min_value=0.0, max_value=150.0, value=25.0, step=0.5)

# Вкладка 3: Трибология резьбы и поправочные коэффициенты смазок по API
with tab_tribology:
    grease_type = st.selectbox(
        "Применяемая резьбовая уплотнительная смазка:",
        [
            "Стандартная свинцово-цинковая смазка (API Bulleproof / Резьбол, K_смазки = 1.0)",
            "Графитовая резьбовая смазка (Повышенное трение, K_смазки = 1.15)",
            "Тефлоновая/полимерная смазка (Сниженное трение, K_смазки = 0.85)",
            "Дешевая отработка / Смесь без присадок (Критический разброс, K_смазки = 1.30)"
        ]
    )
    
    # Назначение трибологического мультипликатора
    if "Стандартная" in grease_type: k_grease = 1.0
    elif "Графитовая" in grease_type: k_grease = 1.15
    elif "Тефлоновая" in grease_type: k_grease = 0.85
    else: k_grease = 1.30
    
    angle_alpha = st.number_input("Измеренный угол натяжения троса лебедки (α), град:", min_value=10.0, max_value=90.0, value=90.0, step=1.0)
# =========================================================================
# БЛОК 3 — ОБНОВЛЕННОЕ ФИЗИКО-МАТЕМАТИЧЕСКОЕ ЯДРО
# =========================================================================
st.markdown("---")
st.markdown("### 📊 Блок 3: Предиктивный расчет параметров свинчивания")

L_effective = fact_l  
M_required = p_moment * k_grease
g_const = 9.80665

# Разделение логики расчета под старый и новый типы ключей
if "Электронный" in control_type:
    alpha_rad = np.radians(angle_alpha)
    sin_alpha = np.sin(alpha_rad)
    if sin_alpha < 0.1736:
        sin_alpha = 0.1736
        st.error("🚨 КРИТИЧЕСКИЙ УГОЛ: Угол менее 10°! Риск обрыва каната.")
    
    f_pull_newtons = (M_required * 1000.0) / (L_effective * sin_alpha)
    f_pull_tons = f_pull_newtons / g_const
    target_unit = f"{f_pull_tons:.2f} т"
    label_text = "🎯 Целевое усилие натяжения на ИВЭ-50:"
else:
    # Расчет давления для гидравлического манометра
    p_target_mpa = M_required / k_hydr
    # Переводим в атмосферы/атм (кгс/см²) для старых советских манометров
    p_target_atm = p_target_mpa * 10.1972
    target_unit = f"{p_target_mpa:.1f} МПа ({p_target_atm:.1f} кгс/см²)"
    label_text = "🎯 Целевое давление по манометру гидросистемы:"

# Визуализация результатов
col_res1, col_res2 = st.columns(2)
with col_res1:
    st.metric(label=label_text, value=target_unit)
with col_res2:
    st.metric(label="⚙️ Скорректированный крутящий момент:", value=f"{M_required:.2f} кН·м")

# =========================================================================
# БЛОК 4 — МОДУЛЬ КОМПЛЕКСНОЙ ОНЛАЙН-ВАЛИДАЦИИ И СТРЕСС-ТЕСТИРОВАНИЯ РИСКОВ
# =========================================================================
# --- БЛОК 4: ПОЛНОЕ ИНЖЕНЕРНОЕ СТРЕСС-ТЕСТИРОВАНИЕ РИСКОВ ---
with st.expander("🛠️ Модуль комплексной валидации рисков (СТО ИНТИ)", expanded=True):
    has_umk_error = False
    
    # 1. Защита приводного элемента (Трос / Гидравлика)
    if "Электронный" in control_type:
        safe_cable_load = (0.06 * (tros_d ** 2)) / 3.0
        if f_pull_tons > safe_cable_load:
            st.error(f"❌ РИСК ОБРЫВА: Натяжение {f_pull_tons:.2f}т > лимита {safe_cable_load:.2f}т!")
            has_umk_error = True
        else:
            st.success(f"✅ КАНАТ: Нагрузка в допуске ({f_pull_tons:.2f} т).")
    else:
        if p_target_mpa > 20.0:
            st.error(f"❌ РИСК РАЗРЫВА РВД: Давление {p_target_mpa:.1f} МПа > предела 20.0 МПа!")
            has_umk_error = True
        elif p_target_mpa > 17.0:
            st.warning(f"🚨 ПРЕДУПРЕЖДЕНИЕ: Давление {p_target_mpa:.1f} МПа близко к критическому!")
        else:
            st.success(f"✅ ГИДРАВЛИКА: Давление {p_target_mpa:.1f} МПа безопасно.")

    # 2. Контроль износа геометрии рычага УМК
    if fact_l < (passport_length * 0.95):
        st.warning(f"🚨 ГЕОМЕТРИЯ: Плечо ключа изношено более чем на 5% ({fact_l} м)!")
        has_umk_error = True
    else:
        st.success("✅ ГЕОМЕТРИЯ: Длина плеча соответствует допускам.")

    # 3. Контроль предела текучести стали (Защита резьбы от смятия)
    steel_limits = {"Д ": 35.0, "К ": 45.0, "Е ": 55.0, "Л ": 70.0, "М ": 90.0}
    allowed_m = next((lim for gr, lim in steel_limits.items() if gr in pipe_steel_group), 999.0)
    
    if p_moment > allowed_m:
        st.error(f"❌ СМЯТИЕ РЕЗЬБЫ: Момент {p_moment} кН·м выше предела текучести стали {pipe_steel_group[:2]} ({allowed_m} кН·м)!")
        has_umk_error = True
    else:
        st.success(f"✅ МАТЕРИАЛ: Группа прочности {pipe_steel_group[:2]} выдержит нагрузку.")

# =========================================================================
# БЛОК 5 — АДАПТИВНЫЙ НАРЯД-ДОПУСК ---
# =========================================================================
АДАПТИВНЫЙ НАРЯД-ДОПУСК ---
st.markdown("---")
st.subheader("📋 Блок 5: Распоряжение")

# Динамическая строка параметров
if "Электронный" in control_type:
    control_line = f"**ЦЕЛЕВОЕ УСИЛИЕ:** {f_pull_tons:.2f} т\n**Угол:** {angle_alpha}°"
else:
    control_line = f"**ДАВЛЕНИЕ:** {p_target_mpa:.1f} МПа"

work_order_text = f"""# РАСПОРЯЖЕНИЕ НА СВИНЧИВАНИЕ
**Скважина:** {well_number} | **Скорректированный момент:** {M_required:.2f} кН·м
{control_line}
---
**Статус СТО ИНТИ:** {"ОШИБКА" if has_umk_error else "БЕЗОПАСНО"}
"""

with st.container(border=True):
    st.markdown(work_order_text)

st.download_button(
    "📥 Скачать .md",
    work_order_text,
    file_name=f"Order_{well_number}.md",
    disabled=has_umk_error
)
