import streamlit as st
from datetime import datetime

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="Калькулятор люфта ВЗД", layout="wide")
st.title("📏 Расчет осевого люфта шпинделя ВЗД")
st.caption("МЕТОДИКА КОНТРОЛЯ ИЗНОСА ПО РЕГЛАМЕНТАМ ИНТИ")
st.markdown("---")

# Верификация ИНТИ (HTML блок)
st.markdown(
    '<div style="color: #374151; font-size: 13px; background-color: #FAFAFA; padding: 16px; border-radius: 6px; border: 1px solid #E5E7EB; border-left: 4px solid #1E3A8A;">'
    '<b>Верификация:</b> СТО ИНТИ S.QS.7 (п. 7.4.3, 7.5.1) и S.QS.8 (п. 5.7.2).<br>'
    'Оценка износа шпиндельной секции по критериям безопасной эксплуатации.'
    '</div>', 
    unsafe_allow_html=True
)

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.header("Параметры")
well_number = st.sidebar.text_input("Скважина:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("Инженер:", value="Иванов И.И.")
selected_client = st.sidebar.selectbox("Заказчик:", ["ПАО Роснефть", "ПАО Газпром / Газпромнефть", "ПАО Лукойл", "🔄 Без учета"])

# --- БАЗА ДАННЫХ И ЛОГИКА ---
# Внутренняя база жестких лимитов Заказчиков
client_limits_db = {
    "ПАО Роснефть": {"малый": {"axial": 3.5, "radial": 1.0}, "средний": {"axial": 4.0, "radial": 1.2}, "большой": {"axial": 5.0, "radial": 1.5}},
    "ПАО Газпром / Газпромнефть": {"малый": {"axial": 4.0, "radial": 1.2}, "средний": {"axial": 4.5, "radial": 1.5}, "большой": {"axial": 5.0, "radial": 2.0}},
    "ПАО Лукойл": {"малый": {"axial": 4.0, "radial": 1.2}, "средний": {"axial": 5.0, "radial": 1.6}, "большой": {"axial": 5.5, "radial": 2.2}}
}

# Встроенная база ВЗД
base_vzd = {
    "Радиус-Сервис": {"73 мм": {"limit": 6.0, "radial_limit": 1.0, "group": "малый"}, "172 мм": {"limit": 10.0, "radial_limit": 1.5, "group": "средний"}},
    "NOV": {"5''": {"limit": 7.94, "radial_limit": 1.2, "group": "малый"}, "7''": {"limit": 11.11, "radial_limit": 1.5, "group": "средний"}},
    "ВНИИБТ": {"Д-73": {"limit": 3.0, "radial_limit": 1.0, "group": "малый"}, "ДГР-172": {"limit": 6.0, "radial_limit": 1.5, "group": "средний"}},
    "НГТ": {"ДР-120": {"limit": 8.0, "radial_limit": 1.2, "group": "малый"}, "ДР-240": {"limit": 11.0, "radial_limit": 1.8, "group": "большой"}}
}

# Выбор оборудования
brand = st.selectbox("1. Производитель:", list(base_vzd.keys()))
model = st.selectbox("2. Габарит/Модель:", list(base_vzd[brand].keys()))

# Параметры из базы
data = base_vzd[brand][model]
limit_wear = data["limit"]
limit_radial_wear = data["radial_limit"]
size_group = data["group"]

# Логика сравнения
if selected_client != "🔄 Без учета":
    c_lim = client_limits_db[selected_client][size_group]
    eff_ax = min(limit_wear, c_lim["axial"])
    eff_rad = min(limit_radial_wear, c_lim["radial"])
    st.info(f"Завод: {limit_wear}мм/Р{limit_radial_wear}мм | Заказчик: {c_lim['axial']}мм/Р{c_lim['radial']}мм")
    st.warning(f"🔥 **Итоговый критерий:** {eff_ax:.2f} мм (Осевой) | {eff_rad:.2f} мм (Радиальный)")
else:
    eff_ax = limit_wear
    eff_rad = limit_radial_wear
    st.caption(f"ℹ Порог: {eff_ax:.2f} мм (Осевой) | {eff_rad:.2f} мм (Радиальный)")

# --- ВВОД И РАСЧЕТ ---
st.markdown("---")
st.markdown("### 📋 Замеры")
col1, col2 = st.columns(2)
with col1:
    size_a = st.number_input("Размер 'А' (выдвинут), мм:", value=10.0)
    size_b = st.number_input("Размер 'Б' (разгружен), мм:", value=5.5)
    delta = size_a - size_b
with col2:
    rad = st.number_input("Радиальный люфт (ИЧ), мм:", value=0.4)

# Проверка
if delta > eff_ax or rad > eff_rad:
    st.error("🚨 КРИТИЧЕСКИЙ ИЗНОС! СПУСК ЗАПРЕЩЕН!")
elif delta <= 0:
    st.warning("⚠ Ошибка: А должно быть > Б")
else:
    st.success("✔ ЛЮФТ В НОРМЕ. Допущен.")

# --- ОТЧЕТ (HTML) ---
st.markdown("---")
st.subheader("📥 Бланк замера")
rep_html = f"""
<div style='border:2px solid #1E3A8A; padding:20px; font-family:sans-serif;'>
    <h3>Акт: ВЗД {brand} {model}</h3>
    <p><b>Скважина:</b> {well_number} | <b>Инженер:</b> {engineer_name}</p>
    <p><b>Замер:</b> А={size_a}мм, Б={size_b}мм | <b>Осевой:</b> {delta:.2f}мм | <b>Рад.:</b> {rad}мм</p>
    <p><b>Норматив:</b> {selected_client} | Статус: <b>{'ОК' if delta <= eff_ax and rad <= eff_rad else 'БРАК'}</b></p>
    <p style='font-size:10px;'>СТО ИНТИ S.QS.7 / S.QS.8 | © Траектория-Сервис</p>
</div>
"""
st.markdown(rep_html, unsafe_allow_html=True)
st.info("💡 Ctrl+P -> Сохранить в PDF")
