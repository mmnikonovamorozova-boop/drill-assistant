import streamlit as st
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Калькулятор люфта ВЗД", layout="wide")

st.title("📏 Комплексный расчет износа и люфтов шпинделя ВЗД")
st.caption("МЕТОДИКА КОНТРОЛЯ ИЗНОСА ПО РЕГЛАМЕНТАМ")
st.markdown("---")

# Сбор данных из боковой панели
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
selected_client = st.sidebar.selectbox("Заказчик (Недропользователь):", ["ПАО Роснефть", "ПАО Газпром", "ПАО Лукойл", "Без ограничений"])

# --- База данных ---
# Внутренние лимиты Заказчиков
client_limits_db = {
    "ПАО Роснефть": {"малый": {"axial": 3.5, "radial": 1.0}, "средний": {"axial": 4.0, "radial": 1.2}, "большой": {"axial": 5.0, "radial": 1.8}},
    "ПАО Газпром": {"малый": {"axial": 4.0, "radial": 1.2}, "средний": {"axial": 4.5, "radial": 1.5}, "большой": {"axial": 5.0, "radial": 2.0}},
    "ПАО Лукойл": {"малый": {"axial": 4.0, "radial": 1.2}, "средний": {"axial": 5.0, "radial": 1.6}, "большой": {"axial": 5.5, "radial": 2.2}}
}

# Восстановленная база: Радиус, Гидробур, NOV, НГТ, ВНИИБТ
base_vzd = {
    "Радиус-Сервис": {
        "95 мм": {"nominal": 1.2, "limit": 8.0, "radial": 1.2, "group": "малый"},
        "172 мм": {"nominal": 2.0, "limit": 10.0, "radial": 1.5, "group": "средний"},
    },
    "Гидробур-Сервис": {
        "178 мм": {"nominal": 1.5, "limit": 5.5, "radial": 1.5, "group": "средний"},
    },
    "NOV": {
        "5'' (5/16'')": {"nominal": 1.5, "limit": 7.94, "radial": 1.5, "group": "малый"},
        "8'' (1/2'')": {"nominal": 3.1, "limit": 12.70, "radial": 2.0, "group": "большой"},
    },
    "НГТ": {
        "ДР-120.NGT": {"nominal": 1.5, "limit": 8.0, "radial": 1.5, "group": "малый"},
    },
    "ВНИИБТ": {
        "Д-73 / ДР-73": {"nominal": 1.2, "limit": 3.0, "radial": 1.2, "group": "малый"},
        "ДГР-172": {"nominal": 2.0, "limit": 6.0, "radial": 1.5, "group": "средний"},
    }
}

# --- Логика выбора и расчета ---
selected_brand = st.selectbox("1. Производитель ВЗД:", list(base_vzd.keys()))
current_brand_models = base_vzd[selected_brand]
selected_diameter = st.selectbox("2. Габарит / Модель:", list(current_brand_models.keys()))

vzd_data = current_brand_models[selected_diameter]
limit_nominal = vzd_data["nominal"]
limit_wear = vzd_data["limit"]
limit_radial = vzd_data["radial"]
size_group = vzd_data["group"]

# Калькулятор NOV (перевод дюймов)
if selected_brand == "NOV":
    st.warning("🇺🇸 ВЗД Американского производства (NOV).")
    col1, col2 = st.columns(2)
    with col1: num = st.selectbox("Числитель:", [1, 3, 5, 7, 9, 11, 13, 15], index=3)
    with col2: den = st.selectbox("Знаменатель:", [2, 4, 8, 16], index=3)
    mm_res = (num / den) * 25.4
    st.success(f"📐 Лимит: {mm_res:.2f} мм")

# Сверка лимитов (Заказчик vs Паспорт)
if selected_client != "Без ограничений":
    limit_client_axial = client_limits_db[selected_client][size_group]["axial"]
    limit_client_radial = client_limits_db[selected_client][size_group]["radial"]
    effective_max_axial = min(limit_wear, limit_client_axial)
    effective_max_radial = min(limit_radial, limit_client_radial)
else:
    effective_max_axial = limit_wear
    effective_max_radial = limit_radial

st.info(f"🎯 **Критерий отбраковки:** Осевой: **{effective_max_axial:.2f} мм**, Радиальный: **{effective_max_radial:.2f} мм**")
st.markdown("---")

# --- Ввод замеров ---
col_a, col_b = st.columns(2)
with col_a: size_a = st.number_input("Размер 'А' (выдвинут), мм:", value=10.0)
with col_b: size_b = st.number_input("Размер 'Б' (разгружен), мм:", value=5.5)
measured_radial = st.number_input("Фактический радиал. люфт, мм:", value=0.4)
calc_axial = size_a - size_b

# --- Результат ---
if calc_axial > effective_max_axial or measured_radial > effective_max_radial:
    st.error(f"🚨 КРИТИЧЕСКИЙ ИЗНОС! Осевой: {calc_axial:.2f} мм, Рад: {measured_radial:.2f} мм")
else:
    st.success(f"✔ ЛЮФТ В НОРМЕ. Осевой: {calc_axial:.2f} мм, Рад: {measured_radial:.2f} мм")
