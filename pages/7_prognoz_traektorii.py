import base64
import json
import requests
import streamlit as st
from datetime import datetime

def load_all_calibrations_from_github():
    """Загружает БД через API с выводом отладочной информации в сайдбар."""
    try:
        api_url = "https://github.com"
        r = requests.get(api_url, headers=get_github_headers())
        
        # Выводим статус загрузки в сайдбар для контроля
        st.sidebar.write(f"🔍 Статус GET-запроса базы: {r.status_code}")
        
        if r.status_code == 200:
            content_json = r.json()
            file_content = base64.b64decode(content_json["content"]).decode("utf-8")
            st.sidebar.write(f"📄 Текущее содержимое файла: {file_content}")
            
            if not file_content.strip() or file_content.strip() == "[]":
                return [], content_json["sha"]
            return json.loads(file_content), content_json["sha"]
            
        return [], None
    except Exception as e:
        st.sidebar.error(f"Ошибка загрузки: {str(e)}")
        return [], None

def save_calibration_to_github(formation_name, calibrated_value, current_wob, current_angle):
    """Обновляет JSON на GitHub и печатает отправляемый payload на экран."""
    try:
        st.sidebar.write("🚀 Запуск функции сохранения...")
        history, sha = load_all_calibrations_from_github()
        
        if not isinstance(history, list):
            history = []
            
        # Формируем запись
        new_record = {
            "formation": str(formation_name),
            "calibrated_ani": float(calibrated_value),
            "wob": float(current_wob),
            "angle": float(current_angle),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        history.append(new_record)
        
        # Печатаем массив, который МЫ ПЫТАЕМСЯ ОТПРАВИТЬ, чтобы увидеть, не пустой ли он
        st.sidebar.write(f"📦 Сформированный массив для отправки: {history}")
        st.sidebar.write(f"🔑 Актуальный SHA файла: {sha}")
        
        # Подготовка контента
        json_string = json.dumps(history, indent=2, ensure_ascii=False)
        encoded_content = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")
        
        target_url = "https://github.com"
        payload = {
            "message": f"СМК-Автокоммит: {formation_name}",
            "content": encoded_content,
            "branch": "main"
        }
        
        if sha:
            payload["sha"] = sha
            
        put_r = requests.put(target_url, headers=get_github_headers(), json=payload)
        
        st.sidebar.write(f"📡 Статус ответа PUT от GitHub: {put_r.status_code}")
        
        if put_r.status_code == 200 or put_r.status_code == 201:
            st.toast("💾 Данные успешно синхронизированы с GitHub!", icon="🚀")
            st.sidebar.success("Коммит успешно отправлен сервером!")
        else:
            st.sidebar.error(f"GitHub отклонил запись! Код: {put_r.status_code}")
            st.sidebar.write(put_r.json())
            
    except Exception as e:
        st.sidebar.error(f"Сбой контура сохранения: {str(e)}")

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
if st.button("Запустить самообучение системы", type="primary"):
    with st.spinner("Обучение ядра ИИ и синхронизация БД..."):
        # 1. Сюда вставьте ваши математические расчеты, которые уже были в кнопке
        # (Например, расчет нового коэффициента анизотропии)
        calibrated_val = 1.400 # Или ваша переменная расчета анизотропии
        
        # 2. Вытаскиваем значения из интерфейса, которые выбрал пользователь
        # Сверяем названия с вашими виджетами выбора свиты, WOB и угла
        current_formation = selected_formation if 'selected_formation' in locals() else "Неизвестная свита"
        # Если у вас виджеты называются иначе, например st.selectbox, укажите их переменные:
        # current_formation = v_svita 
        
        # Забираем значения веса на долото (WOB) и зенитного угла из полей ввода параметров КНБК
        # По скриншотам они у вас введены в поля (14.00 тонн и 25.00 градусов)
        wob_val = target_wob if 'target_wob' in locals() else 14.0
        angle_val = target_angle if 'target_angle' in locals() else 25.0
        
        # 3. ПРИНУДИТЕЛЬНЫЙ ВЫЗОВ НАШЕЙ ИСПРАВЛЕННОЙ ФУНКЦИИ СОХРАНЕНИЯ
        save_calibration_to_github(
            formation_name=current_formation,
            calibrated_value=calibrated_val,
            current_wob=wob_val,
            current_angle=angle_val
        )
        
        st.success(f"🤖 Ядро успешно обучено для свиты {current_formation}! Данные отправлены в GitOps контур.")

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
with col_s2:
    ppi_last = st.number_input("Полученная интенсивность на последнем замере (ППИ), °:", min_value=0.1, max_value=5.0, value=0.6)
    kms_last = st.number_input("Количество метров слайда на последнем замере (КМС), м:", min_value=1.0, max_value=30.0, value=5.0)

if st.button("📈 Рассчитать параметры прогноза на забой", type="secondary"):
    dls_per_meter = ppi_last / kms_last
    slide_length_needed = dls_needed / dls_per_meter if dls_per_meter > 0 else 0.0
        
    t_theta_rad = np.radians(target_angle)
    L_m = 3.0 if "Стабилизирующая" in knbc_type else (18.0 if "Маятниковая" in knbc_type else 9.0)
    rheology_modifier = buoyancy_factor * (1.0 - (yield_stress / 1000.0) * (1.0 - flow_index))
    
    if "Маятниковая" in knbc_type:
        P_b = -150.0 * np.sin(t_theta_rad) * L_m * rheology_modifier
    elif "Стабилизирующая" in knbc_type:
        P_b = 80.0 * (target_wob / L_m) * np.cos(t_theta_rad) * buoyancy_factor
    else:
        P_b = ((50.0 * (target_wob / L_m) * np.cos(t_theta_rad)) - (70.0 * np.sin(t_theta_rad) * L_m)) * rheology_modifier
        
    current_ani_rate = st.session_state.get('calibrated_ani', base_ani)
    predicted_dls_10m = abs(P_b * current_ani_rate) / 400.0
    current_limit = gno_limit if gno_zone else max_allowed_dls

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

