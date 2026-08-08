import streamlit as st
import json
import os

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
    
    control_type = st.radio(
        "Тип контроля момента на буровой:",
        ["🪢 Электронный (ИВЭ-50)", "💧 Гидравлический (манометр)"]
    )
    
        col_t1, col_t2 = st.columns(2)
    with col_t1:
        fact_l = st.number_input(
            "Фактическая длина плеча рычага (Lфакт), м:",
            min_value=0.1, max_value=3.0, value=float(passport_length), step=0.005,
            help="Замеряется рулеткой от центра замка трубы до пальца каната."
        )
    with col_t2:
        if "Электронный" in control_type:
            tros_d = st.number_input(
                "Толщина натяжного троса, мм:",
                min_value=0.0, max_value=50.0, value=16.0, step=1.0,
                help="Необходимо для аудита прочности каната на разрыв."
            )
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

# 1. Расчет скорректированного целевого момента с учетом трения смазки
M_required = p_moment * k_grease
g_const = 9.80665 # Точная константа ускорения свободного падения по ГОСТ

# 2. Расчет целевых уставок в зависимости от типа контроля момента
safe_angle = max(angle_alpha, 10.0) # Защита от деления на ноль
if angle_alpha < 10.0:
    st.error("🚨 КРИТИЧЕСКИЙ УГОЛ: Угол менее 10°!")

if "Электронный" in control_type:
    # Расчет усилия (тонны) с учетом угла sin(alpha)
    f_pull_tons = (M_required / (fact_l * np.sin(np.radians(safe_angle)))) / g_const
    target_unit = f"{f_pull_tons:.2f} т"
    label_text = "🎯 Целевое усилие натяжения на ИВЭ-50:"
    p_target_mpa = 0.0 
else:
    # Исправлено: Давление с учетом утери момента (sin(alpha))
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
    st.metric(label="⚙️ Скорректированный момент на резьбе:", value=f"{M_required:.2f} кН·м")

st.info(f"ℹ️ Сводные данные физики процесса: M_паспорт: {p_moment:.1f} кН·м | K_смазки: {k_grease:.2f} | Плечо рычага: {fact_l:.3f} м | Угол α: {angle_alpha:.1f}°")

# =========================================================================
# БЛОК 4 — ПОЛНЫЙ МОДУЛЬ КОМПЛЕКСНОГО АУДИТА И СТРЕСС-ТЕСТИРОВАНИЯ РИСКОВ
# =========================================================================
st.markdown("---")
with st.expander("🛠️ Модуль комплексной валидации рисков свинчивания (СТО ИНТИ S.QS.7)", expanded=True):
    st.markdown("##### Сводный лог инженерного аудита безопасности:")
    umk_logs = []
    has_umk_error = False

    # 1. Валидация механической/гидравлической прочности приводных систем
    if "Электронный" in control_type:
        # Расчет безопасной разрывной нагрузки каната (ГОСТ/API с коэффициентом запаса 3.0)
        safe_cable_load = (0.06 * (tros_d ** 2)) / 3.0
        if f_pull_tons > safe_cable_load:
            umk_logs.append(f"❌ КРИТИЧЕСКИЙ РИСК: Натяжение ({f_pull_tons:.2f} т) превышает безопасный лимит ({safe_cable_load:.2f} т) для троса Ø {tros_d} мм! Риск обрыва.")
            has_umk_error = True
        else:
            umk_logs.append(f"✅ КАНАТ: Безопасная нагрузка OK ({f_pull_tons:.2f} т / лимит {safe_cable_load:.2f} т).")
    else:
        # Проверка критического давления старого гидроключа на разрыв шлангов (РВД)
        MAX_HYDRAULIC_PRESSURE_MPA = 20.0
        if p_target_mpa > MAX_HYDRAULIC_PRESSURE_MPA:
            umk_logs.append(f"❌ КРИТИЧЕСКИЙ РИСК: Давление ({p_target_mpa:.1f} МПа) превышает предел прочности гидросистемы ключа ({MAX_HYDRAULIC_PRESSURE_MPA} МПа)! Риск взрыва РВД.")
            has_umk_error = True
        elif p_target_mpa > (MAX_HYDRAULIC_PRESSURE_MPA * 0.85):
            umk_logs.append(f"🚨 ПРЕДУПРЕЖДЕНИЕ: Ключ будет работать на пределе мощности ({p_target_mpa:.1f} МПа). Возможен перегрев масла и отказ клапанов.")
        else:
            umk_logs.append(f"✅ ГИДРАВЛИКА: Рабочее давление {p_target_mpa:.1f} МПа в безопасных пределах прочности ключа.")

    # 2. Метрологический аудит геометрии рычажной системы ключа УМК
    if fact_l < (passport_length * 0.95):
        umk_logs.append(f"🚨 АНОМАЛИЯ ГЕОМЕТРИИ: Износ/укорочение плеча ключа составляет более 5% ({fact_l} м вместо паспортных {passport_length} м)! Риск деформации рычага и сухарей.")
        has_umk_error = True
    else:
        umk_logs.append(f"✅ ГЕОМЕТРИЯ: Длина плеча ключа УМК ({fact_l} м) находится в пределах технологического допуска.")

    # 3. Контроль предела текучести стали (Защита резьбового соединения от пластических деформаций)
    steel_max_moments = {"Д ": 35.0, "К ": 45.0, "Е ": 55.0, "Л ": 70.0, "М ": 90.0}
    max_allowed_moment = 999.0
    for group, limit in steel_max_moments.items():
        if group in pipe_steel_group:
            max_allowed_moment = limit
            break
            
    if p_moment > max_allowed_moment:
        umk_logs.append(f"❌ ПРЕДЕЛ ТЕКУЧЕСТИ: Паспортный момент ({p_moment} кН·м) превышает эксплуатационный предел прочности для стали группы {pipe_steel_group[:2]} ({max_allowed_moment} кН·м)! Риск смятия резьбы.")
        has_umk_error = True
    elif M_required > (max_allowed_moment * 1.15):
        umk_logs.append(f"🚨 ПРЕДУПРЕЖДЕНИЕ: Из-за трибологии смазки скорректированный момент ({M_required:.1f} кН·м) близок к критическому. Повышенный износ замковой части труб.")
    else:
        umk_logs.append(f"✅ МАТЕРИАЛ: Номинальные характеристики стали группы {pipe_steel_group[:2]} полностью соответствуют прикладываемым нагрузкам.")

    # Интеллектуальный вывод сводного лога
    for log in umk_logs:
        if "❌" in log:
            st.error(log)
        elif "🚨" in log:
            st.warning(log)
        else:
            st.write(log)

    # Итоговый экспертный вердикт системы безопасности
    if not has_umk_error:
        st.success("🟢 ВЕРИФИКАЦИЯ ПРОЙДЕНА: Параметры свинчивания безопасны и соответствуют СТО ИНТИ.")
    else:
        st.error("🚨 СВИНЧИВАНИЕ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО: Устраните критические нарушения технологического режима бурения!")

# =========================================================================
# БЛОК 5 — АДАПТИВНЫЙ НАРЯД-ДОПУСК ---
# =========================================================================
# --- БЛОК 5: АДАПТИВНЫЙ НАРЯД-ДОПУСК ---
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
