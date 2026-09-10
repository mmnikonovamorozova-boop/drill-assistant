import streamlit as st
import json
import os
import numpy as np

# --- АВТЕНТИФИКАЦИЯ И НАСТРОЙКА ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Авторизуйтесь на Главной странице.")
    st.stop()
# Получение сквозных метаданных из сессии приложения
engineer = st.session_state.get("engineer_name", "Не указано")
well = st.session_state.get("well_number", "Не указано")
field = st.session_state.get("field_name", "Не указано")
bha = st.session_state.get("bha_number", "1")

# Добавляем синюю информационную плашку как в первом модуле
st.info(f"📋 **Рейс:** {field} | Скв/Куст: {well} | КНБК №{bha} | **Инженер:** {engineer}")

# Рисуем горизонтальную черту-разделитель для идеальной симметрии
st.divider()

st.set_page_config(page_title="Расчет ключа УМК", layout="wide")
st.title("🔧 Контроль момента свинчивания УМК")

# Получение сквозных метаданных из сессии приложения
engineer = st.session_state.get("engineer_name", "Не указано")
well = st.session_state.get("well_number", "Не указано")
field = st.session_state.get("field_name", "Не указано")
bha = st.session_state.get("bha_number", "1")

# --- ПАСПОРТ СТО ИНТИ ---
with st.expander("🔰 Паспорт верификации СТО ИНТИ", expanded=False):
    st.markdown("### Требования отраслевых стандартов СТО ИНТИ S.QS.7 и S.QS.8 к креплению соединений:")
    st.markdown("""
    * **Контроль геометрии:** Непрерывный аудит линейных размеров рычажной системы ключа УМК. Отклонение плеча Lфакт от паспортного более чем на 5% категорически запрещено.
    * **Трибологический учет:** Обязательный пересчет номинального момента свинчивания в зависимости от коэффициента трения (K) применяемой резьбовой смазки (по ГОСТ/API).
    * **Инструментальный контроль:** Измерение фактического угла натяжения каната (α) для электронного типа контроля (ИВЭ-50) или калибровка манометра гидросистемы.
    * **Предел текучести:** Автоматическая валидация рисков превышения предела текучести стали бурильных труб в зависимости от выбранной группы прочности (Д, К, Е, Л, М).
    """)

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

# === Вкладка 2: Характеристики бурильных труб (Авторасчет СМК) ===
with tab_pipe:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        pipe_steel_group = st.selectbox(
            "Группа прочности стали бурильной трубы:",
            ["Д", "К", "Е", "Л", "М"],
            help="Укажите группу прочности согласно клеймению или паспорту трубы."
        )
    
    # Автоматическая матрица номиналов ГОСТ/API в зависимости от прочности стали
    steel_defaults = {"Д": 22.0, "К": 26.0, "Е": 32.0, "Л": 38.0, "М": 44.0}
    calculated_base_moment = steel_defaults.get(pipe_steel_group, 25.0)
    
    # ИНТЕГРАЦИОННЫЙ ШЛЮЗ: Если Адаптер КНБК уже выдал скорректированный ИИ-момент - берем его!
    if "p_moment_corrected" in st.session_state:
        calculated_base_moment = float(st.session_state["p_moment_corrected"])
    
    with col_p2:
        p_moment = st.number_input(
            "Номинальный момент резьбового соединения, кН·м:",
            value=float(calculated_base_moment),
            help="Целевой номинал. Автоматически пересчитан СМК на основе прочности стали и износа."
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
# БЛОК 4 — МОДУЛЬ КОМПЛЕКСНОЙ ВАЛИДАЦИИ РИСКОВ (СТО ИНТИ S.QS.7)
# =========================================================================
st.markdown("---")
st.markdown("### 🛡 Блок 4: Модуль комплексной валидации рисков")

has_umk_error = False
error_reasons = []  # Массив для фиксации развернутых причин запрета работ

with st.container(border=True):
    # #1 Логика расчета безопасной нагрузки каната (ГОСТ 3241-91) или давления РВД
    if "Электронный" in control_type:
        safe_cable_load = (0.052 * (tros_d ** 2)) / 3.0
        if f_pull_tons > safe_cable_load:
            st.error(f"❌ КРИТИЧЕСКИЙ РИСК: Натяжение ({f_pull_tons:.2f} т) превышает предел ({safe_cable_load:.2f} т)!")
            has_umk_error = True
            error_reasons.append(f"Превышение безопасной нагрузки на канат ключа УМК (Фактическое: {f_pull_tons:.2f} т, Допустимое по ГОСТ: {safe_cable_load:.2f} т)")
        else:
            st.success(f"⚙️ КАНАТ: Нагрузка в норме ({f_pull_tons:.2f} т).")
    else:
        MAX_P = 20.0
        if p_target_mpa > MAX_P:
            st.error(f"❌ КРИТИЧЕСКИЙ РИСК: Давление ({p_target_mpa:.1f} МПа) > РВД ({MAX_P} МПа)!")
            has_umk_error = True
            error_reasons.append(f"Превышение предела рабочего давления гидросистемы (Фактическое: {p_target_mpa:.1f} МПа, Лимит РВД: {MAX_P} МПа)")
        else:
            st.success(f"💧 ГИДРАВЛИКА: Давление ({p_target_mpa:.1f} МПа) в норме.")

    # #2 Метрологический аудит износа геометрии рычажной системы ключа УМК
    passport_length = active_keys_db.get(selected_key, fact_l)
    
    if fact_l < (passport_length * 0.95) or fact_l > (passport_length * 1.05):
        st.error(f"❌ КРИТИЧЕСКИЙ РИСК: Фактическое плечо ({fact_l:.3f} м) отклоняется от паспортного ({passport_length:.3f} м) более чем на 5%!")
        has_umk_error = True
        error_reasons.append(f"Критическое отклонение фактического плеча рычага ({fact_l:.3f} м) от паспортного значения ({passport_length:.3f} м) — нарушение геометрии УМК")
    else:
        st.success(f"📐 ГЕОМЕТРИЯ: Плечо рычага в допуске ({fact_l:.3f} м).")
    # #3 Контроль предела текучести стали
    steel_max_moments = {"Д": 35.0, "К": 45.0, "Е": 55.0, "Л": 70.0, "М": 90.0}
    max_allowed_moment = steel_max_moments.get(pipe_steel_group, 999.0)

    if M_required > max_allowed_moment:
        st.error(f"❌ ПРЕДЕЛ ТЕКУЧЕСТИ: Момент свинчивания ({M_required:.2f} кН·м) превышает предел ({max_allowed_moment} кН·м) для стали {pipe_steel_group}!")
        has_umk_error = True
        error_reasons.append(f"Превышение предела текучести стали соединения (Расчетный момент: {M_required:.2f} кН·м, Допустимый для группы {pipe_steel_group}: {max_allowed_moment} кН·м)")
    elif M_required > (max_allowed_moment * 0.90):
        st.warning(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Момент свинчивания ({M_required:.2f} кН·м) близко к лимиту стали {pipe_steel_group} ({max_allowed_moment} кН·м)!")
    else:
        st.success(f"🔩 МАТЕРИАЛ: Соответствие прочности стали {pipe_steel_group} подтверждено.")
    
    # # 4. Итоговый экспертный вердикт системы менеджмента качества (СМК)
    if not has_umk_error:
        st.success("🛡️ ВЕРИФИКАЦИЯ ПРОЙДЕНА: Параметры свинчивания безопасны и соответствуют СТО ИНТИ.")
        is_order_disabled = False
    else:
        st.error("🚨 СВИНЧИВАНИЕ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО: Устраните нарушения технологического режима!")
        is_order_disabled = True

# =========================================================================
# БЛОК 5 — ОФИЦИАЛЬНЫЙ ДОКУМЕНТ СМК (СТО ИНТИ S.QS.7 / S.QS.8)
# =========================================================================
st.markdown("---")
st.markdown("### 📋 Блок 5: Документ СМК")

# Определяем название файла для скачивания
if is_order_disabled:
    file_title = f"Akt_Zapreta_UMK_Skv_{well}"
    bg_color = "#FEF2F2"  # Мягкий красный фон для запрета
    border_color = "#EF4444"  # Красная рамка
    title_text = "АКТ О ЗАПРЕТЕ ПРОВЕДЕНИЯ ИНЖЕНЕРНЫХ РАБОТ"
else:
    file_title = f"Order_UMK_Well_{well}"
    bg_color = "#FAFAFA"  # Светлый фон для распоряжения
    border_color = "#1E3A8A"  # Синяя рамка
    title_text = "РАСПОРЯЖЕНИЕ НА КРЕПЛЕНИЕ СОЕДИНЕНИЙ КНБК"

# Начинаем сборку HTML бланка (открываем контейнер-рамку)
html_form = f"<div style='border:3px solid {border_color}; padding:25px; border-radius:10px; background-color:{bg_color}; font-family:Arial, sans-serif; color:#333333;'>"
html_form += "<h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>"
html_form += f"<h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>{title_text}</h3>"
# Заполнение блока общей информации о скважине и инженере
html_form += f"<p><b>Месторождение:</b> {field} &nbsp;&nbsp;&nbsp;&nbsp; <b>Скважина / Куст:</b> {well}</p>"
html_form += f"<p><b>Инженер ННБ:</b> {engineer} &nbsp;&nbsp;&nbsp;&nbsp; <b>Сборка КНБК №:</b> {bha}</p>"
html_form += "<hr style='border:1px solid #CCCCCC; margin:15px 0;'>"
if is_order_disabled:
    html_form += "<p style='color:#991B1B;'><b>КРИТИЧЕСКИЕ НАРУШЕНИЯ (СВИНЧИВАНИЕ ЗАПРЕЩЕНО):</b></p><ul>"
    for reason in error_reasons:
        html_form += f"<li>{reason}</li>"
    html_form += "</ul>"
else:
    html_form += f"<p><b>Группа прочности стали:</b> {pipe_steel_group} &nbsp;&nbsp;&nbsp;&nbsp; <b>Номинальный момент:</b> {p_moment:.1f} кН·м</p>"
    html_form += f"<p><b>Скорректированный момент (учет смазки):</b> {M_required:.2f} кН·м</p>"
    if "Электронный" in control_type:
        html_form += f"<p style='color:#1E3A8A;'><b>ЦЕЛЕВОЕ УСИЛИЕ НА ИВЭ-50:</b> {f_pull_tons:.2f} т (при угловом коэффициенте α: {angle_alpha:.1f}°)</p>"
    else:
        html_form += f"<p style='color:#1E3A8A;'><b>ЦЕЛЕВОЕ ДАВЛЕНИЕ МАНОМЕТРА:</b> {p_target_mpa:.2f} МПа ({p_target_mpa * 10.1972:.1f} кгс/см²)</p>"

# Закрываем главный контейнер бланка
html_form += "</div>"
# Отображаем собранный документ в интерфейсе
st.components.v1.html(html_form, height=350, scrolling=True)

# Кнопка №1: Скачивание готового файла
st.download_button(
    label="💾 Скачать официальный документ СМК в формате HTML",
    data=html_form,
    file_name=f"{file_title}.html",
    mime="text/html",
    use_container_width=True
)

# Поле для почты
email_recipient = st.text_input("Email получателя документа:", placeholder="boss@yourcompany.ru")

# Кнопка №2: Безопасная отправка почты через кнопку-триггер
if st.button("✉ Подготовить письмо в почтовой программе", use_container_width=True):
    subject_text = f"Документ СМК по УМК — {field}, Скв. {well}".replace(" ", "%20")
    body_text = f"Приветствую! Сформирован документ контроля момента свинчивания УМК для скважины {well} ({field}). Инженер: {engineer}.".replace(" ", "%20")
    
    mailto_link = f"mailto:{email_recipient}?subject={subject_text}&body={body_text}"
    js_code = f'<script>window.open("{mailto_link}", "_blank");</script>'
    st.components.v1.html(js_code, height=0)

st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'><b>Разработчик:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • СТО ИНТИ • ООО «Траектория-СЕРВИС» © 2026</div>", unsafe_allow_html=True)
