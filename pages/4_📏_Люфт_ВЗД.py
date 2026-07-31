import streamlit as st

st.set_page_config(page_title="Калькулятор люфта ВЗД", layout="wide")

st.title("📏 Расчет осевого люфта шпинделя ВЗД")
st.caption("МЕТОДИКА КОНТРОЛЯ ИЗНОСА ОПОР ШПИНДЕЛЯ ПО РЕГЛАМЕНТУ ООО 'ТРАЕКТОРЬЯ-СЕРВИС'")
st.markdown("---")

# Данные скважины из бокового меню
st.sidebar.header("📝 Данные для рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")

st.info("Инструкция: Замер Δh выполняется дважды для исключения погрешности перекоса. Технолог обязан ЛИЧНО контролировать магнит и стойку ИЧ на мостках.")

# База данных по габаритам ВЗД
vzd_database = {
    "98 мм": {"limit": 4.5, "info": "Малый габарит. Паспортный люфт нового: 1.0 - 2.0 мм."},
    "106 мм": {"limit": 4.5, "info": "Малый габарит. Паспортный люфт нового: 1.0 - 2.0 мм."},
    "120 мм": {"limit": 4.5, "info": "Малый габарит. Паспортный люфт нового: 1.0 - 2.0 мм."},
    "172 мм": {"limit": 5.0, "info": "Средний габарит. Паспортный люфт нового: 1.0 - 3.0 мм."},
    "240 мм": {"limit": 6.0, "info": "Большой габарит. Паспортный люфт нового: 1.5 - 3.5 мм."}
}

# Выбор оборудования
selected_brand = st.selectbox("Производитель оборудования ВЗД:", ["Радиус-Сервис", "ВНИИБТ", "Гидробур", "НГТ", "NOV"])
selected_diameter = st.selectbox("Диаметр двигателя (типоразмер ВЗД):", list(vzd_database.keys()))

limit_wear = vzd_database[selected_diameter]["limit"]
st.caption("ℹ️ Паспортная справка: " + vzd_database[selected_diameter]["info"])

st.markdown("---")

# Ввод замеров
size_a = st.number_input("Размер 'А' (Вал полностью выдвинут вниз под своим весом), мм:", value=10.0, step=0.1)
size_b = st.number_input("Размер 'Б' (Двигатель опущен на стол ротора и разгружен), мм:", value=5.5, step=0.1)

# Физический расчет перемещения вала
calculated_delta = size_a - size_b

st.markdown("### РЕЗУЛЬТАТЫ РАСЧЕТА:")
st.write("**Фактический осевой люфт (Δh):** " + str(round(calculated_delta, 1)) + " мм")
st.write("**Допустимый предел по паспорту:** " + str(limit_wear) + " мм")

if calculated_delta > limit_wear:
    res_text = "🚨 КРИТИЧЕСКИЙ ИЗНОС ОПОР ШПИНДЕЛЯ! Люфт превышает паспортный лимит. СПУСК В СКВАЖИНУ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕН!"
    st.error(res_text)
elif calculated_delta <= 0:
    res_text = "⚠️ Ошибка измерений! Размер 'А' должен быть больше размера 'Б'. Проверьте шкалу ИЧ стойки."
    st.warning(res_text)
else:
    res_text = "✔️ ЛЮФТ В НОРМЕ. Опорно-торцевые узлы шпинделя исправны. Двигатель ДОПУЩЕН к спуску в скважину."
    st.success(res_text)

# Автоматическое формирование печатного рапорта
html_vzd = "<div style='border:3px solid #1E3A8A; padding:25px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'>"
html_vzd += "<h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРЬЯ-СЕРВИС»</h2>"
html_vzd += "<h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>АКТ ТЕХНИЧЕСКОГО КОНТРОЛЯ ШПИНДЕЛЯ ВЗД</h3>"
html_vzd += "<hr style='border:1px solid #1E3A8A; margin-bottom:20px;'>"
html_vzd += "<p><b>Скважина / Куст:</b> " + well_number + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> " + engineer_name + "</p>"
html_vzd += "<p><b>Оборудование:</b> ВЗД " + selected_brand + " " + selected_diameter + "</p>"
html_vzd += "<p><b>Параметры замера:</b> Размер А = " + str(size_a) + " мм | Размер Б = " + str(size_b) + " мм</p>"
html_vzd += "<h4 style='color:#1E3A8A; margin-top:20px; border-bottom:1px solid #D1D5DB; padding-bottom:5px;'>ЗАКЛЮЧЕНИЕ ПРОВЕРКИ:</h4>"
html_vzd += "<p style='font-size:15px;'>Фактический осевой люфт шпинделя составляет <b>" + str(round(calculated_delta, 1)) + " мм</b> при паспортном лимите износа <b>" + str(limit_wear) + " мм</b>.</p>"
html_vzd += "<p style='font-size:16px; color:" + ("red" if calculated_delta > limit_wear else "green") + ";'><b>СТАТУС: " + res_text + "</b></p>"
html_vzd += "<p style='font-size:12px; color:#6B7280; text-align:center; margin-top:35px; border-top:1px dashed #D1D5DB; padding-top:10px;'>Для вывода на печать нажмите Ctrl + P</p>"
html_vzd += "</div>"

st.markdown("---")
st.subheader("📥 Готовый бланк замера для рапорта:")
st.markdown(html_vzd, unsafe_allow_html=True)
