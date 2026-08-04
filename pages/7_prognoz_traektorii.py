import streamlit as st
import json
import os
import numpy as np

st.title("📈 Модуль пространственной интенсивности (Регламент Р-ТС-12)")
st.caption("Адаптивный СМК-контроль траектории ствола скважины ООО «Траектория-Сервис»")

# ==============================================================================
# БЛОК 1: БАЗА НЕОДРОПОЛЬЗОВАТЕЛЕЙ (ШТРАФНЫЕ ЛИМИТЫ СМК)
# ==============================================================================
CLIENT_LIMITS = {
    "ПАО «НК «Роснефть»": {
        "max_dls": 2.5,
        "penalty_risk": "Высокий (Штраф за превышение DLS на одиночную свечу, риск заклинивания)",
        "gno_zone_limit": 1.2
    },
    "ПАО «Газпром нефть»": {
        "max_dls": 3.0,
        "penalty_risk": "Критический (Снижение ставки за сутки бурения при выходе из коридора)",
        "gno_zone_limit": 1.5
    },
    "ПАО «ЛУКОЙЛ»": {
        "max_dls": 2.0,
        "penalty_risk": "Высокий (Запрет спуска хвостовика, жесткий покаротажный контроль)",
        "gno_zone_limit": 1.0
    }
}

st.sidebar.header("🏢 Выбор Заказчика")
client = st.sidebar.selectbox("Выберите недропользователя:", list(CLIENT_LIMITS.keys()))

max_allowed_dls = CLIENT_LIMITS[client]["max_dls"]
gno_limit = CLIENT_LIMITS[client]["gno_zone_limit"]

st.info(f"📋 **Регламент Заказчика:** {client} | **Макс. допуск:** {max_allowed_dls}°/10м | **Лимит в зоне ГНО:** {gno_limit}°/10м")

# ==============================================================================
# БЛОК 2: ВИЗУАЛЬНЫЙ СМК-ФИЛЬТР СВИТ ПО ЛИТОЛОГИИ И ТВЕРДОСТИ (ДЛЯ ИНЖЕНЕРОВ-ВИЗУАЛОВ)
# ==============================================================================
config_path = os.path.join("config", "formations_config.json")
base_ani = 1.02
selected_formation = "Не выбрана"

if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        geo_db = json.load(f)
        
    if geo_db and isinstance(geo_db, list):
        # Автоматический поиск ключей в JSON (по вашей таблице)
        first_row = geo_db[0] if isinstance(geo_db, list) else geo_db
        region_key = next((k for k in first_row.keys() if "регион" in k.lower()), "Регион")
        formation_key = next((k for k in first_row.keys() if "стратигр" in k.lower() or "свита" in k.lower() or "горизонт" in k.lower()), "Стратиграфиче")
        litho_key = next((k for k in first_row.keys() if "литолог" in k.lower() or "состав" in k.lower() or "тип" in k.lower()), "Типичная литолог")
        ani_key = next((k for k in first_row.keys() if "ani" in k.lower() or "анизотр" in k.lower() or "базовый" in k.lower() or "h_an" in k.lower()), "Базовый I(H_an")
        category_key = next((k for k in first_row.keys() if "категор" in k.lower() or "тверд" in k.lower() or "класс" in k.lower()), "Категория бури")

        # 1. Выбор региона бурения
        regions = list(set([str(row.get(region_key, "Не указан")).strip() for row in geo_db if row.get(region_key)]))
        selected_region = st.sidebar.selectbox("1. Регион бурения:", regions)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🎨 Фильтр визуального восприятия пласта:**")
        
        # 2. Выбор литологического класса (упрощаем для визуала)
        rock_types = ["Все типы", "Пески / Песчаники", "Глины / Аргиллиты", "Известняки / Доломиты / Соли"]
        selected_rock = st.sidebar.selectbox("2. Какая порода на забое?", rock_types)
        
        # 3. Выбор категории твердости
        hardness_types = ["Все категории", "Мягкие (I-III)", "Средние (III-IV)", "Твердые / Хрупкие (V-VII)"]
        selected_hardness = st.sidebar.selectbox("3. Какая твердость пласта?", hardness_types)

        # Фильтрация массива данных на основе понятных инженеру физических критериев
        filtered_rows = [row for row in geo_db if str(row.get(region_key)).strip() == selected_region]
        
        # Фильтр по литологии
        if selected_rock != "Все типы":
            keyword = "песк" if "Пески" in selected_rock else ("глин" if "Глины" in selected_rock else "извест")
            filtered_rows = [r for r in filtered_rows if keyword in str(r.get(litho_key, "")).lower()]
            
        # Фильтр по твердости
        if selected_hardness != "Все категории":
            h_keyword = "мягк" if "Мягкие" in selected_hardness else ("средн" if "Средние" in selected_hardness else "тверд")
            filtered_rows = [r for r in filtered_rows if h_keyword in str(r.get(category_key, "")).lower() or h_keyword in str(r.get(litho_key, "")).lower()]

        # Собираем итоговый список свит, прошедших физический фильтр
        display_formations = sorted(list(set([str(row.get(formation_key, "Не указана")).strip() for row in filtered_rows])))
        display_formations = [f for f in display_formations if f and f != "None" and f != "Не указана"]

        st.sidebar.markdown("---")

        if display_formations:
            # Итоговый отфильтрованный список (он гарантированно короткий и не зависнет)
            selected_formation = st.sidebar.selectbox("🎯 Подходящий горизонт из Базы:", display_formations)
            
            # Извлекаем итоговые расчетные параметры
            current_data = next((row for row in geo_db if str(row.get(region_key)).strip() == selected_region and str(row.get(formation_key)).strip() == selected_formation), {})
            lithology = current_data.get(litho_key, "Данные отсутствуют")
            
            # Парсинг коэффициента анизотропии
            ani_str = str(current_data.get(ani_key, "1.02"))
            try:
                bounds = [float(x.strip()) for x in ani_str.split("-") if x.strip()]
                base_ani = sum(bounds) / len(bounds) if bounds else 1.02
            except:
                base_ani = 1.02
        else:
            st.sidebar.warning("Свиты с такими свойствами в регионе не найдены. Сбросьте фильтры.")
            lithology = "Данные не подобраны"
            
        st.sidebar.caption(f"Выбран индекс анизотропии: {base_ani:.3f}")
    else:
        # Резервный контур для древовидной структуры
        if geo_db:
            selected_region = st.sidebar.selectbox("1. Регион бурения:", list(geo_db.keys()))
            selected_formation = st.sidebar.selectbox("🎯 Горизонт (свита):", list(geo_db[selected_region].keys()))
            current_data = geo_db[selected_region][selected_formation]
            lithology = current_data.get("lithology", "Данные отсутствуют")
            base_ani = current_data.get("base_ani", 1.02)

    st.info(f"📋 **Результат СМК-подбора:** {selected_formation} | **Литологический состав:** {lithology} | **Анизотропия пласта:** {base_ani:.3f}")

# ==============================================================================
# КОНТУР ОБУЧЕНИЯ (ОБРАТНАЯ ЗАДАЧА / ПРЯМОЙ АНАЛИТИЧЕСКИЙ ВЫВОД)
# ==============================================================================
st.subheader("🔄 Контур обучения ядра (Обратная задача по ГГИ/ГТИ)")
st.caption("Введите фактические параметры последнего пробуренного интервала для калибровки свойств пласта")

col_ob1, col_ob2, col_ob3 = st.columns(3)
with col_ob1:
    fact_wob = st.number_input("Фактическая нагрузка на долото (т):", min_value=1.0, max_value=40.0, value=12.0)
with col_ob2:
    fact_angle = st.number_input("Фактический зенитный угол на интервале (°):", min_value=0.0, max_value=90.0, value=30.0)
with col_ob3:
    fact_dls = st.number_input("Фактическая полученная интенсивность (°/10м):", min_value=0.0, max_value=6.0, value=1.4)

if st.button("🔄 Запустить самообучение системы", type="secondary"):
    # Прямая физическая модель сил: боковая сила зависит от нагрузки и угла наклона пласта
    theta_rad = np.radians(fact_angle)
    calculated_pb = abs(65.0 * (fact_wob / 9.0) * np.cos(theta_rad))
    
    if calculated_pb > 0:
        # Аналитическое решение уравнения: k_ani = (fact_dls * 400) / Pb
        raw_k_ani = (fact_dls * 400.0) / calculated_pb
        # Ограничиваем физический диапазон анизотропии для горных пород (от 1.0 до 1.4) через встроенный min/max
        st.session_state.calibrated_ani = max(1.0, min(raw_k_ani, 1.4))
        st.success(f"🎯 Ядро успешно обучено! Текущая анизотропия пласта скорректирована с {base_ani:.2f} до **{st.session_state.calibrated_ani:.3f}**")
    else:
        st.error("Критическая ошибка: боковая сила КНБК близка к нулю, расчет невозможен.")

st.info(f"🤖 **Текущий статус ИИ-ядра:** Используется коэффициент анизотропии породы = **{st.session_state.calibrated_ani:.3f}**")
st.markdown("---")

# ==============================================================================
# БЛОК 3: ПАРАМЕТРЫ КНБК И ОПРЕДЕЛЕНИЕ РЕАКТИВНОГО МОМЕНТА (СТР. 4 МЕТОДИЧКИ)
# ==============================================================================
st.subheader("⚙️ Параметры КНБК и Реактивный момент ВЗД")
col1, col2, col3 = st.columns(3)

with col1:
    knbc_type = st.selectbox("Тип КНБК:", ["Стабилизирующая", "Маятниковая", "Комбинированная"])
    gno_zone = st.checkbox("Бурение в зоне установки ГНО")

with col2:
    target_wob = st.number_input("Планируемая осевая нагрузка (WOB), тонн:", min_value=1.0, max_value=40.0, value=14.0)
    target_angle = st.number_input("Планируемый зенитный угол, градусов:", min_value=0.0, max_value=90.0, value=25.0)

with col3:
    reactive_drop = st.number_input("Реактивный момент ВЗД (отброс при ΔР=15 атм), град:", min_value=0, max_value=180, value=30)
    gtf_target = st.number_input("Плановое положение отклонителя (GTF), град:", min_value=0, max_value=360, value=0)

# Расчет истинного угла установки с учетом реактивного момента (стр. 4 памятки)
true_gtf = (gtf_target - reactive_drop) % 360
st.caption(f"🔄 **Корректировка СМК:** Имитация наворота пружины. Угол установки отклонителя на роторной: **GTF {true_gtf}°**")

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
    # Формула 1 со стр. 11 памятки: Интенсивность за 1 метр проходки слайда
    dls_per_meter = ppi_last / kms_last
    
    # Формула 2 со стр. 11 памятки: Необходимое количество метров слайда (L)
    slide_length_needed = dls_needed / dls_per_meter if dls_per_meter > 0 else 0.0
        
    # Моделирование боковой силы КНБК для прогноза
    t_theta_rad = np.radians(target_angle)
    L_m = 3.0 if "Стабилизирующая" in knbc_type else (18.0 if "Маятниковая" in knbc_type else 9.0)
    
    if "Маятниковая" in knbc_type:
        P_b = -150.0 * np.sin(t_theta_rad) * L_m
    elif "Стабилизирующая" in knbc_type:
        P_b = 80.0 * (target_wob / L_m) * np.cos(t_theta_rad)
    else:
        P_b = (50.0 * (target_wob / L_m) * np.cos(t_theta_rad)) - (70.0 * np.sin(t_theta_rad) * L_m)
        
    # Финальный расчет DLS на 10м с использованием ОБУЧЕННОГО коэффициента (session_state.calibrated_ani)
    predicted_dls_10m = abs(P_b * st.session_state.calibrated_ani) / 400.0
    current_limit = gno_limit if gno_zone else max_allowed_dls

    st.subheader("📋 Результаты оперативного планирования:")
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.metric(label="Интенсивность за 1 метр слайда (И1):", value=f"{dls_per_meter:.3f} °/м")
        st.metric(label="Необходимый метраж слайда (L):", value=f"{slide_length_needed:.1f} м")
    with c_res2:
        st.metric(label="Прогнозная ПИИС на интервал 10м (с учетом ИИ-калибровки):", value=f"{predicted_dls_10m:.2f} °/10м")
        st.metric(label="Действующий лимит технологического коридора:", value=f"{current_limit:.2f} °/10м")

    # СИСТЕМА ПОДДЕРЖКИ ПРИНЯТИЯ РЕШЕНИЙ
    st.markdown("### 💡 Управляющее воздействие экспертной системы:")
    if predicted_dls_10m > current_limit:
        st.error(f"🚨 **НАРУШЕНИЕ ТЕХНОЛОГИЧЕСКОГО КОРИДОРА {client.upper()}!**")
        st.markdown(f"**Риск:** {CLIENT_LIMITS[client]['penalty_risk']}.")
        st.markdown(f"👉 **Решение регулятора:** Расчетная ПИИС {predicted_dls_10m:.2f}°/10м приведет к штрафным санкциям. Сократите метраж планируемого слайда до **{(slide_length_needed * (current_limit / predicted_dls_10m)):.1f} метров**.")
    elif current_limit * 0.8 <= predicted_dls_10m <= current_limit:
        st.warning(f"⚠️ **Предупредительный коридор.** Ожидаемая интенсивность: {predicted_dls_10m:.2f}°/10м. Допускается бурение при условии покаротажного контроля каждые 5 метров.")
    else:
        st.success(f"✅ **ПРОЦЕСС СТАБИЛЕН.** Прогнозная интенсивность ({predicted_dls_10m:.2f}°/10м) в допуске. Параметры КНБК и режимы ГТИ утверждены к применению.")

