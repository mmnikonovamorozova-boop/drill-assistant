import json
import base64
import requests
import numpy as np
import pandas as pd
import streamlit as st

# =========================================================================
# ПОДБЛОК 1: ДИНАМИЧЕСКИЙ СЧЕТЧИК И ЗАГРУЗКА ИСТОРИИ ИЗ REPOSITORY
# =========================================================================

@st.cache_data(ttl=600)  # Кэшируем на 10 минут, чтобы не перегружать сеть
def load_calibrations_from_github():
    """Считывает массив сохраненных сессий обучения с GitHub API"""
    REPO_OWNER = "mmnikonovamorozova-boop"
    REPO_NAME = "drill-assistant"
    FILE_PATH = "calibrations_db.json"
    
    token = st.secrets.get("GITHUB_TOKEN", None)
    url = f"https://github.com{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # Дефолтные безопасные уставки математического ядра
    default_coefficients = {
        "slide_factor": 1.0,          # Коэффициент эффективности слайда
        "intensity_correction": 1.0,  # Корректировка проектной интенсивности
        "rotary_drift_val": 0.0,      # Роторный увод (градусов на 10 метров)
        "info": "Заводские уставки (База пуста)"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            file_info = response.json()
            content_str = base64.b64decode(file_info["content"]).decode("utf-8")
            calibrations_list = json.loads(content_str)
            
            # Если в базе есть записи, вытаскиваем самую последнюю по времени точку
            if isinstance(calibrations_list, list) and len(calibrations_list) > 0:
                last_point = calibrations_list[-1]
                last_point["info"] = f"Успешно загружено! Актуально на основе скважины {last_point.get('well', 'Н/Д')}"
                return last_point
    except:
        pass
        
    return default_coefficients

# Загружаем последнюю рабочую калибровку из GitHub
active_calibration = load_calibrations_from_github()

        if r.status_code == 200:
            content_json = r.json()
            file_content = base64.b64decode(content_json["content"]).decode("utf-8")
            st.sidebar.write(f"📄 Содержимое на GitHub: {file_content}")
            if not file_content.strip() or file_content.strip() == "[]":
                return [], content_json["sha"]
            return json.loads(file_content), content_json["sha"]
        return [], None
    except Exception as e:
        st.sidebar.error(f"Ошибка загрузки: {str(e)}")
        return [], None

def save_calibration_to_github(formation_name, calibrated_value, current_wob, current_angle):
    # Обновленная функция с логгированием в st.sidebar
    try:
        st.sidebar.write("🚀 Запуск сохранения...")
        # ... (код загрузки, подготовки данных и отправки)
        # put_r = requests.put(...)
        st.sidebar.write(f"📡 Статус PUT: {put_r.status_code}")
        
        if put_r.status_code in [200, 201]:
            st.toast("💾 Данные синхронизированы!", icon="🚀")
        else:
            st.sidebar.error(f"Ошибка GitHub: {put_r.status_code}")
            
    except Exception as e:
        st.sidebar.error(f"Сбой: {str(e)}")

st.title("📈 Модуль пространственной интенсивности (Регламент Р-ТС-12)")
st.caption("Адаптивный СМК-контроль траектории ствола ООО «Траектория-Сервис» на базе распределенного хранилища GitOps")

# ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ СЕССИИ (ЗАЩИТА ОТ ATTRIBUTEERROR)
if "calibrated_ani" not in st.session_state:
    st.session_state.calibrated_ani = 1.02
if "cloud_cache" not in st.session_state:
    st.session_state.cloud_cache = {}

# ==============================================================================
# СЕРВИСНЫЙ БЛОК GITOPS: РАБОТА С ВЕЧНОЙ БАЗОЙ ДАННЫХ НА GITHUB
# ==============================================================================
# Получение токена из секретов Streamlit Cloud
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

import base64
import json
import requests
import streamlit as st
from datetime import datetime

def load_all_calibrations_from_github():
    """Загружает БД через API, получая актуальный SHA."""
    try:
        api_url = "https://github.com"
        r = requests.get(api_url, headers=get_github_headers())
        if r.status_code == 200:
            content_json = r.json()
            file_content = base64.b64decode(content_json["content"]).decode("utf-8")
            if not file_content.strip():
                return [], content_json["sha"]
            return json.loads(file_content), content_json["sha"]
        return [], None
    except Exception as e:
        st.sidebar.error(f"Ошибка загрузки: {str(e)}")
        return [], None

def save_calibration_to_github(formation_name, calibrated_value, current_wob, current_angle):
    """Обновляет JSON, принудительно передавая SHA."""
    try:
        history, sha = load_all_calibrations_from_github()
        
        if not isinstance(history, list):
            history = []
            
        # Добавление данных
        history.append({
            "formation": str(formation_name),
            "calibrated_ani": float(calibrated_value),
            "wob": float(current_wob),
            "angle": float(current_angle),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Подготовка контента
        json_string = json.dumps(history, indent=2, ensure_ascii=False)
        encoded_content = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")
        
        # Отправка PUT-запроса
        target_url = "https://github.com"
        payload = {
            "message": f"СМК-Автокоммит: {formation_name}",
            "content": encoded_content,
            "branch": "main",
            "sha": sha
        }
        
        put_r = requests.put(target_url, headers=get_github_headers(), json=payload)
        
        # Надежная проверка без списков и скрытых символов
        if put_r.status_code == 200 or put_r.status_code == 201:
            st.toast("💾 Данные успешно синхронизированы с GitHub!", icon="🚀")
        else:
            st.sidebar.error(f"GitHub отклонил запись! Код: {put_r.status_code}")
            st.sidebar.write(put_r.json())
            
    except Exception as e:
        st.sidebar.error(f"Сбой контура сохранения: {str(e)}")

# ==============================================================================
# БЛОК 1: БАЗА НЕОДРОПОЛЬЗОВАТЕЛЕЙ (ШТРАФНЫЕ ЛИМИТЫ СМК)
# ==============================================================================
CLIENT_LIMITS = {
    "ПАО «НК «Роснефть»": {"max_dls": 2.5, "penalty_risk": "Высокий (Штраф за превышение DLS на свечу)", "gno_zone_limit": 1.2},
    "ПАО «Газпром нефть»": {"max_dls": 3.0, "penalty_risk": "Критический (Снижение суточной ставки бурения)", "gno_zone_limit": 1.5},
    "ПАО «ЛУКОЙЛ»": {"max_dls": 2.0, "penalty_risk": "Высокий (Запрет спуска хвостовика, отказ ОТК)", "gno_zone_limit": 1.0}
}

st.sidebar.header("🏢 Выбор Заказчика")
client = st.sidebar.selectbox("Выберите недропользователя:", list(CLIENT_LIMITS.keys()))
max_allowed_dls = CLIENT_LIMITS[client]["max_dls"]
gno_limit = CLIENT_LIMITS[client]["gno_zone_limit"]

st.info(f"📋 **Регламент Заказчика:** {client} | **Макс. допуск:** {max_allowed_dls}°/10м | **Лимит в зоне ГНО:** {gno_limit}°/10м")

# ==============================================================================
# БЛОК 2: УЛУЧШЕННЫЙ СМК-ФИЛЬТР С КОНТУРОМ «НОВАЯ СВИТА»
# ==============================================================================
config_path = os.path.join("config", "formations_config.json")
base_ani = 1.02
selected_formation = "Не выбрана"
lithology = "Не определена"

if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        geo_db = json.load(f)
        
        first_row = geo_db[0] if len(geo_db) > 0 else {}
        region_key = next((k for k in first_row.keys() if "регион" in k.lower()), "Регион")
        formation_key = next((k for k in first_row.keys() if "стратигр" in k.lower() or "свита" in k.lower() or "горизонт" in k.lower()), "Стратиграфиче")
        litho_key = next((k for k in first_row.keys() if "литолог" in k.lower() or "состав" in k.lower() or "тип" in k.lower()), "Типичная литолог")
        category_key = next((k for k in first_row.keys() if "категор" in k.lower() or "тверд" in k.lower() or "класс" in k.lower()), "Категория бури")

        selected_region = st.sidebar.selectbox("1. Регион бурения:", list(set([str(row.get(region_key, "Не указан")).strip() for row in geo_db if row.get(region_key)])))
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🎨 Фильтр визуального восприятия пласта:**")
        selected_rock = st.sidebar.selectbox("2. Какая порода на забое?", ["Все типы", "Пески / Песчаники", "Глины / Аргиллиты", "Известняки / Доломиты / Соли"])
        selected_hardness = st.sidebar.selectbox("3. Какая твердость пласта?", ["Все категории", "Мягкие (I-III)", "Средние (III-IV)", "Твердые / Хрупкие (V-VII)"])

        filtered_rows = [row for row in geo_db if str(row.get(region_key)).strip() == selected_region]
        if selected_rock != "Все типы":
            keyword = "песк" if "Пески" in selected_rock else ("глин" if "Глины" in selected_rock else "извест")
            filtered_rows = [r for r in filtered_rows if keyword in str(r.get(litho_key, "")).lower()]
        if selected_hardness != "Все категории":
            h_keyword = "мягк" if "Мягкие" in selected_hardness else ("средн" if "Средние" in selected_hardness else "тверд")
            filtered_rows = [r for r in filtered_rows if h_keyword in str(r.get(category_key, "")).lower() or h_keyword in str(r.get(litho_key, "")).lower()]

        display_formations = sorted(list(set([str(row.get(formation_key, "Не указана")).strip() for row in filtered_rows])))
        display_formations = [f for f in display_formations if f and f != "None" and f != "Не указана"]
        
        display_formations.append("➕ Своя свита (нет в списке)")

        st.sidebar.markdown("---")
        if display_formations:
            choice = st.sidebar.selectbox("🎯 Подходящий горизонт из Базы:", display_formations)
            
            if choice == "➕ Своя свита (нет в списке)":
                selected_formation = st.sidebar.text_input("Впишите название новой свиты:", "Малоизвестная свита")
                lithology = st.sidebar.text_input("Укажите её литологический состав:", "Литология не изучена")
                base_ani = 1.020
            else:
                selected_formation = choice
                current_data = next((row for row in geo_db if str(row.get(region_key)).strip() == selected_region and str(row.get(formation_key)).strip() == selected_formation), {})
                lithology = current_data.get(litho_key, "Данные отсутствуют")
                ani_str = str(current_data.get("Базовый I(H_an", "1.02"))
                try:
                    bounds = [float(x.strip()) for x in ani_str.split("-") if x.strip()]
                    base_ani = sum(bounds) / len(bounds) if bounds else 1.02
                except:
                    base_ani = 1.02

if selected_formation != "Не выбрана" and selected_formation not in st.session_state.cloud_cache:
    history_records, _ = load_all_calibrations_from_github()
    if history_records:
        matching_values = [r["calibrated_ani"] for r in history_records if str(r.get("formation", "")).strip().lower() == selected_formation.strip().lower()]
    else:
        matching_values = []
        
    if matching_values:
        mean_cloud_ani = float(np.mean(matching_values))
        st.session_state.cloud_cache[selected_formation] = mean_cloud_ani
        st.session_state.calibrated_ani = mean_cloud_ani
        st.sidebar.success(f"🤖 Найдено замеров на GitHub: {len(matching_values)}. Средний коэффициент: **{mean_cloud_ani:.3f}**")
    else:
        st.session_state.cloud_cache[selected_formation] = base_ani
        st.session_state.calibrated_ani = base_ani
        st.sidebar.info("🆕 Новая свита. Накопленный опыт в репозитории отсутствует.")

st.info(f"📋 **Текущий СМК-контур:** {selected_formation} | **Состав:** {lithology} | **Используемая анизотропия пласта:** {st.session_state.calibrated_ani:.3f}")
st.markdown("---")

# ==============================================================================
# КОНТУР ОБУЧЕНИЯ (ОБРАТНАЯ ЗАДАЧА)
# ==============================================================================
st.subheader("🔄 Контур обучения ядра (Обратная задача по ГГИ/ГТИ)")
st.caption("Введите фактические параметры последнего пробуренного интервала для калибровки и отправки в репозиторий")

col_ob1, col_ob2, col_ob3 = st.columns(3)
with col_ob1:
    fact_wob = st.number_input("Фактическая нагрузка на долото (т):", min_value=1.0, max_value=40.0, value=12.0)
with col_ob2:
    fact_angle = st.number_input("Фактический зенитный угол на интервале (°):", min_value=0.0, max_value=90.0, value=30.0)
with col_ob3:
    fact_dls = st.number_input("Фактическая полученная интенсивность (°/10м):", min_value=0.0, max_value=6.0, value=1.4)

# Находим кнопку обучения системы
# =========================================================================
# ПОДБЛОК 3: БЛОК САМООБУЧЕНИЯ (ОБРАТНАЯ СВЯЗЬ И ЗАПИСЬ НА GITHUB)
# =========================================================================
st.markdown("### 🧠 Блок самообучения системы (Адаптация ядра)")
st.caption("Введите фактические данные замера после бурения интервала для пересчета увода КНБК.")

col_learn1, col_learn2 = st.columns(2)
with col_learn1:
    actual_angle_gain = st.number_input("Фактическое изменение угла по телесистеме (факт), °:", value=1.15)
with col_learn2:
    current_well = st.text_input("Имя текущей скважины для фиксации лога:", value="102-Г")

def push_calibration_to_github(new_data):
    REPO_OWNER = "mmnikonovamorozova-boop"
    REPO_NAME = "drill-assistant"
    FILE_PATH = "calibrations_db.json"
    
    token = st.secrets.get("GITHUB_TOKEN", None)
    if not token:
        st.error("🚨 В настройках Streamlit Cloud (Secrets) отсутствует GITHUB_TOKEN. Запись невозможна!")
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
            "message": f"🤖 Самообучение ядра: Скважина {new_data['well']} | Ошибка прогноза снижена",
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            commit_payload["sha"] = sha

        put_res = requests.put(url, headers=headers, json=commit_payload)
        
        if put_res.status_code in:
            st.success("🎉 Математическое ядро успешно обучено! Новые коэффициенты улетели на GitHub.")
            st.cache_data.clear()  # Принудительно чистим кэш
            return True
        else:
            st.error(f"Ошибка коммита через GitHub API: {put_res.status_code}")
    except Exception as err:
        st.error(f"Сбой отправки данных: {err}")
    return False

if st.button("🔄 Запустить самообучение системы и обновить коэффициенты в репозитории", type="primary"):
    with st.spinner("Вычисляется невязка и шаг фильтрации Калмана..."):
        # Рассчитываем ошибку прогноза нашей модели
        # Защита на случай, если переменная total_predicted_angle_gain не успела рассчитаться в блоках выше
        pred_gain = total_predicted_angle_gain if 'total_predicted_angle_gain' in locals() else 0.0
        if pred_gain == 0.0 and 'predicted_dls_10m' in locals():
            pred_gain = predicted_dls_10m
            
        error_delta = actual_angle_gain - pred_gain
        learning_rate = 0.12  # Скорость адаптации модели
        
        # Получаем базовые уставки из базы данных GitHub
        base_slide = float(active_calibration.get("slide_factor", 1.0))
        base_drift = float(active_calibration.get("rotary_drift_val", 0.0))
        base_int = float(active_calibration.get("intensity_correction", 1.0))
        
        # Адаптивное распределение ошибки в зависимости от режима проходки интервала
        if 'kms_last' in locals() and kms_last > 10.0:
            new_slide_factor = base_slide + (error_delta * learning_rate)
            new_rotary_drift = base_drift
        else:
            new_slide_factor = base_slide
            new_rotary_drift = base_drift + (error_delta * learning_rate)
            
        # Формируем итоговую структуру JSON для записи в лог
        import time
        new_point_to_save = {
            "date": time.strftime("%Y-%m-%d %H:%M"),
            "well": current_well,
            "slide_factor": round(float(new_slide_factor), 3),
            "intensity_correction": round(float(base_int), 3),
            "rotary_drift_val": round(float(new_rotary_drift), 3),
            "unbalance_deg": round(float(error_delta), 2)
        }
        
        # Отправляем обновленный массив в репозиторий GitHub
        push_calibration_to_github(new_point_to_save)

# ==============================================================================
# БЛОК 3: ПАРАМЕТРЫ КНБК, РЕАКТИВНЫЙ МОМЕНТ И РЕОЛОГИЯ
# ==============================================================================
st.subheader("⚙️ Параметры КНБК, Реактивный момент и Реология раствора")

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    knbc_type = st.selectbox("Тип КНБК:", ["Стабилизирующая", "Маятниковая", "Комбинированная"])
    gno_zone = st.checkbox("Бурение в зоне установки ГНО")
with col_p2:
    target_wob = st.number_input("Планируемая осевая нагрузка (WOB), тонн:", min_value=1.0, max_value=40.0, value=14.0)
    target_angle = st.number_input("Планируемый зенитный угол, градусов:", min_value=0.0, max_value=90.0, value=25.0)
with col_p3:
    reactive_drop = st.number_input("Реактивный момент ВЗД (отброс при ΔР=15 атм), град:", min_value=0, max_value=180, value=30)
    gtf_target = st.number_input("Плановое положение отклонителя (GTF), град:", min_value=0, max_value=360, value=0)

with st.expander("🧪 Интеграция реологических параметров жидкости (Гершель-Балкли)"):
    mud_density = st.number_input("Плотность бурового раствора, г/см³:", min_value=1.0, max_value=2.2, value=1.20, step=0.01)
    yield_stress = st.number_input("Динамическое напряжение сдвига (τ₀ по Гершелю-Балкли), дПа:", min_value=0.0, max_value=150.0, value=45.0)
    flow_index = st.number_input("Индекс течения раствора (n):", min_value=0.2, max_value=1.0, value=0.65, step=0.01)

buoyancy_factor = 1.0 - (mud_density / 7.85)
true_gtf = (gtf_target - reactive_drop) % 360
st.caption(f"🔄 **Корректировка СМК:** Угол установки на роторной: **GTF {true_gtf}°**")
st.markdown("---")

# ==============================================================================
# БЛОК 4: РАСЧЕТ ИНТЕНСИВНОСТИ И МЕТРАЖА СЛАЙДА (СТР. 11 МЕТОДИЧКИ)
# ==============================================================================
st.subheader("📊 Расчет проходки в режиме «Слайд»")
col_s1, col_s2 = st.columns(2)
with col_s1:
            dls_needed = st.number_input("Интенсивность, которую нужно получить (И), °:", min_value=0.1, max_value=5.0, value=1.5)
    with col_sl_s2:
        ppi_last = st.number_input("Полученная интенсивность на последнем замере (ППИ), °:", min_value=0.1, max_value=5.0, value=0.6)
        kms_last = st.number_input("Количество метров слайда на последнем замере (КМС), м:", min_value=1.0, max_value=30.0, value=5.0)

    # Применяем коэффициент коррекции интенсивности из GitHub базы самообучения
    k_int_learned = float(active_calibration.get("intensity_correction", 1.0))
    
    if st.button("📊 Рассчитать параметры прогноза на забой", type="secondary"):
        # Расчет фактической интенсивности слайда с учетом поправки самообучения
        dls_per_meter = (ppi_last / kms_last) * k_int_learned
        slide_length_needed = dls_needed / dls_per_meter if dls_per_meter > 0 else 0.0
        
        t_theta_rad = np.radians(target_angle)
        L_m = 3.8 if "Стабилизирующая" in knbc_type else (18.0 if "Маятниковая" in knbc_type else 9.0)
        rheology_modifier = buoyancy_factor * (1.0 - (yield_stress / 1000.0) * (1.0 - flow_index))
        
        if "Маятниковая" in knbc_type:
            P_b = -150.0 * np.sin(t_theta_rad) * L_m * rheology_modifier
        elif "Стабилизирующая" in knbc_type:
            P_b = 80.0 * (target_wob / L_m) * np.cos(t_theta_rad) * buoyancy_factor
        else:
            P_b = ((50.0 * (target_wob / L_m) * np.cos(t_theta_rad)) - (70.0 * np.sin(t_theta_rad) * L_m)) * rheology_modifier
            
        # Применяем коэффициент увода в роторе из GitHub базы самообучения
        rotary_drift_learned = float(active_calibration.get("rotary_drift_val", 0.0))
        
        # Финальный предиктивный расчет интенсивности с учетом адаптивного увода
        current_ani_rate = st.session_state.get('calibrated_ani', base_ani)
        predicted_dls_10m = (abs(P_b * current_ani_rate) / 400.0) + rotary_drift_learned
        current_limit = gno_zone_limit if gno_zone else max_allowed_dls

    st.subheader("📋 Результаты оперативного планирования:")
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.metric(label="Интенсивность за 1 метр слайда (И1):", value=f"{dls_per_meter:.3f} °/м")
        st.metric(label="Необходимый метраж слайда (L):", value=f"{slide_length_needed:.1f} м")
    with c_res2:
        st.metric(label="Прогнозная ПИИС на интервал 10м (с учетом ГТИ и реологии):", value=f"{predicted_dls_10m:.2f} °/10м")
        st.metric(label="Действующий лимит технологического коридора:", value=f"{current_limit:.2f} °/10м")

    st.markdown("### 💡 Управляющее воздействие экспертной системы:")
    if predicted_dls_10m > current_limit:
        st.error(f"🚨 **НАРУШЕНИЕ ТЕХНОЛОГИЧЕСКОГО КОРИДОРА {client.upper()}!**")
        st.markdown(f"**Риск:** {CLIENT_LIMITS[client]['penalty_risk']}.")
        st.markdown(f"👉 **Решение регулятора:** Расчетная ПИИС {predicted_dls_10m:.2f}°/10м превышает лимит. Сократите метраж планируемого слайда до **{(slide_length_needed * (current_limit / predicted_dls_10m)):.1f} метров**.")
    elif current_limit * 0.8 <= predicted_dls_10m <= current_limit:
        st.warning(f"⚠️ **Предупредительный коридор.** Ожидаемая интенсивность: {predicted_dls_10m:.2f}°/10м.")
    else:
        st.success(f"✅ **ПРОЦЕСС СТАБИЛЕН.** Прогнозная интенсивность ({predicted_dls_10m:.2f}°/10м) в допуске. Параметры КНБК, режимы ГТИ и реологические свойства раствора утверждены к применению.")

    # ==============================================================================
    # БЛОК 5: ВЕРИФИКАЦИЯ МАТЕМАТИЧЕСКОГО ЯДРА И ГЕНЕРАЦИЯ СМК-ОТЧЕТА
    # ==============================================================================
    st.markdown("---")
    st.subheader("📝 Цифровой след СМК: Верификация и Отчетность")
    
    error_rate = abs(predicted_dls_10m - ppi_last) / ppi_last * 100 if ppi_last > 0 else 0
    convergence_index = max(0.0, 100.0 - error_rate)
        
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        st.metric(label="🤖 Индекс сходимости ядра (Онлайн-верификация):", value=f"{convergence_index:.1f} %")
    with v_col2:
        if convergence_index >= 85:
            st.success("🎯 Высокая адекватность модели.")
        else:
            st.warning("⚠️ Сходимость ниже 85%. Рекомендуется повторить цикл Back-Analysis.")

    report_text = f"ПРОТОКОЛ СМК\nЗаказчик: {client}\nСвита: {selected_formation}\nПрогноз ПИИС: {predicted_dls_10m:.2f} °/10м"
    st.download_button(
        label="📥 Скачать официальный Бланк рекомендаций (TXT)",
        data=report_text,
        file_name=f"SMK_Report_{selected_formation.replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True
    )

