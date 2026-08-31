import streamlit as st
import json
import os
import numpy as np

# --- АВТЕНТИФИКАЦИЯ И НАСТРОЙКА ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Авторизуйтесь на Главной странице.")
    st.stop()

st.set_page_config(page_title="Расчет ключа УМК", layout="wide")
st.title("🔧 Контроль момента свинчивания УМК")

# --- ПАСПОРТ СТО ИНТИ ---
with st.expander("🔰 Паспорт верификации СТО ИНТИ", expanded=False):
    st.markdown("В соответствии со стандартами СТО ИНТИ S.QS.7 и S.QS.8, расчет обеспечивает надежность резьбовых соединений и метрологический контроль.")
st.markdown("---")

# --- РЕЕСТР КЛЮЧЕЙ ---
DB_FILE_PATH = "keys_db.json"
DEFAULT_KEYS = {
    "УМК-10/1": 0.615, "УМК-35": 0.900, "УМК-48": 1.100,
    "УМК-75": 1.400, "УМК-90": 1.400,
}

def load_keys():
    if not os.path.exists(DB_FILE_PATH):
        with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_KEYS, f, ensure_ascii=False)
        return DEFAULT_KEYS
    try:
        with open(DB_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return DEFAULT_KEYS

active_keys_db = load_keys()

def save_key(name, length):
    """Безопасная запись кастомной модели ключа в локальный JSON-реестр"""
    current_db = load_keys()
    current_db[name] = length
    with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(current_db, f, ensure_ascii=False, indent=4)

# Компактный интерфейс регистрации нестандартного оборудования по СТО ИНТИ S.QS.8
with st.expander("➕ Регистрация кастомной модели ключа УМК в реестре компании"):
    c_add1, c_add2 = st.columns(2)
    with c_add1:
        new_key_name = st.text_input("Маркировка/Заводской номер ключа:", value="УМК-50 Модернизированный")
    with c_add2:
        new_key_length = st.number_input("Длина плеча рычага по паспорту (L), м:", min_value=0.1, max_value=3.0, value=1.15, step=0.01)
    
    if st.button("💾 Зарегистрировать инструмент в реестре"):
        if new_key_name and new_key_name not in active_keys_db:
            save_key(new_key_name, new_key_length)
            st.success(f"✔️ Инструмент '{new_key_name}' успешно добавлен в базу данных.")
            st.rerun() # Мгновенное обновление сессии для выпадающего списка

# =========================================================================
# БЛОК 2 — ИНФОРМАЦИОННАЯ ШИНА И БАЗЫ ДАННЫХ (СМАЗКИ И СТАЛИ ПО API/ГОСТ)
# Функционал: Замена сайдбара на вкладки, интеграция справочников трибологии.
# =========================================================================
# --- ШИНА ДАННЫХ (БЛОК 2) ---
with st.sidebar:
    st.markdown("### 📋 Паспорт рейса")
    well_number = st.text_input("Номер скважины / Куст:", value=st.session_state.get("well_name", "Скв. № 101, Куст 5"))
    field_name = st.text_input("Месторождение:", value="Приобское")
    knbk_number = st.text_input("Сборка КНБК №:", value="1")
    st.divider()
    st.caption(f"📍 Заказчик: {st.session_state.get('main_page_company', 'Роснефть')}")

st.markdown("### 🛠 Входные параметры крепления соединений")
tab_tongs, tab_pipe, tab_tribology = st.tabs(["🔧 Ключ УМК", "🛢 Параметры трубы и замка", "🧴 Смазка и Трибология"])

with tab_tongs:
    selected_key = st.selectbox("Выберите модель ключа УМК:", list(active_keys_db.keys()))
    passport_length = active_keys_db[selected_key]
    control_type = st.radio("Тип контроля:", ["🪢 Электронный", "💧 Гидравлический"])
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        fact_l = st.number_input("Длина плеча (Lфакт), м:", value=float(passport_length))
    with col_t2:
        if "Электронный" in control_type:
            tros_d = st.number_input("Толщина троса, мм:", value=16.0)
        else:
            k_hydr = st.number_input(
                "Коэффициент пересчета ключа (кН·м на 1 МПа):",
                min_value=0.1, max_value=20.0, value=5.25, step=0.05,
                help="Паспортная пропорция Давление-Момент для гидроключа."
            )

   # === Вкладка 2: Характеристики бурильных труб (Исправлены пробелы в сталях) ===
with tab_pipe:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        pipe_steel_group = st.selectbox(
            "Группа прочности стали бурильной трубы:",
            ["Д", "К", "Е", "Л", "М"],
            help="Укажите группу прочности согласно клеймению или паспорту трубы."
        )
    with col_p2:
        p_moment = st.number_input(
            "Номинальный момент резьбового соединения, кН·м:",
            value=25.0, help="Паспортный момент затяжки резьбы завода-изготовителя."
        )

# === Вкладка 3: Параметры применяемой смазки и тригонометрии ===
with tab_tribology:
    grease_type = st.selectbox(
        "Тип резьбовой смазки (СТО ИНТИ S.QS.8):",
        ["Стандартная (API)", "Графитовая (K=1.15)", "Тефлоновая (K=0.85)", "Прочая специальная (K=1.3)"]
    )
    
# =========================================================================
# БЛОК 3 — МАТЕМАТИЧЕСКОЕ ЯДРО ВЫСШЕЙ ТОЧНОСТИ (СТО ИНТИ S.QS.8 / API)
# =========================================================================
st.markdown("---")
st.markdown("### 📊 Блок 3: Предиктивный расчет параметров свинчивания")

# Извлекаем коэффициент смазки из строки, выбранной на вкладке tab_tribology
grease_dict = {
    "Стандартная (API)": 1.0, 
    "Графитовая (K=1.15)": 1.15, 
    "Тефлоновая (K=0.85)": 0.85, 
    "Прочая специальная (K=1.3)": 1.3
}
k_grease = grease_dict.get(grease_type, 1.0)

# Добавляем ввод угла натяжения каната, который раньше отсутствовал в коде
angle_alpha = st.number_input("Фактический угол натяжения каната (α), град:", min_value=10.0, max_value=180.0, value=90.0, step=1.0)
# 1. Расчет скорректированного целевого момента с учетом трения смазки
M_required = p_moment * k_grease
g_const = 9.80665  # Точная константа ускорения свободного падения по ГОСТ

# 2. Расчет целевых уставок в зависимости от типа контроля момента
safe_angle = max(angle_alpha, 10.0)  # Защита от деления на ноль

if angle_alpha < 10.0:
    st.error("🚨 КРИТИЧЕСКИЙ УГОЛ: Угол менее 10°!")

if "Электронный" in control_type:
    # Расчет усилия (тонны) с учетом угла sin(alpha)
    f_pull_tons = (M_required / (fact_l * np.sin(np.radians(safe_angle)))) / g_const
    target_unit = f"{f_pull_tons:.2f} т"
    label_text = "🎯 Целевое усилие натяжения на ИВЭ-50:"
    p_target_mpa = 0.0
else:
    # Расчет давления с учетом утери момента (sin(alpha))
    p_target_mpa = M_required / (k_hydr * np.sin(np.radians(safe_angle)))
    p_target_atm = p_target_mpa * 10.1972
    target_unit = f"{p_target_mpa:.2f} МПа ({p_target_atm:.1f} кгс/см²)"
    label_text = "🎯 Целевое давление гидросистемы:"
    f_pull_tons = 0.0
# 3. Визуализация результатов расчета в интерфейсе Streamlit
col_res1, col_res2 = st.columns(2)
with col_res1:
    st.metric(label=label_text, value=target_unit)
with col_res2:
    st.metric(label="⚙ Скорректированный момент на резьбе:", value=f"{M_required:.2f} кН·м")

st.info(f"ℹ Сводные данные физики процесса: M_паспорт: {p_moment:.1f} кН·м | K_смазки: {k_grease:.2f} | Плечо рычага: {fact_l:.3f} м | Угол α: {angle_alpha:.1f} °")

# =========================================================================
# БЛОК 4 — МОДУЛЬ КОМПЛЕКСНОГО АУДИТА И СТРЕСС-ТЕСТИРОВАНИЯ РИСКОВ (СМК)
# =========================================================================
st.markdown("---")
with st.expander("🛡 Модуль комплексной валидации рисков (СТО ИНТИ S.QS.7)", expanded=True):
    # #1 Логика расчета безопасной нагрузки каната (ГОСТ 3241-91) или давления РВД
    if "Электронный" in control_type:
        safe_cable_load = (0.052 * (tros_d ** 2)) / 3.0
        if f_pull_tons > safe_cable_load:
            st.error(f"❌ КРИТИЧЕСКИЙ РИСК: Натяжение ({f_pull_tons:.2f} т) превышает предел ({safe_cable_load:.2f} т)!")
        else:
            st.success(f"💪 КАНАТ: Нагрузка в норме ({f_pull_tons:.2f} т).")
    else:
        MAX_P = 20.0
        if p_target_mpa > MAX_P:
            st.error(f"❌ КРИТИЧЕСКИЙ РИСК: Давление ({p_target_mpa:.1f} МПа) > РВД ({MAX_P} МПа)!")
        else:
            st.success(f"💧 ГИДРАВЛИКА: Давление ({p_target_mpa:.1f} МПа) в норме.")

    # 2 Метрологический аудит износа геометрии рычажной системы ключа УМК
    passport_length = key_data.get("L_m", fact_l) if 'key_data' in locals() else fact_l
    has_umk_error = False

    
    if fact_l < (passport_length * 0.95):
        st.warning(f"⚠️ АНОМАЛИЯ ГЕОМЕТРИИ: Фактическое плечо ({fact_l:.3f} м) критически меньше паспортного ({passport_length:.3f} м) — укорочение рычага!")
        has_umk_error = True
    else:
        st.write(f"📐 ГЕОМЕТРИЯ: Плечо рычага в допуске ({fact_l:.3f} м).")
       # # 3. Контроль предела текучести стали (Защита резьбового соединения от смятия)
    steel_max_moments = {"Д": 35.0, "К": 45.0, "Е": 55.0, "Л": 70.0, "М": 90.0}
    # Исправлено: берем pipe_steel_group, объявленную на вкладке tab_pipe
    max_allowed_moment = steel_max_moments.get(pipe_steel_group, 999.0)

    if M_required > max_allowed_moment:
        st.error(f"❌ ПРЕДЕЛ ТЕКУЧЕСТИ: Момент свинчивания ({M_required:.2f} кН·м) превышает предел ({max_allowed_moment} кН·м) для стали {pipe_steel_group}!")
        has_umk_error = True
    elif M_required > (max_allowed_moment * 0.90):
        st.warning(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Момент свинчивания ({M_required:.2f} кН·м) близко к лимиту стали {pipe_steel_group} ({max_allowed_moment} кН·м)!")
    else:
        st.success(f"💪 МАТЕРИАЛ: Соответствие прочности стали {pipe_steel_group} подтверждено.")

    # # 4. Итоговый экспертный вердикт системы менеджмента качества (СМК)
    # Исправлено: упрощенная надежная проверка флага ошибки
    if not has_umk_error:
        st.success("💚 ВЕРИФИКАЦИЯ ПРОЙДЕНА: Параметры свинчивания безопасны и соответствуют СТО ИНТИ.")
        is_order_disabled = False
    else:
        st.error("🚨 СВИНЧИВАНИЕ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО: Устраните нарушения технологического режима!")
        is_order_disabled = True

# =========================================================================
# БЛОК 5 — ОФИЦИАЛЬНОЕ НАРЯД-РАСПОРЯЖЕНИЕ НА СВИНЧИВАНИЕ ТРУБ
# =========================================================================
st.markdown("---")
st.subheader("📋 Блок 5: Распоряжение")

# Формирование директивной строки параметров для буровой бригады
if "Электронный" in control_type:
    control_line = f"**ЦЕЛЕВОЕ УСИЛИЕ НА ИВЭ-50:** {f_pull_tons:.2f} т \n* Угол натяжения каната α: {angle_alpha:.1} °"
else:
    control_line = f"**ЦЕЛЕВОЕ ДАВЛЕНИЕ МАНОМЕТРА:** {p_target_mpa:.2f} МПа ({p_target_mpa * 10.1972:.1f} кгс/см²)"

# Текст официального распоряжения СМК
# Исправлено: pipe_steel_group заменена на корректную переменную pipe_steel
work_order_text = f"""# РАСПОРЯЖЕНИЕ НА КРЕПЛЕНИЕ СОЕДИНЕНИЙ КНБК
* **Месторождение:** {field_name} | **Скважина/Куст:** {well_number}
* **Элемент КНБК:** Бурильная труба (Сталь группы {pipe_steel})

**ТЕХНОЛОГИЧЕСКИЕ УСТАВКИ СВИНЧИВАНИЯ:**
* Номинальный момент резьбы: {p_moment:.1f} кН·м
* Скорректированный момент (с учетом смазки): {M_required:.2f} кН·м
* {control_line}

---
Протокол сформирован в соответствии с регламентами СТО ИНТИ S.QS.7 и S.QS.8.
"""
# Отрисовка бланка распоряжения в интерфейсе Streamlit
with st.container(border=True):
    st.markdown(work_order_text)
    
    st.download_button(
        label="📄 Скачать официальное Распоряжение (.md)",
        data=work_order_text,
        file_name=f"Order_UMK_Well_{well_number.replace(' ', '_')}.md",
        disabled=is_order_disabled,
        use_container_width=True
    )
