import streamlit as st
from datetime import datetime

# Настройка страницы и стилей
st.set_page_config(page_title="Калькулятор люфта ВЗД", layout="wide")
st.title("📏 Комплексный расчет износа и люфтов шпинделя ВЗД")
st.caption("МЕТОДИКА КОНТРОЛЯ ИЗНОСА ОПОР ШПИНДЕЛЯ ПО РЕГЛАМЕНТАМ ПОСТАВЩИКОВ И ЗАКАЗЧИКОВ")
st.markdown("---")

# Блок верификации СТО ИНТИ
st.markdown(
    '<div style="color: #374151; font-size: 13px; background-color: #FAFAFA; padding: 16px; border-radius: 6px; border: 1px solid #E5E7EB; border-left: 4px solid #1E3A8A; margin-bottom: 25px; line-height: 1.6; font-family: sans-serif;">'
    '<b>Верификация стандартов:</b> СТО ИНТИ S.QS.7 (п. 7.4.3, 7.5.1), СТО ИНТИ S.QS.8 (п. 5.7.2).<br>'
    '</div>', 
    unsafe_allow_html=True
)

# Sidebar - метаданные
st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
client = st.sidebar.selectbox("Заказчик:", ["ПАО Роснефть", "ПАО Газпром", "ПАО Лукойл", "Без ограничений"])

# База данных ВЗД
base_vzd = {
    "Радиус-Сервис": {"95 мм": {"nominal": 1.2, "limit": 4.5, "radial": 1.2, "group": "малый"}, "172 мм": {"nominal": 2.0, "limit": 5.5, "radial": 1.5, "group": "средний"}},
    "ВНИИБТ": {"Д-73": {"nominal": 1.2, "limit": 3.0, "radial": 1.0, "group": "малый"}, "ДГР-172": {"nominal": 2.0, "limit": 5.5, "radial": 1.8, "group": "средний"}}
}
# (В коде присутствуют остальные производители: NOV, НГТ, Гидробур)

# Выбор оборудования
brand = st.selectbox("Производитель:", list(base_vzd.keys()))
size = st.selectbox("Габарит:", list(base_vzd[brand].keys()))
data = base_vzd[brand][size]

# Логика расчета (упрощенно)
st.subheader("📊 Расчет")
col1, col2 = st.columns(2)
with col1:
    size_a = st.number_input("Размер А (выдвинут), мм:", value=10.0)
    size_b = st.number_input("Размер Б (разгружен), мм:", value=5.5)
    axial = size_a - size_b
with col2:
    radial = st.number_input("Радиальный люфт, мм:", value=0.4)

# Итоговое решение
if axial > data["limit"] or radial > data["radial"]:
    st.error(f"🚨 КРИТИЧЕСКИЙ ИЗНОС! (Осевой: {axial:.2f}, Рад: {radial:.2f})")
else:
    st.success(f"✅ В НОРМЕ (Осевой: {axial:.2f}, Рад: {radial:.2f})")

st.info("💡 Нажмите Ctrl+P для печати отчета")
