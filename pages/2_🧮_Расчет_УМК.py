import streamlit as st
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Расчет УМК", layout="wide")

st.title("🧮 Совмещенный расчет момента ключа УМК")
st.caption("КОРРЕКТИРОВКА УСТАВКИ С УЧЕТОМ ТОЛЩИНЫ КАНАТА И УГЛА НАТЯЖЕНИЯ")
st.markdown("---")

well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

st.info("Инструкция: Толстый трос увеличивает плечо (риск перекрута), а неправильный угол снижает эффективную силу (риск недокрепа). Введите параметры для расчета точной уставки.")

# Ввод исходных данных
m_pasport = st.number_input("Паспортный момент затяжки резьбового соединения, кН*м:", value=20.0, step=1.0)
length_nom = st.number_input("Паспортное (номинальное) плечо ключа L_ном, м:", value=1.4, step=0.1)

col_t1, col_t2 = st.columns(2)
with col_t1:
    thickness_mm = st.number_input("Фактическая толщина (диаметр) каната/троса лебедки, мм:", value=22.0, step=1.0)
with col_t2:
    angle = st.slider("Фактический угол натяжения троса ключа (альфа), градусов:", min_value=10, max_value=90, value=70, step=1)

# Математический пересчет по формуле с учетом фактического плеча
# 1. Переводим толщину троса из мм в метры для дельты радиуса
delta_r = (thickness_mm / 2.0) / 1000.0
length_fact = length_nom + delta_r

# 2. Считаем синус угла
angle_rad = np.radians(angle)
sin_alpha = np.sin(angle_rad)

# 3. Рассчитываем необходимую силу тяги лебедки
# F_тяги = M_паспорт / (L_факт * sin_alpha)
f_tyagi = m_pasport / (length_fact * sin_alpha)

# 4. Рассчитываем уставку моментомера по фактическому плечу L_факт
m_ustavka = f_tyagi * length_fact

# 5. Общая совмещенная погрешность системы в %
pogreshnost = abs(1.0 - (length_nom / length_fact) * sin_alpha) * 100

st.markdown("---")
st.subheader("📋 РЕЗУЛЬТАТЫ КОРРЕКТИРОВКИ:")

st.write(f"**Фактическое плечо с учетом намотки троса (L_факт):** {length_fact:.4f} м")
st.write(f"**Совмещенная погрешность системы ключа:** {pogreshnost:.1f} %")

st.success(f"🔧 ЗНАЧЕНИЕ ДЛЯ УСТАНОВКИ НА МОМЕНТОМЕРЕ: {m_ustavka:.2f} кН*м")

if angle < 60:
    st.error("🚨 КРИТИЧЕСКИЙ УГОЛ! По регламенту, если угол менее 60°, запрещено дотягивать резьбу экстремальным давлением! Переставьте натяжную лебедку под правильный угол.")
elif pogreshnost > 10.0:
    st.warning("⚠️ ВНИМАНИЕ: Совмещенная погрешность превышает 10%. Убедитесь в жесткой фиксации пальца ключа.")
else:
    st.success("✔️ Корректировка момента находится в безопасном технологическом диапазоне.")

# Сборка красивого HTML-бланка для рапорта
html_umk = "<div style='border:3px solid #1E3A8A; padding:25px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'>"
html_umk += "<h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРЬЯ-СЕРВИС»</h2>"
html_umk += "<h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>РАСПОРЯЖЕНИЕ НА ЗА ТЯЖКУ КНБК КЛЮЧОМ УМК</h3>"
html_umk += "<hr style='border:1px solid #1E3A8A; margin-bottom:20px;'>"
html_v_p = "<p><b>Дата/Время расчета:</b> " + current_time + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> " + field_name + "</p>"
html_umk += html_v_p
html_umk += "<p><b>Объект / Скважина:</b> " + well_number + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> " + engineer_name + "</p>"
html_umk += f"<p><b>Целевой паспортный момент:</b> {m_pasport:.1f} кН*м &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Номинальное плечо:</b> {length_nom:.2f} м</p>"
html_umk += f"<p><b>Параметры замера на устье:</b> Толщина троса = {thickness_mm:.0f} мм | Угол натяжения = {angle}°</p>"
html_umk += "<h4 style='color:#1E3A8A; margin-top:20px; border-bottom:1px solid #D1D5DB; padding-bottom:5px;'>ТЕХНОЛОГИЧЕСКОЕ РЕШЕНИЕ:</h4>"
html_umk += f"<p style='font-size:15px;'>С учетом совмещенной погрешности троса и угла (<b>{pogreshnost:.1f}%</b>), эффективное плечо увеличилось до <b>{length_fact:.4f} м</b>.</p>"
html_umk += f"<p style='font-size:18px; color:green;'><b>🔧 УСТАНОВИТЬ НА МОМЕНТОМЕРЕ КЛЮЧА: {m_ustavka:.2f} кН*м</b></p>"
html_umk += "<p style='font-size:12px; color:#6B7280; text-align:center; margin-top:35px; border-top:1px dashed #D1D5DB; padding-top:10px;'>Сгенерировано в цифровом модуле расчетов УМК • Для печати распоряжения нажмите Ctrl + P</p>"
html_umk += "</div>"

st.markdown("---")
st.subheader("📥 Официальный бланк распоряжения для буровой бригады:")
st.markdown(html_umk, unsafe_allow_html=True)
