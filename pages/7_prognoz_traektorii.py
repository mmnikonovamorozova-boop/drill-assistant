import streamlit as st
import pandas as pd
import numpy as np
import math
import json
import base64
import time

# =========================================================================
# БЛОК 0 — СТРОГАЯ АВТЕНТИФИКАЦИЯ И СЛУЖЕБНЫЕ НАСТРОЙКИ СТРАНИЦЫ
# =========================================================================
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Авторизуйтесь на Главной странице.")
    st.stop()
st.set_page_config(page_title="Прогноз траектории КНБК", layout="wide")
st.title("🎯 Модуль предиктивного моделирования пространственной интенсивности")

# =========================================================================
# БЛОК 1 — ИНИЦИАЛИЗАЦИЯ И ПАСПОРТ СООТВЕТСТВИЯ СТО ИНТИ
# Функционал: Верификация алгоритмов ИНТИ S.QS.7, S.QS.8 и S.100.3.
# =========================================================================
# --- ЧАСТЬ 1.1: СТАТИЧЕСКИЙ ПАСПОРТ ВЕРИФИКАЦИИ СТО ИНТИ ---
st.markdown("### 📈 Блок 1: Предиктивный прогноз траектории скважины")

with st.expander("📋 Паспорт верификации СТО ИНТИ (Прогнозирование траектории и КНБК)"):
    st.markdown(
        """
        <div style="background-color: #F8FAFC; padding: 15px; border-radius: 6px; border-left: 5px solid #2563EB;">
            <p><b>1. СТО ИНТИ S.100.3:</b> Стандартизация предиктивных моделей и алгоритмов машинного обучения для адаптивного прогнозирования пространственного положения ствола скважины при роторном и слайдовом бурении.</p>
            <p style="margin-bottom: 0px;"><b>2. СТО ИНТИ S.QS.8:</b> Контроль интенсивности искривления (DLS) и коэффициентов передачи геометрии КНБК (Slide Factor) для предотвращения локальных перегибов и жестких посадок инструмента.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

st.markdown(" ")  # Компактный технологический отступ
# =========================================================================
# БЛОК 2: УМНОЕ ИИ-ЯДРО: ИМПОРТ И СЕЛЕКЦИЯ КАЛИБРОВОК ПО ИМЕНИ СКВАЖИНЫ
# =========================================================================

# Исправлено: Оставляем строго один декоратор кэширования для защиты от зависаний
@st.cache_data(ttl=60)
def load_calibrations_from_github_api(target_well_name):
    """
    Развернутая функция безопасного извлечения адаптивных весов КНБК из удаленного
    репозитория GitHub API по принципам сквозного логирования СТО ИНТИ S.100.3.
    """
    # Безопасное чтение токена авторизации из секретов Streamlit Cloud
    token = st.secrets.get("GITHUB_TOKEN", None)
    
    # Репозиторий хранения калибровочных паспортов компании
    repo = "mmnikonovamorozova-boop/drill-assistant"
    path = "calibrations_db.json"
    url = f"https://github.com{repo}/contents/{path}"
    
    # Формирование дефолтного (базового) паспорта КНБК на случай сбоя связи
    default_passport = {
        "well_name": "Базовый паспорт КНБК",
        "k_slide_base": 0.38,
        "k_rotary_base": 0.02,
        "last_update": "01.01.2026"
    }
    
    if not token:
        # Автономный режим работы на удаленной буровой (без интернета)
        return default_passport

    try:
        import requests
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            file_data = response.json()
            # Декодирование защищенного Base64-контента из GitHub
            content_b64 = file_data.get("content", "")
            json_str = base64.b64decode(content_b64).decode("utf-8")
            db_dict = json.loads(json_str)
            
            # Поиск калибровочных весов под конкретную целевую скважину
            clean_target = str(target_well_name).strip().upper()
            for key_well, data_v in db_dict.items():
                if clean_target in str(key_well).strip().upper():
                    return data_v
                    
            # Если скважина новая — возвращаем базовые отраслевые настройки
            return default_passport
        else:
            return default_passport
            
    except Exception:
        # Защитный барьер: при любых сетевых ошибках возвращаем стабильный дефолт
        return default_passport

# =========================================================================
# БЛОК 3 — СКВОЗНАЯ ШИНА ДАННЫХ И ЦЕНТРАЛЬНЫЙ АДАПТИВНЫЙ ИНТЕРФЕЙС
# Функционал: Считывание vink_limits_db.xlsx, разгрузка боковой панели,
# вынос настроек КНБК, режимов и геологии в центр экрана для мобильных устройств.
# =========================================================================

# --- 3.1. Боковая панель (Только автоматические сквозные данные) ---
st.sidebar.markdown("### 🧬 Сквозные данные системы")
selected_vink = st.sidebar.text_input("Заказчик (Холдинг):", value=st.session_state.get("main_page_company", "Роснефть"), disabled=True)

# Считывание базы данных лимитов из Excel с защитным откатом
try:
    df_vink_db = pd.read_excel("vink_limits_db.xlsx")
    df_vink_db["Холдинг"] = df_vink_db["Холдинг"].astype(str).str.strip()
    df_vink_db["Заказчик (ДОР)"] = df_vink_db["Заказчик (ДОР)"].astype(str).str.strip()
except Exception:
    fallback_data = {
        "Холдинг": ["Роснефть", "Роснефть", "Газпром нефть", "ЛУКОЙЛ"],
        "Заказчик (ДОР)": ["ООО РН-Юганскнефтегаз", "АО Самаранефтегаз", "ООО Газпромнефть-Хантос", "ООО ЛУКОЙЛ-Западная Сибирь"],
        "Лимит_DLS": [2.5, 3.0, 3.2, 2.8],
        "Лимит_ГНО": [1.0, 1.5, 1.2, 1.1]
    }
    df_vink_db = pd.DataFrame(fallback_data)

# Фильтруем строки таблицы по холдингу
filtered_dors = df_vink_db[df_vink_db["Холдинг"] == selected_vink]
list_of_dors = filtered_dors["Заказчик (ДОР)"].unique().tolist() if not filtered_dors.empty else ["Стандартный договор"]

# Подтягиваем автоматические параметры раствора и износа
shared_buoyancy = float(st.session_state.get("shared_buoyancy_factor", 0.85))
yield_stress = float(st.session_state.get("shared_yield_stress", 40.0))
radial_wear_vzd = float(st.session_state.get("val_radial_ich", 0.20))

st.sidebar.caption(f"💧 ДНС раствора: {yield_stress} дПа")
st.sidebar.caption(f"🔧 Люфт шпинделя: {radial_wear_vzd} мм")
st.sidebar.caption(f"🚢 Коэф. плавучести: {shared_buoyancy:.2f}")


# --- 3.2. Центральная рабочая область (Адаптивные вкладки для мобильных) ---
st.markdown("### 🛠 Настройки интервала бурения")
tab_contract, tab_knbc, tab_geology = st.tabs(["📋 Контракт и Лимиты", "📐 Компоновка КНБК", "🌋 Геологический разрез"])

# Вкладка 1: Контрактные ограничения ДОРов
with tab_contract:
    c_c1, c_c2 = st.columns(2)
    with c_c1:
        selected_dor = st.selectbox(f"🏢 Выберите предприятие ({selected_vink}):", list_of_dors)
    with c_c2:
        gno_zone = st.checkbox("⚠️ Учитывать зоны ГНО / Опасность желобов", value=False)
    
    # Извлекаем лимиты на основе выбранного ДОРа
    if not filtered_dors.empty and selected_dor in list_of_dors:
        dor_row = filtered_dors[filtered_dors["Заказчик (ДОР)"] == selected_dor].iloc[0]
        contract_dls_limit = float(dor_row["Лимит_DLS"])
        contract_gno_limit = float(dor_row["Лимит_ГНО"])
    else:
        contract_dls_limit, contract_gno_limit = 3.0, 1.2
        
    # Вывод лимита интенсивности в зависимости от галочки ГНО
    if gno_zone:
        max_allowed_dls = st.number_input("Макс. допустимый DLS по договору (ГНО), °/10м:", value=contract_gno_limit, step=0.1)
    else:
        max_allowed_dls = st.number_input("Макс. допустимый DLS по договору, °/10м:", value=contract_dls_limit, step=0.1)

# Вкладка 2: Геометрия КНБК и Режимы бурения
with tab_knbc:
    c_k1, c_k2, c_k3 = st.columns(3)
    with c_k1:
        knbc_type = st.selectbox("Конфигурация КНБК:", ["Стандартная", "Маятниковая", "Стабилизирующая"])
    with c_k2:
        target_angle = st.number_input("Текущий зенитный угол, °:", min_value=0.0, max_value=90.0, value=45.0)
    with c_k3:
        target_wob = st.number_input("Нагрузка на долото (WOB), т:", value=15.0)

# Вкладка 3: Геология без ГГИ
with tab_geology:
    lithology_type = st.selectbox(
        "Текущая проходимая свита / литология (при отсутствии ГГИ):",
        [
            "Глины, аргиллиты, песчаники (Мягкие породы)",
            "Переслаивание глин и песчаников (Средняя твердость)",
            "Известняки, доломиты, ангидриты (Твердые породы)",
            "Кремнистые и плотные скальные породы (Крепкие)"
        ],
        index=1
    )

    if "Мягкие" in lithology_type: default_ani, default_drift = 0.02, 0.01
    elif "Средняя" in lithology_type: default_ani, default_drift = 0.05, 0.03
    elif "Твердые" in lithology_type: default_ani, default_drift = 0.12, 0.08
    else: default_ani, default_drift = 0.18, 0.15

    base_ani = st.number_input("Базовая анизотропия породы (H_ani):", value=default_ani, step=0.01)
    default_rotary_drift = float(default_drift)

buoyancy_factor = shared_buoyancy # Переменная для сохранения совместимости с нижними блоками

# =========================================================================
# БЛОК 5.1 — ФИЗИКО-МАТЕМАТИЧЕСКОЕ МОДЕЛИРОВАНИЕ СИЛ КНБК И УВОДА ДОЛОТА
# Требования легитимности: СТО ИНТИ S.100.3 / API RP 7G
# =========================================================================

st.markdown("### 🛠️ Блок 5: Пространственная интенсивность и увод")

# Извлекаем сквозные реологические параметры из сессии (зашиты в Блоке 5_kontrol_rastvora)
f_dens = float(st.session_state.get("shared_buoyancy_factor", 1.0)) # Фактор плавучести инструмента
f_yp_corrected = float(st.session_state.get("shared_yield_stress", 12.0)) # Динамическое напряжение сдвига (ДНС), дПа
n_hb = float(st.session_state.get("shared_flow_index", 0.65)) # Индекс течения Гершеля-Балкли

# --- ШАГ 5.1.1: СТРОГИЙ РАСЧЕТ ГИДРОДИНАМИЧЕСКОГО СОПРОТИВЛЕНИЯ РАСТВОРА ---
# Физически корректная модель: рост ДНС (f_yp_corrected) увеличивает сопротивление КНБК в затрубе
rheology_modifier = (1.0 / f_dens) * (1.0 + (f_yp_corrected * 0.025) * (2.0 - n_hb))

# Извлекаем калибровочные веса КНБК из ИИ-паспорта (Блок 2)
k_slide_current = float(active_calibration.get("k_slide_base", 0.38))
k_rotary_current = float(active_calibration.get("k_rotary_base", 0.02))

# Ввод параметров геомеханики пласта и конструкции КНБК инженером ННБ
st.markdown("##### ⚙️ Параметры калибровки боковой силы и анизотропии пласта:")
col_f1, col_f2 = st.columns(2)
with col_f1:
    formation_anisotropy = st.slider("Коэффициент анизотропии горной породы (h):", 
                                     min_value=0.50, max_value=1.50, value=0.95, step=0.01,
                                     help="Физическая способность пласта уводить долото по или против падения пласта")
with col_f2:
    wob_force_kn = st.number_input("Осевая нагрузка на долото WOB (кН):", 
                                   min_value=10.0, max_value=250.0, value=120.0, step=5.0)

# --- ШАГ 5.1.2: ФИЗИЧЕСКИЙ РАСЧЕТ СИЛЫ БОКОВОГО ОТКЛОНЕНИЯ ---
# Боковое уводящее усилие долота зависит от геометрии, нагрузки и реологии промывочной среды
side_force_calculated = wob_force_kn * (1.0 - formation_anisotropy) * k_slide_current * rheology_modifier

# =========================================================================
# БЛОК 5.2 — ИНТЕЛЛЕКТУАЛЬНЫЙ РАСЧЕТ ПРОГНОЗНОЙ ТРАЕКТОРИИ (СТО ИНТИ S.100.3)
# =========================================================================

st.markdown("##### 🔮 Параметры планирования прогнозного интервала:")
col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    progno_step_meters = st.number_input("Длина прогнозного интервала (м):", 
                                         min_value=10.0, max_value=300.0, value=30.0, step=10.0)
with col_p2:
    planned_slide_pct = st.slider("Доля слайдирования на интервале (%):", 
                                  min_value=0.0, max_value=100.0, value=30.0, step=5.0)
with col_p3:
    tool_face_angle = st.slider("Угол установки отклонителя (Tool Face, °):", 
                                min_value=0.0, max_value=360.0, value=45.0, step=5.0)

# Перевод процента слайда в долевой коэффициент
slide_fraction = planned_slide_pct / 100.0

# 1. Извлечение последних фактических маркшейдерских точек траектории
if df_trajectory_calculated is not None and not df_trajectory_calculated.empty:
    last_row = df_trajectory_calculated.iloc[-1]
    current_md = float(last_row["ГЛУБИНА_MD"])
    current_inc = float(last_row["ЗЕНИТ_ГРАД"])
    current_azi = float(last_row["АЗИМУТ_ГРАД"])
    current_tvd = float(last_row["TVD"])
    current_north = float(last_row["NORTH"])
    current_east = float(last_row["EAST"])
else:
    # Безопасные стартовые значения по умолчанию (если файл ГГИ не загружен)
    current_md = 1500.0
    current_inc = 25.0
    current_azi = 120.0
    current_tvd = 1420.0
    current_north = 150.0
    current_east = 320.0

# --- ШАГ 5.2.1: РАСЧЕТ ЕСТЕСТВЕННОГО И ПРИНУДИТЕЛЬНОГО ИСКРИВЛЕНИЯ КНБК ---
# Интенсивность изменения зенитного угла под влиянием слайда и боковой силы (град/10м)
# Учитываем физический увод долота side_force_calculated из Блока 5.1
build_rate_slide = 0.45 * k_slide_current * math.cos(math.radians(tool_face_angle))
build_rate_rotary = 0.02 * k_rotary_current + (side_force_calculated * 0.001)

# Итоговая интенсивность изменения зенитного угла (град/10м)
total_build_rate = (build_rate_slide * slide_fraction) + (build_rate_rotary * (1.0 - slide_fraction))

# Интенсивность изменения азимута (град/10м) с учетом естественного увода породы
turn_rate_slide = 0.45 * k_slide_current * math.sin(math.radians(tool_face_angle))
turn_rate_rotary = -0.015 * (1.0 - formation_anisotropy) # Естественный увод вправо/влево по породе

# Итоговый темп изменения азимута (град/10м)
total_turn_rate = (turn_rate_slide * slide_fraction) + (turn_rate_rotary * (1.0 - slide_fraction))

# --- ШАГ 5.2.2: ИНТЕГРАЛЬНЫЙ ПРОГНОЗ ПОЛОЖЕНИЯ СТВОЛА ---
forecast_md = current_md + progno_step_meters
# Вычисление приращений углов на длину прогнозной проходки
delta_inc = (total_build_rate / 10.0) * progno_step_meters
delta_azi = (total_turn_rate / 10.0) * progno_step_meters

forecast_inc = max(0.0, min(90.0, current_inc + delta_inc))
forecast_azi = (current_azi + delta_azi) % 360.0

# Усредненные углы интервала для тригонометрического шага по API RP 7G
avg_inc_rad = math.radians((current_inc + forecast_inc) / 2.0)
avg_azi_rad = math.radians((current_azi + forecast_azi) / 2.0)

# Приращения пространственных координат (метод сбалансированных тангенсов)
forecast_tvd = current_tvd + progno_step_meters * math.cos(avg_inc_rad)
forecast_north = current_north + progno_step_meters * math.sin(avg_inc_rad) * math.cos(avg_azi_rad)
forecast_east = current_east + progno_step_meters * math.sin(avg_inc_rad) * math.sin(avg_azi_rad)

# Расчет пространственной интенсивности (DLS) на прогнозном интервале
cos_dl = math.cos(math.radians(current_inc)) * math.cos(math.radians(forecast_inc)) + \
         math.sin(math.radians(current_inc)) * math.sin(math.radians(forecast_inc)) * math.cos(math.radians(forecast_azi - current_azi))
cos_dl = max(-1.0, min(1.0, cos_dl))
forecast_dls = (math.acos(cos_dl) * 10.0) / max(0.001, progno_step_meters)

# Сохранение результатов прогнозирования в сессию Streamlit
st.session_state["forecast_md"] = forecast_md
st.session_state["forecast_inc"] = forecast_inc
st.session_state["forecast_azi"] = forecast_azi
st.session_state["forecast_dls_deg10m"] = np.degrees(forecast_dls)

# --- ШАГ 5.2.3: ВЫВОД ПРЕДИКТИВНЫХ РЕЗУЛЬТАТОВ НА ЭКРАН ---
st.markdown("##### 📊 Прогноз пространственного положения КНБК на забое:")
col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("Прогнозная глубина MD", f"{forecast_md:.1f} м", f"+{progno_step_meters:.1f} м")
col_r2.metric("Прогнозный зенитный угол", f"{forecast_inc:.2f}°", f"{delta_inc:+.2f}°")
col_r3.metric("Прогнозный азимут ствола", f"{forecast_azi:.2f}°", f"{delta_azi:+.2f}°")

# =========================================================================
# БЛОК 6 — ТЕХНОЛОГИЧЕСКИЙ КАЛЬКУЛЯТОР И КОНТРОЛЬ ШТРАФНЫХ САНКЦИЙ ЗАКАЗЧИКА
# Требования легитимности: СТО ИНТИ S.QS.8 / Коммерческие ТК Договора
# =========================================================================

st.markdown("---")
st.markdown("### 🎯 Блок 6: Оптимизация слайдирования и аудит штрафных рисков")
st.caption("Расчет интервалов проходки с контролем правила 3 последовательных нарушений по ТК договора")

# --- ШАГ 6.1: ИНТЕРАКТИВНЫЙ ВВОД ШТРАФНЫХ ЛИМИТОВ ТЕКУЩЕГО ДОГОВОРА ---
st.markdown("##### 📜 Настройка лимитов интенсивности по Договору Заказчика:")
col_tk1, col_tk2, col_tk3 = st.columns(3)

with col_tk1:
    tk_dls_max = st.number_input(
        "Макс. допустимая интенсивность (°/10м):", 
        min_value=0.5, max_value=3.0, value=1.2, step=0.1, key="tk_dls_max",
        help="Верхний предел пространственной интенсивности (DLS) по ТК Договора"
    )
with col_tk2:
    tk_dls_min = st.number_input(
        "Мин. необходимый набор угла (°/10м):", 
        min_value=0.0, max_value=1.5, value=0.15, step=0.05, key="tk_dls_min",
        help="Минимальный темп изменения угла для исключения падения траектории"
    )
with col_tk3:
    st.metric("Триггер коммерческого штрафа", "3 точки подряд", help="Согласно условиям договора, 3 последовательных нарушения ведут к финансовым санкциям")

# --- ШАГ 6.2: АВТОМАТИЧЕСКИЙ ПОИСК ЦЕЛЕВЫХ УСТАВОК ИЗ МАРКШЕЙДЕРСКОГО ПЛАНА ---
if uploaded_ggi is not None and df_trajectory_calculated is not None:
    try:
        target_inc = float(df_trajectory_calculated.iloc[-1]["ЗЕНИТ_ГРАД"])
        target_azi = float(df_trajectory_calculated.iloc[-1]["АЗИМУТ_ГРАД"])
        st.info(f"🎯 Проектные уставки автоматически считаны из ГГИ: Зенит {target_inc:.2f}°, Азимут {target_azi:.2f}°")
    except Exception:
        target_inc = 26.50
        target_azi = 118.20
else:
    col_t1, col_t2 = st.columns(2)
    with col_t1: target_inc = st.number_input("Целевой проектный зенитный угол (°):", value=26.50, key="b6_target_inc")
    with col_t2: target_azi = st.number_input("Целевой проектный азимут ствола (°):", value=118.20, key="b6_target_azi")

# --- ШАГ 6.3: МАТЕМАТИЧЕСКИЙ ПОДБОР ПРОХОДКИ СЛАЙДОМ ---
needed_delta_inc = target_inc - current_inc
available_build_rate_10m = build_rate_slide

if abs(available_build_rate_10m) > 0.001:
    required_slide_meters = (needed_delta_inc / (available_build_rate_10m / 10.0))
    required_slide_meters = max(0.0, min(progno_step_meters, required_slide_meters))
else:
    required_slide_meters = 0.0

required_rotary_meters = max(0.0, progno_step_meters - required_slide_meters)
recommended_slide_pct = (required_slide_meters / max(1.0, progno_step_meters)) * 100.0

# Извлекаем расчетное DLS прогнозного шага из Блока 5.2
forecast_dls_val = st.session_state.get("forecast_dls_deg10m", 0.0)

# --- ШАГ 6.4: АЛГОРИТМ СКОЛЬЗЯЩЕГО ОКНА КОНТРОЛЯ ШТРАФОВ (3 ТОЧКИ) ---
# Анализируем историю последних замеров из загруженного файла ГГИ
consecutive_violations = 0
violation_history_text = []

if df_trajectory_calculated is not None and "DLS_10M" in df_trajectory_calculated.columns:
    # Берем последние 2 фактические точки
    last_actual_dls = df_trajectory_calculated["DLS_10M"].tail(2).values
    # Создаем цепочку: 2 прошлые точки + 1 наша прогнозная
    combined_dls_chain = list(last_actual_dls) + [forecast_dls_val]
    
    # Проверяем цепочку на превышение или недобор
    for idx, dls_point in enumerate(combined_dls_chain):
        point_name = f"Замер №{idx+1}" if idx < 2 else "Текущий Прогноз"
        if dls_point > tk_dls_max:
            consecutive_violations += 1
            violation_history_text.append(f"❌ {point_name}: Превышение лимита ({dls_point:.2f} > {tk_dls_max}°/10м)")
        elif dls_point < tk_dls_min:
            consecutive_violations += 1
            violation_history_text.append(f"❌ {point_name}: Недобор интенсивности ({dls_point:.2f} < {tk_dls_min}°/10м)")
        else:
            # Прерываем серию последовательных нарушений, если замер в норме
            if consecutive_violations < 3:
                consecutive_violations = 0

# --- ШАГ 6.5: ВЫВОД ДИРЕКТИВЫ И КОММЕРЧЕСКОГО РИСК-МЕНЕДЖМЕНТА ---
with st.container(border=True):
    st.markdown("##### 📝 Директивное технологическое указание для инженера ННБ:")
    
    col_out1, col_out2, col_out3 = st.columns(3)
    col_out1.metric("Необходимый СЛАЙД", f"{required_slide_meters:.1f} м", "Режим ориентирования")
    col_out2.metric("Необходимый РОТОР", f"{required_rotary_meters:.1f} м", "Режим вращения")
    col_out3.metric("Доля слайда в рейсе", f"{recommended_slide_pct:.0f} %")
    
    st.markdown("##### ⚖️ Аудит выполнения Технических Критериев договора:")
    
    # Выводим статус на основе скользящего окна
    if consecutive_violations >= 3:
        st.error(
            f"🚨 **КРИТИЧЕСКИЙ ФИНАНСОВЫЙ РИСК: ВЫСТАВЛЕНИЕ ШТРАФА!**\n"
            f"Зафиксировано 3 последовательных нарушения уставных лимитов ТК Договора подряд (включая прогнозный интервал).\n"
            f"Срочно измените параметры слайдирования для выравнивания траектории!"
        )
        with st.expander("Посмотреть хронологию нарушений цепочки"):
            for tx in violation_history_text: st.write(tx)
            
    elif consecutive_violations > 0 and consecutive_violations < 3:
        st.warning(
            f"⚠️ **ВНИМАНИЕ: Нарушение лимитов ТК (Серия: {consecutive_violations} из 3).**\n"
            f"Текущий тренд ведет к коммерческому штрафу. Ситуация на усмотрении супервайзера Заказчика. "
            f"Рекомендуется скорректировать угол Tool Face для возврата в коридор."
        )
        with st.expander("Посмотреть хронологию нарушений цепочки"):
            for tx in violation_history_text: st.write(tx)
    else:
        st.success("✔️ Профиль КНБК полностью соответствует критериям договора. Риски коммерческих штрафов отсутствуют.")

# =========================================================================
# БЛОК 7 — ИИ-ЯДРО САМООБУЧЕНИЯ И СИНХРОНИЗАЦИИ С GITHUB API
# Требования легитимности: СТО ИНТИ S.100.3 (Адаптивное машинное обучение)
# =========================================================================

def push_calibration_to_github_api(target_well_name, updated_k_slide, updated_k_rotary):
    """
    Развернутая функция безопасной фиксации пересчитанных весов КНБК в удаленную
    базу данных через защищенный шлюз GitHub API.
    """
    token = st.secrets.get("GITHUB_TOKEN", None)
    repo = "mmnikonovamorozova-boop/drill-assistant"
    path = "calibrations_db.json"
    url = f"https://github.com{repo}/contents/{path}"
    
    if not token:
        st.error("🚨 ОШИБКА АВТОРИЗАЦИИ: В системе Streamlit Secrets отсутствует токен GITHUB_TOKEN. Запись невозможна.")
        return False

    try:
        import requests
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Шаг 1: Извлекаем текущую версию файла для получения SHA-хэша коммита
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            file_data = response.json()
            sha = file_data.get("sha", "")
            content_b64 = file_data.get("content", "")
            json_str = base64.b64decode(content_b64).decode("utf-8")
            db_dict = json.loads(json_str)
        else:
            db_dict = {}
            sha = None
            
        # Шаг 2: Модифицируем структуру данных ИИ-паспорта скважины
        clean_key = str(target_well_name).strip().upper()
        db_dict[clean_key] = {
            "well_name": target_well_name,
            "k_slide_base": round(float(updated_k_slide), 4),
            "k_rotary_base": round(float(updated_k_rotary), 4),
            "last_update": time.strftime("%d.%m.%Y %H:%M:%S")
        }
        
        # Шаг 3: Кодируем обновленный файл обратно в Base64 формат
        updated_json_bytes = json.dumps(db_dict, ensure_ascii=False, indent=4).encode("utf-8")
        updated_b64_str = base64.b64encode(updated_json_bytes).decode("utf-8")
        
        # Шаг 4: Отправляем коммит изменений в удаленный репозиторий компании
        commit_payload = {
            "message": f"🤖 ИИ-Адаптация КНБК: Обновлены калибровки для скважины {target_well_name}",
            "content": updated_b64_str
        }
        if sha:
            commit_payload["sha"] = sha
            
        put_response = requests.put(url, headers=headers, json=commit_payload, timeout=5)
        return put_response.status_code in [200, 201]
        
    except Exception as ex:
        st.error(f"🚨 ОШИБКА СИНХРОНИЗАЦИИ С СЕРВЕРОМ GITHUB: {str(ex)}")
        return False

# --- ИНТЕРФЕЙСНЫЙ БЛОК ОБУЧЕНИЯ (БЛОК 7.2) ---
st.markdown("---")
st.markdown("### 🤖 Блок 7: Полевое самообучение предиктивного ядра")
st.caption("Адаптивная корректировка паспортных коэффициентов КНБК по фактическим замерам инклинометрии")

# Ввод фактических параметров проходки от инженера ННБ
st.markdown("##### 📐 Фактические параметры отработавшего интервала:")
col_l1, col_l2, col_l3 = st.columns(3)
with col_l1:
    actual_interval_len = st.number_input("Длина отработавшего интервала (м):", value=30.0, step=5.0, key="b7_len")
with col_l2:
    actual_delta_inc = st.number_input("Фактический набранный зенитный угол (°):", value=1.10, step=0.05, key="b7_inc")
with col_l3:
    actual_slide_pct = st.slider("Фактическая доля слайда в интервале (%):", min_value=0.0, max_value=100.0, value=40.0, step=5.0)

# Расчет фактического изменения траектории
fact_slide_fraction = actual_slide_pct / 100.0

if st.button("🚀 Запустить адаптивное ИИ-самообучение модели", use_container_width=True):
    # Рассчитываем теоретический прогноз, который давала старая модель
    theoretical_delta_inc = ((0.45 * k_slide_current * fact_slide_fraction) + (build_rate_rotary * (1.0 - fact_slide_fraction))) * (actual_interval_len / 10.0)
    
    # Вычисляем ошибку прогнозирования
    prediction_error = actual_delta_inc - theoretical_delta_inc
    
    # Оптимизированный градиентный шаг обучения (СТО ИНТИ S.100.3)
    learning_rate = 0.08
    new_k_slide = max(0.10, min(1.20, k_slide_current + (prediction_error * learning_rate * fact_slide_fraction)))
    new_k_rotary = max(0.001, min(0.15, k_rotary_current + (prediction_error * learning_rate * (1.0 - fact_slide_fraction) * 0.05)))
    
    st.markdown("##### Результаты пересчета внутренних весов КНБК:")
    st.write(f"📉 Старый Slide Factor: `{k_slide_current:.3f}` ➡️ Новый адаптированный Slide Factor: `{new_k_slide:.3f}`")
    st.write(f"📉 Старый Rotary Factor: `{k_rotary_current:.3f}` ➡️ Новый адаптированный Rotary Factor: `{new_k_rotary:.3f}`")
    st.write(f"🎯 Абсолютная ошибка прогноза по углу на интервале составила: `{abs(prediction_error):.2f}°`")
    
    # Фиксация изменений в облаке
    with st.spinner("💾 Запись обновленных калибровок КНБК в удаленную базу данных GitHub..."):
        success = push_calibration_to_github_api(well_name, new_k_slide, new_k_rotary)
        if success:
            st.success(f"✔️ ИИ-паспорт скважины {well_name} успешно обновлен! Калибровки будут применены автоматически при следующем цикле.")
            st.cache_data.clear() # Сброс кэша Streamlit для мгновенного обновления интерфейса
        else:
            st.warning("⚠️ Локальный расчет завершен, но не удалось отправить файл на GitHub. Проверьте GITHUB_TOKEN или настройки сети.")

# =========================================================================
# БЛОК 8 — ТЕХНОЛОГИЧЕСКИЙ ЖУРНАЛ КОРРЕКЦИИ ТРАЕКТОРИИ
# =========================================================================
st.markdown("---")
st.markdown("### 📋 Блок 8: Журнал технологических рекомендаций")

if "trajectory_history" not in st.session_state:
    st.session_state.trajectory_history = []

if st.button("💾 Зафиксировать текущую рекомендацию в журнал рейса", use_container_width=True):
    time_stamp = time.strftime("%H:%M:%S")
    st.session_state.trajectory_history.append({
        "Время": time_stamp,
        "Скважина": well_name,
        "Прогноз MD (м)": round(forecast_md, 1),
        "Реком. Слайд (м)": round(required_slide_meters, 1),
        "Реком. Ротор (м)": round(required_rotary_meters, 1),
        "Прогноз DLS (°/10м)": round(forecast_dls_val, 2),
        "Коммерческий риск": "🚨 ШТРАФ" if consecutive_violations >= 3 else "⚠️ РИСК" if consecutive_violations > 0 else "🟢 НОРМА"
    })
    st.success(f"Рекомендация для скважины {well_name} успешно зафиксирована в журнал рейса!")

if st.session_state.trajectory_history:
    df_history = pd.DataFrame(st.session_state.trajectory_history)
    st.dataframe(df_history, use_container_width=True, hide_index=True)
    
    # Скачивание лога в формате TXT
    log_out = "ПРОТОКОЛ ТЕХНОЛОГИЧЕСКОГО ПЛАНИРОВАНИЯ ТРАЕКТОРИИ:\n" + "\n".join([
        f"[{r['Время']}] Скв: {r['Скважина']} | Слайд: {r['Реком. Слайд (м)']}м | Ротор: {r['Реком. Ротор (м)']}м | Статус: {r['Коммерческий риск']}"
        for r in st.session_state.trajectory_history
    ])
    st.download_button("📥 Экспортировать суточный рапорт траектории (.txt)", data=log_out, file_name=f"Trajectory_Report_{well_name}.txt", use_container_width=True)
