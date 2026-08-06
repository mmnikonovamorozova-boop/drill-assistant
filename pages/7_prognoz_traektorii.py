import json
import base64
import requests
import numpy as np
import pandas as pd
import streamlit as st
import time
from scipy.interpolate import CubicSpline

# =========================================================================
# ИНИЦИАЛИЗАЦИЯ И ИНТЕГРАЦИЯ БАЗЫ САМООБУЧЕНИЯ ИЗ REPOSITORY
# =========================================================================

@st.cache_data(ttl=600)
def load_calibrations_from_github():
    """Удаленно считывает архив калибровок траектории с GitHub API"""
    REPO_OWNER = "mmnikonovamorozova-boop"
    REPO_NAME = "drill-assistant"
    FILE_PATH = "calibrations_db.json"
    
    token = st.secrets.get("GITHUB_TOKEN", None)
    url = "https://github.com"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    default_coefficients = {
        "slide_factor": 1.0,          
        "intensity_correction": 1.0,  
        "rotary_drift_val": 0.0,      
        "info": "Используются заводские уставки (база калибровок пуста)"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            file_info = response.json()
            content_str = base64.b64decode(file_info["content"]).decode("utf-8")
            calibrations_list = json.loads(content_str)
            
            if isinstance(calibrations_list, list) and len(calibrations_list) > 0:
                last_point = calibrations_list[-1]
                last_point["info"] = f"Успешно загружено! Актуально на основе скважины {last_point.get('well', 'Н/Д')}"
                return last_point
    except:
        pass
        
    return default_coefficients

# Загружаем адаптивные веса из GitHub
active_calibration = load_calibrations_from_github()

# =========================================================================
# БОКОВАЯ ПАНЕЛЬ И НАСТРОЙКИ СТРАНИЦЫ
# =========================================================================
st.sidebar.markdown(f"🤖 **Статус ядра:** {active_calibration['info']}")

# Глобальные константы и параметры КНБК
base_ani = st.sidebar.number_input("Базовая анизотропия породы:", value=0.05, step=0.01)
knbc_type = st.sidebar.selectbox("Конфигурация КНБК:", ["Стандартная безориентируемая", "Маятниковая", "Стабилизирующая"])
target_angle = st.sidebar.number_input("Текущий зенитный угол скважины, °:", min_value=0.0, max_value=90.0, value=45.0)

# Гидродинамические параметры для поправок
buoyancy_factor = st.sidebar.number_input("Коэффициент плавучести (мультипликатор):", value=0.85, step=0.01)
yield_stress = st.sidebar.number_input("ДНС бурового раствора, дПа:", value=40.0)
flow_index = st.sidebar.number_input("Индекс течения раствора (n):", value=0.7, step=0.05)
target_wob = st.sidebar.number_input("Нагрузка на долото (G_wob), т:", value=15.0)

# Ограничения зон ГНО
gno_zone = st.sidebar.checkbox("Учитывать зоны ГНО/Опасность желобообразования", value=False)
gno_zone_limit = st.sidebar.number_input("Предел интенсивности в ГНО, град/10м:", value=1.0)
max_allowed_dls = st.sidebar.number_input("Макс. допустимая интенсивность по ТЗ:", value=2.5)

# =========================================================================
# БЛОК 1: СВЕРКА ДАННЫХ И ИНТЕРПОЛЯЦИЯ ИНКЛИНОМЕТРИИ
# =========================================================================
st.markdown("### 🗂 Блок 1: Сверка пространственных данных")
well_name = st.text_input("📝 Номер/Название скважины:", value="101-Г")

# Таблица замеров инклинометрии рейса
data_inc = {
    "Глубина (м)": [1000.0, 1030.0, 1060.0, 1090.0],
    "Зенитный угол (°)": [42.1, 43.5, 44.8, 45.0],
}
df_inc = pd.DataFrame(data_inc)
st.dataframe(df_inc, use_container_width=True)

# Математическая интерполяция траектории кубическими сплайнами (scipy)
try:
    md_points = df_inc["Глубина (м)"].values
    inc_points = df_inc["Зенитный угол (°)"].values
    cs_inc = CubicSpline(md_points, inc_points, extrapolate=True)
except Exception as e:
    st.warning(f"Ошибка калибровки сплайнов траектории: {e}")

# =========================================================================
# БЛОК 2 И 3: РАСЧЕТ ПРОСТРАНСТВЕННОЙ ИНТЕНСИВНОСТИ (DLS)
# =========================================================================
st.markdown("### 📈 Блок 2 и 3: Пространственная интенсивность и увод")

col_b2_1, col_b2_2 = st.columns(2)
with col_b2_1:
    planned_slide = st.number_input("Запланировано СЛАЙДА на следующем интервале, м:", min_value=0.0, value=9.0)
    k_slide_current = st.number_input("Рабочий коэффициент слайда (K_slide):", 
                                      value=float(active_calibration["slide_factor"]), step=0.01)
with col_b2_2:
    planned_rotary = st.number_input("Запланировано РОТОРА на следующем интервале, м:", min_value=0.0, value=21.0)
    drift_current = st.number_input("Естественный увод в роторе, град/10м:", 
                                    value=float(active_calibration["rotary_drift_val"]), step=0.01)

target_intensity = st.number_input("Проектная интенсивность КНБК, град/10м:", min_value=0.0, value=1.2)
k_int_current = st.number_input("Коэффициент коррекции интенсивности:", 
                                value=float(active_calibration["intensity_correction"]), step=0.01)

# Физическая модель расчета прогнозируемого изменения зенитного угла КНБК
actual_slide_work = planned_slide * k_slide_current
predicted_angle_gain_slide = (actual_slide_work / 10.0) * (target_intensity * k_int_current)
predicted_angle_gain_rotary = (planned_rotary / 10.0) * drift_current

total_predicted_angle_gain = predicted_angle_gain_slide + predicted_angle_gain_rotary
st.metric("Прогнозное изменение зенитного угла на интервале КНБК:", f"{total_predicted_angle_gain:.2f} °")

# =========================================================================
# БЛОК 4: РАСЧЕТ ИНТЕНСИВНОСТИ И МЕТРАЖА СЛАЙДА (СТР. 11 МЕТОДИЧКИ)
# =========================================================================
st.markdown("---")
st.subheader("📝 Блок 4: Расчет проходки в режиме «Слайд»")
col_sl_s1, col_sl_s2 = st.columns(2)

with col_sl_s1:
    dls_needed = st.number_input("Интенсивность, которую нужно получить (И), °:", min_value=0.1, max_value=5.0, value=1.5)
with col_sl_s2:
    ppi_last = st.number_input("Полученная интенсивность на последнем замере (ППИ), °:", min_value=0.1, max_value=5.0, value=0.6)
    kms_last = st.number_input("Количество метров слайда на последнем замере (КМС), м:", min_value=1.0, max_value=30.0, value=5.0)

# Применяем коэффициент коррекции интенсивности из базы самообучения
k_int_learned = float(active_calibration.get("intensity_correction", 1.0))

if st.button("📊 Рассчитать параметры прогноза на забой", type="secondary"):
    dls_per_meter = (ppi_last / kms_last) * k_int_learned
    slide_length_needed = dls_needed / dls_per_meter if dls_per_meter > 0 else 0.0
    st.write(f"📈 Необходимый метраж слайда: **{slide_length_needed:.2f} м**")
    
    t_theta_rad = np.radians(target_angle)
    L_m = 3.8 if "Стабилизирующая" in knbc_type else (18.0 if "Маятниковая" in knbc_type else 9.0)
    rheology_modifier = buoyancy_factor * (1.0 - (yield_stress / 1000.0) * (1.0 - flow_index))
    
    if "Маятниковая" in knbc_type:
        P_b = -150.0 * np.sin(t_theta_rad) * L_m * rheology_modifier
    elif "Стабилизирующая" in knbc_type:
        P_b = 80.0 * (target_wob / L_m) * np.cos(t_theta_rad) * buoyancy_factor
    else:
        P_b = ((50.0 * (target_wob / L_m) * np.cos(t_theta_rad)) - (70.0 * np.sin(t_theta_rad) * L_m)) * rheology_modifier
        
    rotary_drift_learned = float(active_calibration.get("rotary_drift_val", 0.0))
    current_ani_rate = st.session_state.get('calibrated_ani', base_ani)
    predicted_dls_10m = (abs(P_b * current_ani_rate) / 400.0) + rotary_drift_learned
    current_limit = gno_zone_limit if gno_zone else max_allowed_dls
    
    st.write(f"📉 Прогнозная пространственная интенсивность на 10м бурения: **{predicted_dls_10m:.2f} °**")

# =========================================================================
# ПОДБЛОК 5: БЛОК САМООБУЧЕНИЯ (ОБРАТНАЯ СВЯЗЬ И КЛИЕНТ GITHUB API)
# =========================================================================
st.markdown("---")
st.markdown("### 🧠 Блок динамического самообучения системы (Адаптация траектории)")
st.caption("Введите фактические параметры замера инклинометрии после бурения интервала для калибровки математического ядра.")

col_learn1, col_learn2 = st.columns(2)
with col_learn1:
    actual_angle_gain = st.number_input("Фактическое изменение зенитного угла по MWD (факт), °:", value=1.15)
with col_learn2:
    current_well = st.text_input("Имя текущей скважины для лога калибровки:", value="102-Г")

def push_calibration_to_github(new_data):
    REPO_OWNER = "mmnikonovamorozova-boop"
    REPO_NAME = "drill-assistant"
    FILE_PATH = "calibrations_db.json"
    
    token = st.secrets.get("GITHUB_TOKEN", None)
    if not token:
        st.error("🚨 В настройках Streamlit Cloud (Secrets) отсутствует GITHUB_TOKEN! Запись невозможна.")
        return False

    url = f"https://github.com{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        res = requests.get(url, headers=headers)
        sha = None
        current_list = []
        
        if res.status_code == 200:
            file_info = res.json()
            sha = file_info["sha"]
            old_str = base64.b64decode(file_info["content"]).decode("utf-8")
            try:
                current_list = json.loads(old_str)
                if not isinstance(current_list, list): current_list = []
            except: pass

        current_list.append(new_data)
        updated_json_str = json.dumps(current_list, indent=4, ensure_ascii=False)
        encoded_content = base64.b64encode(updated_json_str.encode("utf-8")).decode("utf-8")

        commit_payload = {
            "message": f"🤖 Самообучение ядра траектории: Скважина {new_data['well']}",
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            commit_payload["sha"] = sha

        put_res = requests.put(url, headers=headers, json=commit_payload)
        
            if put_res.status_code == 200 or put_res.status_code == 201:
            st.success("🎉 Математическое ядро успешно обучено! Свежие коэффициенты записаны на GitHub.")
            st.cache_data.clear()
            return True
        else:
            st.error(f"Ошибка удаленной записи на GitHub API: {put_res.status_code} - {put_res.text}")
    except Exception as err:
        st.error(f"Сбой отправки данных предиктивного анализа: {err}")
    return False

if st.button("🔄 Запустить самообучение системы и обновить коэффициенты в репозитории", type="primary"):
    with st.spinner("Вычисляется невязка и шаг фильтрации Калмана..."):
        pred_gain = total_predicted_angle_gain if 'total_predicted_angle_gain' in locals() else 0.0
        error_delta = actual_angle_gain - pred_gain
        learning_rate = 0.12
        
        base_slide = float(active_calibration.get("slide_factor", 1.0))
        base_drift = float(active_calibration.get("rotary_drift_val", 0.0))
        base_int = float(active_calibration.get("intensity_correction", 1.0))
        
        if 'kms_last' in locals() and kms_last > 10.0:
            new_slide_factor = base_slide + (error_delta * learning_rate)
            new_rotary_drift = base_drift
        else:
            new_slide_factor = base_slide
            new_rotary_drift = base_drift + (error_delta * learning_rate)
            
        new_point_to_save = {
            "date": time.strftime("%Y-%m-%d %H:%M"),
            "well": current_well,
            "slide_factor": round(float(new_slide_factor), 3),
            "intensity_correction": round(float(base_int), 3),
            "rotary_drift_val": round(float(new_rotary_drift), 3),
            "unbalance_deg": round(float(error_delta), 2)
        }
        
        push_calibration_to_github(new_point_to_save)
