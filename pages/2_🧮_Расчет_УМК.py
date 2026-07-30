import streamlit as st
import numpy as np

st.title("🧮 Калькулятор момента ключа УМК")
st.write("Расчет уставки моментомера с учетом геометрических погрешностей")

m_pasport = st.number_input("Паспортный момент затяжки резьбы, кН*м", value=20.0, step=1.0)
length = st.number_input("Фактическая длина плеча ключа УМК, м", value=1.4, step=0.1)
angle = st.slider("Угол натяжения троса, градусов", min_value=10, max_value=90, value=80, step=1)

angle_rad = np.radians(angle)
sin_alpha = np.sin(angle_rad)
pogreshnost = (1.0 - sin_alpha) * 100
m_ustavka = m_pasport / sin_alpha

st.markdown("---")
st.subheader("📋 Результаты расчета:")
st.info(f"📐 Погрешность из-за угла (п. 5.1.1.8), %: {pogreshnost:.1f}")
st.success(f"🔧 УСТАНОВИТЬ НА МОМЕНТОМЕРЕ КЛЮЧА, кН*м: {m_ustavka:.1f}")
st.warning("⚠️ ВНИМАНИЕ: Учтите поправку моментомера! Недокрепление резьбы КНБК ведет к аварии.")
