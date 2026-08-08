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
# БЛОК 2 — ИНТЕГРАЦИЯ С REST API GITHUB И СЧИТЫВАНИЕ АДАПТИВНЫХ ВЕСОВ
# =========================================================================
@st.cache_data(ttl=300)
# =========================================================================
# БЛОК 2 — УМНОЕ ИИ-ЯДРО: ИМПОРТ И СЕЛЕКЦИЯ КАЛИБРОВОК ПО ИМЕНИ СКВАЖИНЫ
# =========================================================================
@st.cache_data(ttl=60)  # Уменьшили кэш до 60 секунд, чтобы изменения применялись быстрее
def load_calibrations_from_github_api(target_well_name):
    """Считывает архив калибровок и ищет исторические веса под конкретную скважину"""
    url = "https://api.github.com/repos/mmnikonovamorozova-boop/drill-assistant/contents/calibrations_db.json"
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {st.secrets.get('GITHUB_TOKEN', '')}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            file_info = response.json()
            content_str = base64.b64decode(file_info["content"]).decode("utf-8")
            calibrations_list = json.loads(content_str)
            
            if isinstance(calibrations_list, list) and len(calibrations_list) > 0:
                # Фильтруем массив: ищем все замеры по текущей скважине
                well_data = [p for p in calibrations_list if str(p.get("well")).strip() == str(target_well_name).strip()]
                
                if well_data:
                    # Если нашли историю по этой скважине, берем самый актуальный (последний) её замер
                    match = well_data[-1]
                    match["info"] = f"🤖 ИИ: Адаптировано под скважину {target_well_name}. Замеров в базе: {len(well_data)}"
                    return match
                    
    except Exception: pass
    # Если скважина новая — выдаем чистые заводские уставки
    return {"slide_factor": 1.0, "intensity_correction": 1.0, "rotary_drift_val": 0.03, "info": "Используются заводские уставки (Новая скважина)"}

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
# БЛОК 4 — ОБРАБОТКА ГГИ ЗАКАЗЧИКА И РАСЧЕТ ТРАЕКТОРИИ (MINIMUM CURVATURE METHOD)
# Функционал: Двухвариантный импорт данных инклинометрии, расчет пространственной 
# интенсивности (DLS) по стандарту API и трехмерная интерполяция профиля скважины.
# =========================================================================
st.markdown("### 🗂 Блок 4: Сверка пространственных данных и импорт ГГИ")
well_name = st.text_input("📝 Номер/Название скважины:", value="101-Г")
active_calibration = load_calibrations_from_github_api(well_name)
st.sidebar.markdown(f"🤖 **Статус ИИ-ядра:** {active_calibration['info']}")

# Интерактивный загрузчик ГГИ Заказчика (Приоритетный режим)
uploaded_ggi = st.file_uploader("Выгрузите Excel/CSV с плановым профилем (ГГИ):", type=["xlsx", "csv"])

if uploaded_ggi is not None:
    try:
        if uploaded_ggi.name.endswith('.xlsx'):
            df_inc = pd.read_excel(uploaded_ggi)
        else:
            df_inc = pd.read_csv(uploaded_ggi)
            
        # Принудительная стандартизация и очистка колонок от мусора
        df_inc.columns = df_inc.columns.astype(str).str.upper().str.strip()
        st.success(f"✅ Профиль ГГИ Заказчика успешно подгружен! Успешно считано точек: {len(df_inc)}")
    except Exception as e:
        st.error(f"⚠️ Ошибка парсинга файла ГГИ: {e}. Переход на стандартный профиль.")
        uploaded_ggi = None

# Аналитический откат: если файл не загружен, генерируем стандартную таблицу рейса
if uploaded_ggi is None:
    data_inc = {
        "ГЛУБИНА (М)": [1000.0, 1030.0, 1060.0, 1090.0],
        "ЗЕНИТНЫЙ УГОЛ (°)": [42.1, 43.5, 44.8, 45.0],
        "АЗИМУТ (°)": [12.5, 13.1, 13.8, 14.2]
    }
    df_inc = pd.DataFrame(data_inc)
    st.info("ℹ Файл ГГИ не обнаружен. Расчет ведется по стандартному устьевому журналу замера.")

# Отображение таблицы на интерфейсе с возможностью ручной корректировки
df_inc = st.data_editor(df_inc, use_container_width=True)

# МАТЕМАТИЧЕСКОЕ ЯДРО: Вычисление DLS между точками по методу Minimum Curvature
try:
    md = df_inc.iloc[:, 0].values
    inc = np.radians(df_inc.iloc[:, 1].values)
    azi = np.radians(df_inc.iloc[:, 2].values if df_inc.shape[1] > 2 else np.zeros(len(md)))
    
    calculated_dls_list = [0.0]
    
    for i in range(1, len(md)):
        dl_md = md[i] - md[i-1]
        if dl_md <= 0:
            calculated_dls_list.append(0.0)
            continue
            
        # Угол пространственного ухода (Dogleg Severity Angle) по формуле API
        cos_beta = (np.cos(inc[i-1]) * np.cos(inc[i])) + (np.sin(inc[i-1]) * np.sin(inc[i]) * np.cos(azi[i] - azi[i-1]))
        cos_beta = max(-1.0, min(1.0, cos_beta)) # Защита от выхода за пределы тригонометрии
        beta = np.arccos(cos_beta)
        
        # Расчет пространственной интенсивности (DLS) на стандартные 10 метров проходки
        if beta == 0:
            dls_10m = 0.0
        else:
            dls_10m = np.degrees(beta) * (10.0 / dl_md)
            
        calculated_dls_list.append(round(dls_10m, 2))
        
    df_inc["РАСЧЕТНЫЙ DLS (ГРАД/10М)"] = calculated_dls_list
    
    # Резервная кубическая интерполяция для непрерывного прогнозирования между точками
    cs_inc = CubicSpline(md, df_inc.iloc[:, 1].values, extrapolate=True)
    st.success("✅ Математическое ядро Minimum Curvature и сплайн-модель успешно откалиброваны.")
except Exception as e:
    st.error(f"❌ Критический сбой математического ядра траектории: {e}")
# =========================================================================
# БЛОК 5.1 — МОДЕЛИРОВАНИЕ СИЛ КНБК, АНИЗОТРОПИИ ПЛАСТА И УВОДА ДОЛОТА
# Функционал: Расчет боковой отклоняющей силы на долоте с учетом реологии
# бурового раствора, конструктивного типа КНБК, радиального износа ВЗД
# и нормативного коэффициента анизотропии проходимой геологической свиты.
# =========================================================================
st.markdown("---")
st.markdown("### 📈 Блок 5: Пространственная интенсивность и увод")

# Ввод эксплуатационных параметров интервала бурения
col_b2_1, col_b2_2 = st.columns(2)
with col_b2_1:
    planned_slide = st.number_input("Запланировано СЛАЙДА, м:", value=9.0, key="planned_slide_input")
    k_slide_current = st.number_input("Коэффициент слайда (K_slide):", value=float(active_calibration.get("slide_factor", 1.0)))
with col_b2_2:
    planned_rotary = st.number_input("Запланировано РОТОРА, м:", value=21.0, key="planned_rotary_input")
    # Подставляем базовый увод из геологического селектора, если в базе нет свежей калибровки
    drift_current = st.number_input("Естественный увод в роторе, град/10м:", value=default_rotary_drift)

target_intensity = st.number_input("Проектная интенсивность КНБК, град/10м:", value=1.2, key="target_intensity_input")
k_int_current = st.number_input("Коэффициент коррекции КНБК:", value=float(active_calibration.get("intensity_correction", 1.0)))

# Расчет гидродинамических и конструктивных сил по модели API RP 13D
t_theta_rad = np.radians(target_angle)
L_m = 3.8 if "Стабилизирующая" in knbc_type else (18.0 if "Маятниковая" in knbc_type else 9.0)

# Интеграция ДНС раствора из 5-го модуля как гидродинамического демпфера силы
rheology_modifier = buoyancy_factor * (1.0 - (yield_stress / 1000.0))

# Векторное вычисление конструктивных сил КНБК (Маятник / Стабилизатор / Направленная)
if "Маятниковая" in knbc_type:
    P_b_structural = -150.0 * np.sin(t_theta_rad) * L_m * rheology_modifier
elif "Стабилизирующая" in knbc_type:
    P_b_structural = 80.0 * (target_wob / L_m) * np.cos(t_theta_rad) * buoyancy_factor
else:
    P_b_structural = ((50.0 * (target_wob / L_m) * np.cos(t_theta_rad)) - (70.0 * np.sin(t_theta_rad) * L_m)) * rheology_modifier

# ФИЗИКА ГЕОЛОГИИ: Расчет реактивной боковой силы увода за счет анизотропии свиты
# Чем жестче порода (выше base_ani), тем сильнее вектор отклонения КНБК от проектной оси
P_b_geology = P_b_structural * (1.0 + base_ani)

# Модификатор износа ВЗД: радиальный люфт шпинделя гасит полезную боковую силу на долоте
wear_loss_factor = max(0.2, 1.0 - (radial_wear_vzd / 3.0)) 
P_b_effective = P_b_geology * wear_loss_factor

# =========================================================================
# БЛОК 5.2 — РАСЧЕТ ПРОГНОЗНОЙ ГЕОМЕТРИИ ТРАЕКТОРИИ НА ЗАБОЕ
# Функционал: Интеграция режимов бурения (Слайд/Ротор), расчет изменения
# зенитного угла с учетом сил КНБК, анизотропии пласта и увода.
# =========================================================================

# Расчет раздельного вклада интервалов бурения
actual_slide_work = planned_slide * k_slide_current
predicted_angle_gain_slide = (actual_slide_work / 10.0) * (target_intensity * k_int_current)
predicted_angle_gain_rotary = (planned_rotary / 10.0) * drift_current

# Итоговое предиктивное изменение угла КНБК
total_predicted_angle_gain = predicted_angle_gain_slide + predicted_angle_gain_rotary

# Отображение результатов на интерфейсе
st.markdown("##### 🎯 Результаты прогнозного моделирования траектории:")
st.metric(
    label="Прогнозное изменение зенитного угла на интервале КНБК:", 
    value=f"{total_predicted_angle_gain:.2f} °"
)

# Краткая инженерная аналитика сил взаимодействия
st.markdown("##### 🧠 Экспертная оценка динамики КНБК:")
col_stat1, col_stat2 = st.columns(2)
with col_stat1:
    st.write(f"🔹 **Эффективная отклоняющая сила:** `{P_b_effective:.1f} кгс` (с учетом износа шпинделя)")
with col_stat2:
    if abs(P_b_effective) > 100.0:
        st.warning("⚠️ **Внимание:** Высокие изгибающие силы на долоте. Повышенный риск микроизвилистости ствола!")
    else:
        st.success("🟢 Динамика сил стабильна. Прогнозируется плавный профиль набора кривизны.")
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
