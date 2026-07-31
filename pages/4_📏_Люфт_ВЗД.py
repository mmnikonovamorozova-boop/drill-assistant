import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Калькулятор люфта ВЗД", layout="wide")

st.title("📏 Расчет осевого люфта шпинделя ВЗД")
st.caption("МЕТОДИКА КОНТРОЛЯ ИЗНОСА ОПОР ШПИНДЕЛЯ ПО РЕГЛАМЕНТАМ ПОСТАВЩИКОВ")
st.markdown("---")

well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")
vzd_passport_number = st.sidebar.text_input("Серийный номер ВЗД по паспорту:", value="№ 6677")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
report_text = ""

if "custom_vzd" not in st.session_state:
    st.session_state.custom_vzd = {}

# Официальная встроенная база данных ВЗД
base_vzd = {
    "Радиус-Сервис": {
        "43 мм": 6.0, "54 мм": 6.0, "73 мм": 6.0, "75 мм": 6.0, 
        "95 мм": 8.0, "98 мм": 8.0, "106 мм": 8.0, "120 мм": 8.0, "127 мм": 8.0,
        "165 мм": 10.0, "172 мм": 10.0, "195 мм": 10.0, "210 мм": 10.0, "240 мм": 10.0
    },
    "Гидробур-Сервис": {
        "95 мм": 1.0, "106 мм": 1.0, "120 мм": 1.0, "178 мм": 1.0, "210 мм": 1.0, "240 мм": 1.0
    },
    "NOV": {
        "5'' (Лимит: 5/16'')": 7.94, 
        "6-1/2'' (Лимит: 7/16'')": 11.11, 
        "7'' (Лимит: 7/16'')": 11.11, 
        "8'' (Лимит: 1/2'')": 12.70, 
        "9-5/8'' (Лимит: 11/16'')": 17.46
    },
    "НГТ": {
        "ДР-120.NGT.7/8.43.20.M2": 8.0, "ДР-120.NGT.7/8.59.M2 ТС": 8.0,
        "ДР-165.NGT.7/8.45.38.M1": 9.0, "ДР-178.NGT.7/8.61.45.M25": 9.0,
        "ДР-210.NGT.7/8.60.60.M2": 10.0, "ДР-240.NGT.3/4.62.70.M1": 11.0
    },
    "ВНИИБТ": {
        "Д-43 / 2Д-43 / 2Д-43-01": 1.5, "Д1-43": 2.0, "Д1-55": 3.0,
        "Д-73 / ДР-73 / Д-76М": 3.0, "ДР-73С / ДР-73ОПН": 3.5, "Д-88 / ДР-88": 4.0,
        "ДВ-95 / Д-106 / Д-106ПН / Д3-106МР / ДР3-106МР": 3.0,
        "ДР3-95М / ДР4-95С / ДР5-95С / ДР5-106 / Д1-105 / Д3-106М / ДР3-106М / ДР3-106ТС / ДР4-106 / ДР3-120 / ДР3-120Н / ДР3-120С / ДГР-120ТСЭ / Д3-127М / ДР3-127М": 5.0,
        "ДГР-165 / ДГР-172 / ДГР-172С / ДГР1-172 / ДГР3-172 / ДГР-178М / ДР-178М / ДГР-195М / ДГР-195С / ДГР-240М / ДР1-240М": 6.0,
        "ДГР3-172Н / SM700 / SM.H700 / ДГР-210 / ДГР1-240": 10.0
    }
}

brands_list = list(base_vzd.keys()) + ["➕ НОВЫЙ ПОСТАВЩИК / МОДЕЛЬ"]
selected_brand = st.selectbox("1. Выберите производителя оборудования ВЗД:", brands_list)

limit_wear = 0.0
vzd_model_name = ""

# Интеграция американского дюймового конвертера для NOV
if selected_brand == "NOV":
    st.warning("🇺🇸 ВЗД Американского производства (NOV). Паспортные лимиты пересчитаны из дюймов в метрическую систему (1 дюйм = 25.4 мм)")
    
    # Экспресс-конвертер в реальном времени
    st.markdown("**🔄 Взаимный промысловый конвертер (Дюймы ⇄ Миллиметры):**")
    c_inch = st.number_input("Ввести значение из паспорта в дюймах (Inch):", value=0.4375, step=0.0625, format="%.4f")
    st.caption(f"📐 Результат конвертации в метрическую систему: **{round(c_inch * 25.4, 2)} мм**")
    st.markdown("---")

if selected_brand == "➕ НОВЫЙ ПОСТАВЩИК / МОДЕЛЬ":
    st.success("🛠️ Окно добавления нового оборудования в локальную базу данных:")
    custom_brand = st.text_input("Введите название завода/поставщика:", value="Буринтех")
    custom_model = st.text_input("Введите габарит или шифр серии двигателя (например, 172ТС):", value="172 мм")
    custom_limit = st.number_input("Укажите паспортный предел осевого люфта, мм:", value=5.0, step=0.1)
    
    if st.button("💾 Сохранить и внести двигатель в реестр"):
        if custom_brand and custom_model:
            if custom_brand not in st.session_state.custom_vzd:
                st.session_state.custom_vzd[custom_brand] = {}
            st.session_state.custom_vzd[custom_brand][custom_model] = custom_limit
            st.toast(f"Двигатель {custom_brand} {custom_model} успешно добавлен в списки!", icon="✔️")
            
    vzd_model_name = custom_brand + " " + custom_model
    limit_wear = custom_limit

else:
    current_brand_models = base_vzd[selected_brand].copy()
    if selected_brand in st.session_state.custom_vzd:
        current_brand_models.update(st.session_state.custom_vzd[selected_brand])
        
    selected_diameter = st.selectbox("2. Выберите габарит или серию двигателя:", list(current_brand_models.keys()))
    limit_wear = current_brand_models[selected_diameter]
    vzd_model_name = selected_brand + " " + selected_diameter
    st.caption("ℹ️ Пороговый критерий износа шпинделя: " + str(limit_wear) + " мм")

st.markdown("---")

# Ввод замеров
size_a = st.number_input("Размер 'А' (Вал полностью выдвинут вниз под своим весом), мм:", value=10.0, step=0.1)
size_b = st.number_input("Размер 'Б' (Двигатель опущен на стол ротора и разгружен), мм:", value=5.5, step=0.1)

calculated_delta = size_a - size_b

st.markdown("### РЕЗУЛЬТАТЫ РАСЧЕТА:")
st.write("**Фактический осевой люфт (Δh):** " + str(round(calculated_delta, 1)) + " мм")
st.write("**Допустимый предел по паспорту:** " + str(limit_wear) + " мм")

if calculated_delta > limit_wear:
    res_text = "🚨 КРИТИЧЕСКИЙ ИЗНОС ОПОР ШПИНДЕЛЯ! СПУСК В СКВАЖИНУ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕН!"
    st.error(res_text)
elif calculated_delta <= 0:
    res_text = "⚠️ Ошибка измерений! Размер 'А' должен быть больше размера 'Б'. Перепроверьте ИЧ."
    st.warning(res_text)
else:
    res_text = "✔️ ЛЮФТ В НОРМЕ. Двигатель ДОПУЩЕН к спуску в скважину."
    st.success(res_text)

# Генерация красивой печатной формы Акта
html_vzd = "<div style='border:3px solid #1E3A8A; padding:25px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'>"
html_vzd += "<h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРЬЯ-СЕРВИС»</h2>"
html_vzd += "<h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>АКТ ТЕХНИЧЕСКОГО КОНТРОЛЯ ШПИНДЕЛЯ ВЗД</h3>"
html_vzd += "<hr style='border:1px solid #1E3A8A; margin-bottom:20px;'>"
html_vzd += "<p><b>Дата/Время:</b> " + current_time + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> " + field_name + "</p>"
html_vzd += "<p><b>Объект / Скважина:</b> " + well_number + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> " + engineer_name + "</p>"
html_vzd += "<p><b>Оборудование:</b> ВЗД " + vzd_model_name + " (Паспорт: " + vzd_passport_number + ")</p>"
html_vzd += "<p><b>Параметры замера шпинделя:</b> Размер А = " + str(size_a) + " мм | Размер Б = " + str(size_b) + " мм</p>"
html_vzd += "<h4 style='color:#1E3A8A; margin-top:20px; border-bottom:1px solid #D1D5DB; padding-bottom:5px;'>ЗАКЛЮЧЕНИЕ ПРОВЕРКИ:</h4>"
html_vzd += "<p style='font-size:15px;'>Фактический осевой люфт шпинделя составляет <b>" + str(round(calculated_delta, 1)) + " мм</b> при паспортном лимите износа <b>" + str(limit_wear) + " мм</b>.</p>"
html_vzd += "<p style='font-size:16px; color:" + ("red" if calculated_delta > limit_wear else "green") + ";'><b>СТАТУС: " + res_text + "</b></p>"
html_vzd += "<p style='font-size:12px; color:#6B7280; text-align:center; margin-top:35px; border-top:1px dashed #D1D5DB; padding-top:10px;'>Сгенерировано в цифровом модуле • Для печати нажмите Ctrl + P</p>"
html_vzd += "</div>"

if report_text == "":
    st.markdown("---")
    st.subheader("📥 Официальный бланк замера для рапорта:")
    st.markdown(html_vzd, unsafe_allow_html=True)
