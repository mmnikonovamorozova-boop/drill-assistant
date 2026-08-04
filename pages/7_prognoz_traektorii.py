import streamlit as st
import json
import os
import numpy as np
import requests

st.title("📈 Модуль пространственной интенсивности (Регламент Р-ТС-12)")
st.caption("Адаптивный СМК-контроль траектории ствола ООО «Траектория-Сервис» с учетом реологии Гершеля-Балкли")

# ==============================================================================
# СЕРВИСНЫЙ ОБЛАЧНЫЙ БЛОК: СИНХРОНИЗАЦИЯ С ЯНДЕКС ДИСКОМ
# ==============================================================================
YANDEX_TOKEN = "y0__wgBEOCakoMCGNuWAyDes4rGGDCG7NP5B4UnkGMyCzsQsaLAS58perqQMUtu"

def get_yandex_headers():
    return {
        "Authorization": f"OAuth {YANDEX_TOKEN}",
        "Accept": "application/json"
    }

def load_calibration_from_yandex(formation_name):
    if not YANDEX_TOKEN or "ВАШ" in YANDEX_TOKEN:
        return None
    try:
        path_on_disk = f"drill_assistant_memory/{formation_name}_calibrated.json"
        # ИСПРАВЛЕНО: Добавлен полный рабочий адрес cloud-api.yandex.net
        url = f"https://yandex.net{path_on_disk}"
        response = requests.get(url, headers=get_yandex_headers())
        if response.status_code == 200:
            download_url = response.json().get("href")
            file_response = requests.get(download_url)
            if file_response.status_code == 200:
                return float(file_response.json().get("calibrated_ani", 1.02))
    except:
        pass
    return None

def save_calibration_to_yandex(formation_name, calibrated_value):
    if not YANDEX_TOKEN or "ВАШ" in YANDEX_TOKEN:
        st.error("Токен Яндекс Диска отсутствует или не заполнен.")
        return
    try:
        # 1. Пробуем создать папку и смотрим код ответа
        dir_res = requests.put("https://yandex.net", headers=get_yandex_headers())
        
        # 2. Запрашиваем ссылку на загрузку
        path_on_disk = f"drill_assistant_memory/{formation_name}_calibrated.json"
        url = f"https://yandex.net{path_on_disk}&overwrite=true"
        response = requests.get(url, headers=get_yandex_headers())
        
        if response.status_code == 200:
            upload_url = response.json().get("href")
            data_to_save = {"formation": formation_name, "calibrated_ani": calibrated_value}
            put_response = requests.put(upload_url, data=json.dumps(data_to_save))
            if put_response.status_code in:
                st.toast("💾 Калибровка успешно записана на ваш Яндекс Диск!", icon="☁️")
            else:
                st.error(f"🔴 Ошибка загрузки файла! Код: {put_response.status_code}. Текст: {put_response.text}")
        else:
            # Выводим точный ответ сервера, если токен просрочен или заблокирован
            st.error(f"🔴 Ошибка API Яндекс Диска! Код: {response.status_code}. Ответ: {response.text}")
            st.info("Попробуйте обновить токен на yandex.ru/dev/disk/poligon")
    except Exception as e:
        st.error(f"❌ Критический сбой сети: {str(e)}")
    return None

def save_calibration_to_yandex(formation_name, calibrated_value):
    if not YANDEX_TOKEN or "ВАШ" in YANDEX_TOKEN:
        return
    try:
        requests.put("https://yandex.net", headers=get_yandex_headers())
        path_on_disk = f"drill_assistant_memory/{formation_name}_calibrated.json"
        url = f"https://yandex.net{path_on_disk}&overwrite=true"
        response = requests.get(url, headers=get_yandex_headers())
        if response.status_code == 200:
            upload_url = response.json().get("href")
            data_to_save = {"formation": formation_name, "calibrated_ani": calibrated_value}
            put_response = requests.put(upload_url, data=json.dumps(data_to_save))
            if put_response.status_code == 201:
                st.toast("💾 Калибровка успешно записана на ваш Яндекс Диск!", icon="☁️")
    except:
        pass

# ==============================================================================
# БЛОК 1: БАЗА НЕОДРОПОЛЬЗОВАТЕЛЕЙ (ШТРАФНЫЕ ЛИМИТЫ СМК)
# ==============================================================================
CLIENT_LIMITS = {
    "ПАО «НК «Роснефть»": {"max_dls": 2.5, "penalty_risk": "Высокий (Штраф за превышение DLS на одиночную свечу)", "gno_zone_limit": 1.2},
    "ПАО «Газпром нефть»": {"max_dls": 3.0, "penalty_risk": "Критический (Снижение суточной ставки бурения)", "gno_zone_limit": 1.5},
    "ПАО «ЛУКОЙЛ»": {"max_dls": 2.0, "penalty_risk": "Высокий (Запрет спуска хвостовика, отказ ОТК)", "gno_zone_limit": 1.0}
}

st.sidebar.header("🏢 Выбор Заказчика")
client = st.sidebar.selectbox("Выберите недропользователя:", list(CLIENT_LIMITS.keys()))
max_allowed_dls = CLIENT_LIMITS[client]["max_dls"]
gno_limit = CLIENT_LIMITS[client]["gno_zone_limit"]

st.info(f"📋 **Регламент Заказчика:** {client} | **Макс. допуск:** {max_allowed_dls}°/10м | **Лимит в зоне ГНО:** {gno_limit}°/10м")

# ==============================================================================
# БЛОК 2: ВИЗУАЛЬНЫЙ СМК-ФИЛЬТР СВИТ ПО ЛИТОЛОГИИ И ТВЕРДОСТИ
# ==============================================================================
config_path = os.path.join("config", "formations_config.json")
base_ani = 1.02
selected_formation = "Не выбрана"
lithology = "Не определена"

if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        geo_db = json.load(f)
        
    if geo_db and isinstance(geo_db, list):
        first_row = geo_db[0] if isinstance(geo_db, list) else geo_db
        region_key = next((k for k in first_row.keys() if "регион" in k.lower()), "Регион")
        formation_key = next((k for k in first_row.keys() if "стратигр" in k.lower() or "свита" in k.lower() or "горизонт" in k.lower()), "Стратиграфиче")
        litho_key = next((k for k in first_row.keys() if "литолог" in k.lower() or "состав" in k.lower() or "тип" in k.lower()), "Типичная литолог")
        ani_key = next((k for k in first_row.keys() if "ani" in k.lower() or "анизотр" in k.lower() or "базовый" in k.lower() or "h_an" in k.lower()), "Базовый I(H_an")
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

        st.sidebar.markdown("---")
        if display_formations:
            selected_formation = st.sidebar.selectbox("🎯 Подходящий горизонт из Базы:", display_formations)
            current_data = next((row for row in geo_db if str(row.get(region_key)).strip() == selected_region and str(row.get(formation_key)).strip() == selected_formation), {})
            lithology = current_data.get(litho_key, "Данные отсутствуют")
            ani_str = str(current_data.get(ani_key, "1.02"))
            try:
                bounds = [float(x.strip()) for x in ani_str.split("-") if x.strip()]
                base_ani = sum(bounds) / len(bounds) if bounds else 1.02
            except:
                base_ani = 1.02
        else:
            st.sidebar.warning("Свиты не найдены. Сбросьте фильтры.")

if "cloud_cache" not in st.session_state:
    st.session_state.cloud_cache = {}

if selected_formation != "Не выбрана" and selected_formation not in st.session_state.cloud_cache:
    cloud_val = load_calibration_from_yandex(selected_formation)
    if cloud_val:
        st.session_state.cloud_cache[selected_formation] = cloud_val
        st.session_state.calibrated_ani = cloud_val
    else:
        st.session_state.cloud_cache[selected_formation] = base_ani
        st.session_state.calibrated_ani = base_ani

st.info(f"📋 **СМК-подбор:** {selected_formation} | **Состав:** {lithology} | **Базовая анизотропия:** {base_ani:.3f}")
st.markdown("---")

# ==============================================================================
# КОНТУР ОБУЧЕНИЯ (ОБРАТНАЯ ЗАДАЧА С СИНХРОНИЗАЦИЕЙ В ОБЛАКО)
# ==============================================================================
st.subheader("🔄 Контур обучения ядра (Обратная задача по ГГИ/ГТИ)")
st.caption("Введите фактические параметры последнего пробуренного интервала для калибровки и отправки на Яндекс Диск")

col_ob1, col_ob2, col_ob3 = st.columns(3)
with col_ob1:
    fact_wob = st.number_input("Фактическая нагрузка на долото (т):", min_value=1.0, max_value=40.0, value=12.0)
with col_ob2:
    fact_angle = st.number_input("Фактический зенитный угол на интервале (°):", min_value=0.0, max_value=90.0, value=30.0)
with col_ob3:
    fact_dls = st.number_input("Фактическая полученная интенсивность (°/10м):", min_value=0.0, max_value=6.0, value=1.4)

if st.button("🔄 Запустить самообучение системы", type="secondary"):
    theta_rad = np.radians(fact_angle)
    calculated_pb = abs(65.0 * (fact_wob / 9.0) * np.cos(theta_rad))
    if calculated_pb > 0:
        raw_k_ani = (fact_dls * 400.0) / calculated_pb
        new_ani = max(1.0, min(raw_k_ani, 1.4))
        st.session_state.calibrated_ani = new_ani
        st.session_state.cloud_cache[selected_formation] = new_ani
        save_calibration_to_yandex(selected_formation, new_ani)
        st.success(f"🎯 Ядро обучено! Индекс анизотропии пласта скорректирован до **{new_ani:.3f}**")
    else:
        st.error("Ошибка расчета боковой силы КНБК.")

st.info(f"🤖 **Текущий статус ИИ-ядра:** Используется коэффициент анизотропии породы = **{st.session_state.get('calibrated_ani', base_ani):.3f}**")
st.markdown("---")

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

# Внедрение параметров реологии (модель Гершеля-Балкли)
with st.expander("🧪 Интеграция реологических параметров жидкости (Гершель-Балкли)"):
    mud_density = st.number_input("Плотность раствора, г/см³:", min_value=1.0, max_value=2.2, value=1.20, step=0.01)
    yield_stress = st.number_input("Напряжение сдвига (τ₀), дПа:", min_value=0.0, max_value=150.0, value=45.0)
    flow_index = st.number_input("Индекс течения (n):", min_value=0.2, max_value=1.0, value=0.65, step=0.01)

# Коэффициент плавучести (плотность стали 7.85)
buoyancy_factor = 1.0 - (mud_density / 7.85)

true_gtf = (gtf_target - reactive_drop) % 360
st.caption(f"🔄 **Корректировка СМК:** Угол установки (роторная): **GTF {true_gtf}°**")
st.markdown("---")
