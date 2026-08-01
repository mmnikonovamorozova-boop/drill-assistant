import streamlit as st
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Расчет УМК", layout="wide")

st.title("🧮 Совмещенный расчет момента ключа УМК")
st.caption("КОРРЕКТИРОВКА УСТАВКИ С УЧЕТОМ ГЕОМЕТРИИ КЛЮЧА, ТОЛЩИНЫ КАНАТА И УГЛА НАТЯЖЕНИЯ")
st.markdown("---")

well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

st.info("Инструкция: Замерьте фактическое плечо рулеткой от оси трубы до центра пальца ключа. Введите диаметр троса и угол для получения точной уставки.")

# База данных стандартных буровых ключей для справки
keys_database = {
    "УМК-1 (Ключ машинный универсальный)": 1.40,
    "УМК-2 (Увеличенный габарит)": 1.60,
    "Ключ Халилок (Стандартный промысловый)": 1.20,
    "КЛ-150 / КТГУ (Легкие трубные ключи)": 1.00,
    "🛠️ Редкий / Импортный ключ": 1.40
}

# 1. Выбор модели для автоматической подсказки номинала
selected_key_model = st.selectbox("1. Выберите модель используемого бурового ключа:", list(keys_database.keys()))
length_nom = keys_database[selected_key_model]

if selected_key_model != "🛠️ Редкий / Импортный ключ":
    st.caption(f"ℹ️ Справка: Паспортный номинал плеча для этой модели составляет **{length_nom:.2f} м**.")

# 2. Ручной занос фактического замера рулеткой с мостков
length_measured = st.number_input("2. Введите фактическую длину плеча по замеру рулеткой (от оси трубы до центра пальца), м:", value=float(length_nom), step=0.01, format="%.2f")

st.markdown("---")

# 3. Ввод параметров намотки троса и угла
m_pasport = st.number_input("3. Паспортный момент затяжки резьбового соединения КНБК, кН*м:", value=20.0, step=1.0)

col_t1, col_t2 = st.columns(2)
with col_t1:
    thickness_mm = st.number_input("Фактическая толщина (диаметр) каната/троса лебедки, мм:", value=22.0, step=1.0)
with col_t2:
    angle = st.slider("Фактический угол натяжения троса ключа (альфа), градусов:", min_value=10, max_value=90, value=70, step=1)

# Математический пересчет по формуле
# Радиус намотки троса (дельта r)
delta_r = (thickness_mm / 2.0) / 1000.0

# Итоговое плечо = Замер рулеткой + Радиус троса
length_total_fact = length_measured + delta_r

# Считаем синус угла
angle_rad = np.radians(angle)
sin_alpha = np.sin(angle_rad)

# Расчет необходимой силы тяги лебедки
f_tyagi = m_pasport / (length_total_fact * sin_alpha)

# Расчет уставки для шкалы моментомера (который проградуирован по паспортному L_ном)
m_ustavka = f_tyagi * length_nom

# Совмещенная погрешность системы в %
pogreshnost = abs(1.0 - (length_nom / length_total_fact) * sin_alpha) * 100

st.markdown("---")
st.subheader("📋 РЕЗУЛЬТАТЫ КОРРЕКТИРОВКИ:")

st.write(f"**Номинальное плечо по паспорту (L_ном):** {length_nom:.2f} м")
st.write(f"**Плечо по факту вашего замера рулеткой:** {length_measured:.2f} м")
st.write(f"**Итоговое плечо с учетом намотки троса (L_факт):** {length_total_fact:.4f} м (Смещение оси на {delta_r*1000:.1f} мм)")
st.write(f"**Необходимое усилие натяжения лебедки (F_тяги):** {f_tyagi:.2f} кН")
st.write(f"**Совмещенная погрешность (Геометрия + Трос + Угол):** {pogreshnost:.1f} %")

st.success(f"🔧 ЗНАЧЕНИЕ ДЛЯ УСТАНОВКИ НА ШКАЛЕ МОМЕНТОМЕРА: {m_ustavka:.2f} кН*м")

if angle < 60:
    st.error("🚨 КРИТИЧЕСКИЙ УГОЛ! По регламенту, если угол менее 60°, запрещено дотягивать резьбу завышением давления на пульте! Требуется перестановка натяжной лебедки.")
elif pogreshnost > 10.0:
    st.warning("⚠️ ВНИМАНИЕ: Совмещенная погрешность превышает 10%. Убедитесь в жесткой фиксации пальца ключа.")
else:
    st.success("✔️ Параметры затяжки находятся в безопасном технологическом диапазоне.")

# Сборка красивого HTML-бланка для рапорта
html_umk = "<div style='border:3px solid #1E3A8A; padding:25px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'> "
html_umk += "<h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРЬЯ-СЕРВИС»</h2>"
html_umk += "<h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>РЕКОМЕНДАЦИИ НА ЗАТЯЖКУ КНБК КЛЮЧОМ УМК</h3>"
html_umk += "<hr style='border:1px solid #1E3A8A; margin-bottom:20px;'>"
html_v_p = "<p><b>Дата/Время расчета:</b> " + current_time + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> " + field_name + "</p>"
html_umk += html_v_p
html_umk += "<p><b>Объект / Скважина:</b> " + well_number + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> " + engineer_name + "</p>"
html_umk += f"<p><b>Модель ключа и целевой момент резьбы:</b> {selected_key_model} | {m_pasport:.1f} кН*м</p>"
html_umk += f"<p><b>Геометрия по замеру рулеткой:</b> {length_measured:.2f} м | <b>Итоговое расчетное плечо L_факт:</b> {length_total_fact:.4f} м</p>"
html_umk += f"<p><b>Параметры троса и тяги:</b> Диаметр троса = {thickness_mm:.0f} мм | Угол натяжения = {angle}° | Погрешность = {pogreshnost:.1f}%</p>"
html_umk += "<h4 style='color:#1E3A8A; margin-top:20px; border-bottom:1px solid #D1D5DB; padding-bottom:5px;'>ТЕХНОЛОГИЧЕСКОЕ РЕШЕНИЕ ДЛЯ БУРОВОЙ БРИГАДЫ:</h4>"
html_umk += f"<p style='font-size:15px;'>Для компенсации совмещенной погрешности инструмента и создания требуемого момента сил:</p>"
html_umk += f"<p style='font-size:18px; color:green;'><b>🔧 ВЫСТАВИТЬ НА ШКАЛЕ МОМЕНТОМЕРА: {m_ustavka:.2f} кН*м</b></p>"
html_umk += "<p style='font-size:12px; color:#6B7280; text-align:center; margin-top:35px; border-top:1px dashed #D1D5DB; padding-top:10px;'>Сгенерировано в цифровом модуле расчетов УМК • Для печати распоряжения нажмите Ctrl + P</p>"
html_umk += "</div>"

st.markdown("---")
st.subheader("📥 Официальный бланк распоряжения для буровой бригады:")
st.markdown(html_umk, unsafe_allow_html=True)
