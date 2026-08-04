import streamlit as st
import json
import os
import numpy as np
import requests

st.title("📈 Модуль пространственной интенсивности (Регламент Р-ТС-12)")
st.caption("Адаптивный СМК-контроль траектории ствола ООО «Траектория-Сервис» с учетом реологии Гершеля-Балкли")

# ==============================================================================
# СЕРВИСНЫЙ ОБЛАЧНЫЙ БЛОК: СИНХРОНИЗАЦИЯ С ВАШЕЙ ПАПКОЙ DRILL_MEMORY
# ==============================================================================
YANDEX_TOKEN = "y0__wgBEOCakoMCGNuWAyDes4rGGDCG7NP5B4UnkGMyCzsQsaLAS58perqQMUtu"

def get_yandex_headers():
    return {
        "Authorization": f"OAuth {YANDEX_TOKEN}",
        "Accept": "application/json"
    }

def load_calibration_from_yandex(formation_name):
    """Загрузка калибровки с обработкой ошибок."""
    if not YANDEX_TOKEN or "ВАШ" in YANDEX_TOKEN: return None
    try:
        path = f"drill_memory/{formation_name}_calibrated.json"
        url = f"https://yandex.net{path}"
        r = requests.get(url, headers=get_yandex_headers())
        if r.status_code == 200:
            file_r = requests.get(r.json().get("href"))
            return float(file_r.json().get("calibrated_ani", 1.02))
    except: pass
    return None

def save_calibration_to_yandex(formation_name, calibrated_value):
    """Сохранение с детальным контролем ошибок API."""
    if not YANDEX_TOKEN or "ВАШ" in YANDEX_TOKEN:
        st.error("Токен Яндекс Диска отсутствует.")
        return
    try:
        path = f"drill_memory/{formation_name}_calibrated.json"
        url = f"https://yandex.net{path}&overwrite=true"
        r = requests.get(url, headers=get_yandex_headers())
        
        if r.status_code == 200:
            up_url = r.json().get("href")
            data = {"formation": formation_name, "calibrated_ani": calibrated_value}
            # Отправка файла
            put_r = requests.put(up_url, data=json.dumps(data))
            if put_r.status_code == 201:
                st.toast("💾 Калибровка сохранена!", icon="✅")
            else:
                st.error(f"🔴 Ошибка записи. Код: {put_r.status_code}")
        else:
            st.error(f"🔴 Ошибка Яндекс API ({r.status_code})")
            if r.status_code == 401: st.warning("🔐 Обновите токен")
            elif r.status_code == 404: st.warning("📂 Создайте папку 'drill_memory'")
    except Exception as e:
        st.error(f"❌ Ошибка: {str(e)}")

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
# БЛОК 2: ВИЗУАЛЬНЫЙ СМК-ФИЛЬТР СВИТ ПО ЛИТОЛОГИИ И ТВЕРДОСТИ (ДЛЯ СПИСКОВ JSON)
# ==============================================================================
config_path = os.path.join("config", "formations_config.json")
base_ani = 1.02
selected_formation = "Не выбрана"
lithology = "Не определена"

if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        geo_db = json.load(f)
        
    if geo_db and isinstance(geo_db, list):
        # Защита от AttributeError: берем первый элемент (словарь) из списка
        first_row = geo_db[0] if len(geo_db) > 0 else {}
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

# ==============================================================================
# КОНТУР ОБУЧЕНИЯ (ОБРАТНАЯ ЗАДАЧА)
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

if st.button("🔄 Запустить самообучение системы", type="primary"):
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

if st.button("📈 Рассчитать параметры прогноза на забой", type="primary"):
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
    
    # 1. Расчет онлайн-верификации математического ядра (метрика сходимости)
    # Сравниваем базовую интенсивность, факт и наш прогноз
    if ppi_last > 0:
        error_rate = abs(predicted_dls_10m - ppi_last) / ppi_last * 100
        convergence_index = max(0.0, 100.0 - error_rate)
    else:
        convergence_index = 100.0
        
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        st.metric(
            label="🤖 Индекс сходимости математического ядра (Онлайн-верификация):", 
            value=f"{convergence_index:.1f} %",
            help="Показывает точность настройки предиктивной модели относительно фактических данных ГТИ"
        )
    with v_col2:
        if convergence_index >= 85:
            st.success("🎯 Высокая адекватность модели. Дополнительная калибровка не требуется.")
        else:
            st.warning("⚠️ Сходимость ниже 85%. Рекомендуется повторить цикл Back-Analysis в контуре обучения.")

    # 2. Формирование текстового бланка рекомендаций (протокола)
    report_text = f"""==================================================================
           ПРОТОКОЛ ПРЕДИКТИВНОГО УПРАВЛЕНИЯ ТРАЕКТОРИЕЙ СТВОЛА
               ООО «ТРАЕКТОРИЯ-СЕРВИС» • СМК-КОНТУР АУДИТА
==================================================================
Дата/Время расчета: Автоматическая фиксация в ИС
Заказчик (Недропользователь): {client}
Стратиграфический горизонт: {selected_formation}
Литологический состав пласта: {lithology}
Расчетный индекс механической анизотропии пород: {st.session_state.get('calibrated_ani', base_ani):.3f}

1. ТЕКУЩИЕ ПАРАМЕТРЫ И РЕОЛОГИЯ (ГЕРШЕЛЬ-БАЛКЛИ):
- Планируемая осевая нагрузка (WOB): {target_wob} тонн
- Зенитный угол секции: {target_angle} град.
- Плотность бурового раствора: {mud_density} г/см3
- Динамическое напряжение сдвига (tau_0): {yield_stress} дПа
- Индекс течения раствора (n): {flow_index}

2. РЕЗУЛЬТАТЫ МАТЕМАТИЧЕСКОГО МОДЕЛИРОВАНИЯ И ВЕРИФИКАЦИИ:
- Тип применяемой КНБК: {knbc_type}
- Расчетный истинный угол установки отклонителя: GTF {true_gtf} град.
- Необходимый метраж слайда для коррекции профиля: {slide_length_needed:.1f} метров
- Прогнозная пространственная интенсивность (ПИИС): {predicted_dls_10m:.2f} град/10м
- Действующий регламентный лимит Заказчика: {current_limit:.2f} град/10м
- Индекс онлайн-верификации сходимости ядра: {convergence_index:.1f} %

3. УПРАВЛЯЮЩЕЕ ВОЗДЕЙСТВИЕ ЭКСПЕРТНОЙ СИСТЕМЫ:
{"[НАРУШЕНИЕ ЛИМИТА] Снизить плановые режимы бурения / изменить жесткость КНБК." if predicted_dls_10m > current_limit else "[НОРМА] Параметры КНБК и режимы ГТИ утверждены к применению."}

Ответственный инженер ННБ: Системная авторизация
=================================================================="""

    # 3. Кнопка скачивания бланка в один клик
    st.download_button(
        label="📥 Скачать официальный Бланк рекомендаций (TXT)",
        data=report_text,
        file_name=f"SMK_Report_{selected_formation.replace(' ', '_')}.txt",
        mime="text/plain",
        type="secondary",
        use_container_width=True
    )
