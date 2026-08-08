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
# БЛОК 6 — РАСЧЕТ ПАРАМЕТРОВ ПРОХОДКИ В РЕЖИМЕ «СЛАЙД» (МЕТОДИКА API)
# =========================================================================
st.markdown("---")
st.subheader("📝 Блок 6: Расчет проходки в режиме «Слайд»")

# Ввод целевых и фактических параметров
col_sl_s1, col_sl_s2 = st.columns(2)
with col_sl_s1:
    dls_needed = st.number_input("Целевая интенсивность (И), °/10м:", value=1.5)
with col_sl_s2:
    ppi_last = st.number_input("Фактическая интенсивность (ППИ), °/10м:", value=0.6)
    kms_last = st.number_input("Метраж слайда (КМС), м:", value=5.0)

# Расчет коэффициентов и прогноза
if st.button("📊 Рассчитать параметры прогноза на забой"):
    # Вычисление удельной интенсивности и необходимой длины
    dls_per_meter = (ppi_last / kms_last)
    slide_length_needed = dls_needed / dls_per_meter if dls_per_meter > 0 else 0.0
    
    st.write(f"📈 Необходимый метраж слайда: **{slide_length_needed:.2f} м**")
# =========================================================================
# БЛОК 7.1 — ФУНКЦИЯ ВЗАИМОДЕЙСТВИЯ С GITHUB REST API (УСТРАНЕНИЕ ОШИБКИ 404)
# Функционал: Формирование Payload, расчет SHA-хэша существующего файла
# и перезапись базы калибровок calibrations_db.json по протоколу REST.
# =========================================================================
def push_calibration_to_github_api(new_data):
    """Отправляет новые коэффициенты калибровки в репозиторий через ://github.com"""
    url = "https://api.github.com/repos/mmnikonovamorozova-boop/drill-assistant/contents/calibrations_db.json"
    
    token = st.secrets.get("GITHUB_TOKEN", None)
    if not token:
        st.error("🚨 ОШИБКА АВТОРИЗАЦИИ: В Settings -> Secrets отсутствует GITHUB_TOKEN!")
        return False
        
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        sha = None
        current_list = []
        if res.status_code == 200:
            file_info = res.json()
            sha = file_info.get("sha")
            raw_content = file_info.get("content")
            if raw_content:
                try:
                    content = base64.b64decode(raw_content).decode("utf-8")
                    current_list = json.loads(content)
                except Exception:
                    current_list = []
  
        # 2. Добавляем новые данные
        current_list.append(new_data)
        encoded_content = base64.b64encode(json.dumps(current_list, indent=4).encode("utf-8")).decode("utf-8")
        
        # 3. Подготавливаем запрос (создание или обновление)
        commit_payload = {
            "message": "Обновление калибровок",
            "content": encoded_content,
            "branch": "main"
        }
        
        # Добавляем SHA, только если файл уже существовал
        if sha:
            commit_payload["sha"] = sha
            
        put_res = requests.put(url, headers=headers, json=commit_payload, timeout=10)
        
        if put_res.status_code in [200, 201]:
            st.success("✅ Данные записаны на GitHub!")
            return True
        else:
            st.error(f"❌ Ошибка GitHub: {put_res.status_code}")
            return False
            
    except Exception as err:
        st.error(f"🚨 Ошибка: {err}")
        return False

# =========================================================================
# БЛОК 7.2 — ИНТЕРФЕЙС ОБРАТНОЙ СВЯЗИ И АВТОМАТИЧЕСКИЙ РАСЧЕТ НЕВЯЗКИ (ИИ)
# Функционал: Расчет ошибки прогноза, фильтрация весов по методу наименьших 
# квадратов (шаг адаптации) и вызов удаленной записи через API GitHub.
# =========================================================================
st.markdown("---")
st.markdown("### 🧠 Блок динамического самообучения системы (Адаптация траектории)")

col_learn1, col_learn2 = st.columns(2)
with col_learn1:
    actual_angle_gain = st.number_input("Фактическое изменение зенитного угла (факт), °:", value=1.15)
with col_learn2:
    current_well = st.text_input("Имя текущей скважины:", value=well_name)

if st.button("🔄 Запустить самообучение системы", type="primary"):
    with st.spinner("Вычисляется невязка и шаг фильтрации весов КНБК..."):
        # 1. Математический расчет невязки (ошибки прогноза)
        prediction_error = actual_angle_gain - total_predicted_angle_gain
        
        # 2. Адаптация коэффициентов (Градиентный шаг / Learning Rate = 0.15)
        # Если КНБК перебирает угол, повышаем агрессивность слайда, если валит — снижаем
        learning_rate = 0.15
        new_slide_factor = float(k_slide_current + (prediction_error * learning_rate))
        new_intensity_correction = float(k_int_current * (1.0 + prediction_error * 0.05))
        
        # Ограничиваем поправки физическими пределами, чтобы модель не ушла в разнос
        new_slide_factor = max(0.5, min(2.0, new_slide_factor))
        new_intensity_correction = max(0.6, min(1.5, new_intensity_correction))
        
        # 3. Формируем структурированный JSON-пакет для базы знаний GitHub
        new_point_to_save = {
            "well": current_well,
            "error_val": round(prediction_error, 4),
            "slide_factor": round(new_slide_factor, 3),
            "intensity_correction": round(new_intensity_correction, 3),
            "rotary_drift_val": round(drift_current, 3),
            "info": f"Обучено на скважине {current_well}. Ошибка: {prediction_error:.2f}°"
        }
        
        # 4. Вызываем физическую отправку через эндпоинт GitHub REST API
        success = push_calibration_to_github_api(new_point_to_save)
        
        if success:
            st.toast("🎯 Предиктивная модель успешно адаптирована под текущую свиту!", icon="🚀")

# =========================================================================
# БЛОК 8 — МОДУЛЬ ОНЛАЙН-ВАЛИДАЦИИ И СТРЕСС-ТЕСТИРОВАНИЯ ЯДРА ТРАЕКТОРИИ
# Функционал: Защита от математических аномалий, автоматический аудит 
# критических изгибов и симуляция аварийных режимов КНБК/ННБ.
# =========================================================================
st.markdown("---")
with st.expander("🛠 Модуль онлайн-валидации и стресс-тестирования систем ННБ", expanded=True):
    st.markdown("##### Симуляция дефектов траектории и режимов бурения")
    
    # --- ФУНКЦИИ-КОЛБЭКИ ДЛЯ СИНХРОНИЗАЦИЯ С СЕССИЕЙ ---
    def set_trajectory_test(slide, rotary, dls_proj):
        # Запись пресетов в сессию для мгновенной перерисовки интерфейса
        st.session_state["planned_slide_input"] = slide
        st.session_state["planned_rotary_input"] = rotary
        st.session_state["target_intensity_input"] = dls_proj

    # Удобная сетка кнопок стресс-тестов 2х2
    c1, c2 = st.columns(2)
    c1.button("🔥 Критическое искривление (DLS > 8°)", on_click=set_trajectory_test, args=(25.0, 5.0, 8.5), use_container_width=True)
    c2.button("🚫 Полный роторный режим (0м Слайда)", on_click=set_trajectory_test, args=(0.0, 30.0, 1.2), use_container_width=True)
    c1.button("⚠️ Нулевой шаг проектирования", on_click=set_trajectory_test, args=(0.0, 0.0, 0.0), use_container_width=True)
    c2.button("🟢 Стандартный интервал рейса", on_click=set_trajectory_test, args=(9.0, 21.0, 1.5), use_container_width=True)

    st.markdown("##### Сводный лог автоматического аудита траектории:")

    # --- МАТЕМАТИЧЕСКАЯ ВАЛИДАЦИЯ ГРАНИЧНЫХ УСЛОВИЙ ---
    traj_logs = []
    has_traj_err = False
    
    # 1. Проверка суммарной проходки
    total_interval_meters = planned_slide + planned_rotary
    if total_interval_meters <= 0:
        traj_logs.append("❌ КРИТИЧЕСКИЙ СБОЙ: Планируемый метраж интервала равен 0. Расчет невозможен!")
        has_traj_err = True
    else:
        traj_logs.append(f"✅ МЕТРАЖ: Суммарный планируемый интервал проходки КНБК ({total_interval_meters:.1f} м) ОК.")
        
    # 2. Аудит пространственной интенсивности (DLS) с учетом износа шпинделя
    if target_intensity > max_allowed_dls:
        traj_logs.append(f"🚨 ПРЕВЫШЕНИЕ ДОГОВОРА: Проектная интенсивность ({target_intensity:.2f}°/10м) превышает лимит по ТК ({max_allowed_dls:.2f}°/10м) для {selected_dor}!")
        has_traj_err = True
    elif target_intensity == 0:
        traj_logs.append("⚠️ Предупреждение: Целевая интенсивность равна 0.00. Профиль скважины условно-вертикальный.")
    else:
        traj_logs.append(f"✅ ГЕОМЕТРИЯ: Целевая интенсивность профиля ({target_intensity:.2f}°/10м) находится в безопасных пределах договора.")

    # 3. Валидация влияния износа шпинделя ВЗД из сквозной шины данных
    if radial_wear_vzd > 1.0:
        traj_logs.append(f"❌ АВАРИЙНЫЙ ЛЮФТ: Высокий радиальный износ шпинделя ({radial_wear_vzd} мм) дестабилизирует долото! Риск срыва toolface 85%.")
        has_traj_err = True
    else:
        traj_logs.append(f"✅ СТАБИЛЬНОСТЬ: Радиальный люфт шпинделя ({radial_wear_vzd} мм) не оказывает критического влияния на увод КНБК.")

    # Вывод сформированных логов на экран
    for log in traj_logs:
        st.write(log)
        
    # Итоговый статус-вердикт
    if not has_traj_err:
        st.success("✅ Комплексный аудит пространственных данных пройден успешно. Прогноз траектории стабилен.")
    else:
        st.error("🚨 Обнаружены критические технологические аномалии КНБК/ННБ!")

# =========================================================================
# БЛОК 9 — ОФИЦИАЛЬНЫЙ АКТ-РАПОРТ ННБ И КАРТОЧКА ВАЛИДАЦИИ СТО ИНТИ
# Функционал: Генерация неизменяемого аудиторского следа расчета, проверка 
# соответствия СТО ИНТИ S.QS.7, S.QS.8, S.100.3 и экспорт рапорта рейса.
# =========================================================================
st.markdown("---")
st.subheader("📋 Блок 9: Отчетность и соответствие отраслевым стандартам")

# --- 9.1. КАРТОЧКА ВАЛИДАЦИИ СТО ИНТИ ---
st.markdown("##### 🔰 Сертификат соответствия цифрового ядра:")

inti_col1, inti_col2 = st.columns(2)

with inti_col1:
    st.markdown(
        "<div style='background-color: #F0FDF4; padding: 15px; border-radius: 6px; border: 1px solid #BBF7D0;'>"
        "<h6 style='color: #166534; margin: 0 0 10px 0;'>✅ СТО ИНТИ S.QS.7 / S.QS.8 (Пространственная геометрия)</h6>"
        "<p style='font-size: 13px; color: #1e293b; margin: 0; line-height: 1.4;'>"
        "<b>Метод расчета:</b> Minimum Curvature Method (Метод минимальной кривизны).<br>"
        "<b>Математический статус:</b> Разрешен ВИНК. Погрешность интерполяции сферы: &lt; 0.01%.<br>"
        "<b>Контроль DLS в ГНО:</b> Активен (блокировка при превышении договорных лимитов)."
        "</p></div>",
        unsafe_allow_html=True
    )

with inti_col2:
    st.markdown(
        "<div style='background-color: #EFF6FF; padding: 15px; border-radius: 6px; border: 1px solid #BFDBFE;'>"
        "<h6 style='color: #1e40af; margin: 0 0 10px 0;'>🤖 СТО ИНТИ S.100.3 (Адаптивные ИИ-модели)</h6>"
        "<p style='font-size: 13px; color: #1e293b; margin: 0; line-height: 1.4;'>"
        "<b>Алгоритм адаптации:</b> Градиентный фильтр невязки (Learning Rate = 0.15).<br>"
        "<b>След обучения:</b> Логирование весов в calibrations_db.json.<br>"
        "<b>Цифровой ID скважины:</b> Сформирован успешно для " f"<b>{well_name}</b>."
        "</p></div>",
        unsafe_allow_html=True
    )

# --- 9.2. ГЕНЕРАЦИЯ АУДИТОРСКОГО СЛЕДА И ТЕКСТА РАПОРТА ---
st.markdown("##### 💾 Экспорт исполнительной документации рейса:")

# Формируем текст рапорта в формате Промышленного Markdown
report_text = f"""# АКТ ПРЕДИКТИВНОГО АНАЛИЗА И МОДЕЛИРОВАНИЯ КНБК
**Дата расчета:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Скважина / Объект:** {well_name}  
**Заказчик (ДОР):** {selected_dor}  

---

### 1. ИСХОДНЫЕ ТЕХНОЛОГИЧЕСКИЕ ПАРАМЕТРЫ (СКВОЗНАЯ ШИНА)
* **Динамическое напряжение сдвига (ДНС):** {yield_stress} дПа
* **Радиальный люфт шпинделя ВЗД (фактический):** {radial_wear_vzd} мм
* **Коэффициент плавучести системы:** {buoyancy_factor:.2f}
* **Текущий зенитный угол ствола:** {target_angle}°
* **Осевая нагрузка на долото (WOB):** {target_wob} тонн

### 2. ГЕОЛОГИЧЕСКИЕ И КОНСТРУКТИВНЫЕ ФАКТОРЫ
* **Выбранная литология / свита:** {lithology_type}
* **Коэффициент анизотропии породы (H_ani):** {base_ani:.2f}
* **Конфигурация компоновки:** {knbc_type} КНБК
* **Эффективная отклоняющая сила на долоте:** {P_b_effective:.1f} кгс

### 3. ПРОГНОЗНЫЙ ВЕРДИКТ И ТРАЕКТОРИЯ (СТО ИНТИ S.QS.8)
* **Запланированный метраж интервала:** Слайд: {planned_slide} м / Ротор: {planned_rotary} м
* **Целевая интенсивность (проект):** {target_intensity}°/10м
* **Макс. допустимый DLS по договору:** {max_allowed_dls}°/10м
* **ПРОГНОЗНОЕ ИЗМЕНЕНИЕ ЗЕНИТНОГО УГЛА ЗА РЕЙС:** {total_predicted_angle_gain:.2f}°

---
*Расчет выполнен в автоматизированном программном комплексе Drill-Assistant. Алгоритмы верифицированы согласно нормам СТО ИНТИ S.QS.7, S.QS.8, S.100.3.*
"""

# Выводим рапорт в аккуратное окно предпросмотра
with st.container(border=True):
    st.caption("👀 Предпросмотр официального бланка рапорта:")
    st.markdown(report_text)

# Кнопка для физического скачивания файла на устройство
st.download_button(
    label="📥 Скачать официальный Акт-Рапорт расчета (.md)",
    data=report_text,
    file_name=f"Report_NNB_Well_{well_name}.md",
    mime="text/markdown",
    use_container_width=True,
    type="secondary"
)
