import streamlit as st
import json
import os
import numpy as np
from scipy.optimize import minimize_scalar

st.title("📈 Модуль пространственной интенсивности (Регламент Р-ТС-12)")
st.caption("Адаптивный СМК-контроль траектории ствола скважины ООО «Траектория-Сервис»")

# ==============================================================================
# БЛОК 1: БАЗА НЕ ДРОПОЛЬЗОВАТЕЛЕЙ (ШТРАФНЫЕ ЛИМИТЫ СМК)
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
# БЛОК 2: ПОДКЛЮЧЕНИЕ СТРАТИГРАФИИ ИЗ НАШЕЙ ПАПКИ CONFIG
# ==============================================================================
config_path = os.path.join("config", "formations_config.json")
base_ani = 1.02
selected_formation = "Не выбрана"

if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        geo_db = json.load(f)
    if geo_db and isinstance(geo_db, list):
        regions = list(set([row.get("Регион", "Не указан") for row in geo_db if row.get("Регион")]))
        selected_region = st.sidebar.selectbox("Регион бурения:", regions)
        formations = [row.get("Стратиграфиче", "Не указана") for row in geo_db if row.get("Регион") == selected_region]
        selected_formation = st.sidebar.selectbox("Стратиграфический горизонт:", formations)
        current_data = next((row for row in geo_db if row.get("Регион") == selected_region and row.get("Стратиграфиче") == selected_formation), {})
        ani_str = str(current_data.get("Базовый I(H_an", "1.02"))
        try:
            bounds = [float(x.strip()) for x in ani_str.split("-") if x.strip()]
            base_ani = sum(bounds) / len(bounds) if bounds else 1.02
        except:
            base_ani = 1.02
        st.sidebar.caption(f"Выбрана свита: {selected_formation} (Дефолтная анизотропия: {base_ani})")

# Инициализируем рабочую анизотропию дефолтным значением
if "calibrated_ani" not in st.session_state:
    st.session_state.calibrated_ani = base_ani

st.markdown("---")

# ==============================================================================
# КОНТУР ОБУЧЕНИЯ (ОБРАТНАЯ ЗАДАЧА / BACK-ANALYSIS)
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
    
    # Функция ошибки для минимизации (обратный расчет k_ani)
    def loss_function(k_ani):
        # Модель прогноза: dls = (Pb * k_ani) / 400
        pred_dls = (calculated_pb * k_ani) / 400.0
        return (fact_dls - pred_dls) ** 2

    # Ищем истинный коэффициент анизотропии пласта в физических границах (1.0 - 1.4)
    res = minimize_scalar(loss_function, bounds=(1.0, 1.4), method='bounded')
    
    if res.success:
        st.session_state.calibrated_ani = float(res.x)
        st.success(f"🎯 Ядро успешно обучено! Текущая анизотропия пласта скорректирована с {base_ani:.2f} до **{st.session_state.calibrated_ani:.3f}**")
    else:
        st.error("Ошибка сходимости алгоритма калибровки.")

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
        st.warning(f"⚠️ **Предупредительный рубеж СМК (Зона повышенного внимания).**")
        st.markdown("👉 **Рекомендация по Р-ТС-12:** Ожидаемый профиль близок к критической границе. Стройте предиктивную палетку на 3 свечи вперед после каждого фактического замера.")
    else:
        st.success("✅ **ТЕХНОЛОГИЧЕСКИЙ КОМПЛАЕНС ПОЛНОСТЬЮ СОБЛЮДЕН.**")
        st.markdown(f"👉 Режимы ГТИ и КНБК утверждены. Пространственная интенсивность находится под управлением адаптивной СМК-модели.")
