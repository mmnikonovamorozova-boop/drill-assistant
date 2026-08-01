import streamlit as st
from datetime import datetime

# --- 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="Калькулятор люфта ВЗД", layout="wide")

st.title("📏 Комплексный расчет износа и люфтов шпинделя ВЗД")
st.caption("МЕТОДИКА КОНТРОЛЯ ИЗНОСА ОПОР ШПИНДЕЛЯ ПО РЕГЛАМЕНТАМ ПОСТАВЩИКОВ И ЗАКАЗЧИКОВ")
st.markdown("---")

# Сдержанная техническая отметка о соответствии стандартам ИНТИ
st.markdown(
    "<div style='color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #1E3A8A; margin-bottom: 20px; line-height: 1.5; font-family: Arial, sans-serif;'> "
    "<b>Верификация стандартами:</b> Данный модуль контроля осевого износа шпиндельной секции ВЗД разработан в строгом соответствии с требованиями отраслевых стандартов "
    "<b>СТО ИНТИ S.QS.7 (п. 7.4.3 «Верификация закупаемой продукции», п. 7.5.1 «Управление производством и предоставлением услуг»)</b> в части проведения обязательной входной инспекции, проверки критических параметров и оценки соответствия забойных двигателей критериям безопасной эксплуатации на устье, "
    "а также <b>СТО ИНТИ S.QS.8 (п. 5.7.2 «Управление оборудованием для мониторинга и измерений»)</b> в части обязательного контроля исправности и метрологического подтверждения применяемого мерительного инструмента на буровой площадке."
    "</div>", 
    unsafe_allow_html=True
)

# --- 2. ВЫБОР ЗАКАЗЧИКА ПО ЦЕНТРУ СТРАНИЦЫ ---
selected_client = st.selectbox(
    "1. Выберите Заказчика (Недропользователя) для применения ограничений:", 
    ["ПАО Роснефть", "ПАО Газпром", "ПАО Лукойл", "🔄 Без учета ограничений Заказчика"]
)
st.markdown("---")

# --- 3. СБОР МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")
vzd_passport_number = st.sidebar.text_input("Серийный номер ВЗД по паспорту:", value="№ 6677")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
report_text = ""

# Инициализация локальной пользовательской базы в сессии
if "custom_vzd" not in st.session_state:
    st.session_state.custom_vzd = {}

# --- 4. НОРМАТИВНЫЕ БАЗЫ ДАННЫХ ---
client_limits_db = {
    "ПАО Роснефть": {"малый": 3.5, "средний": 4.0, "большой": 5.0},
    "ПАО Газпром": {"малый": 4.0, "средний": 4.5, "большой": 5.0},
    "ПАО Лукойл": {"малый": 4.0, "средний": 5.0, "большой": 5.5}
}

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
selected_brand = st.selectbox("2. Выберите производителя оборудования ВЗД:", brands_list)

limit_wear = 0.0
vzd_model_name = ""
size_group = "средний"

# --- 5. ЛОГИКА ДЛЯ NOV ---
if selected_brand == "NOV":
    st.warning("🇺🇸 ВЗД Американского производства (NOV). Паспортные лимиты автоматически пересчитаны в метрическую систему до сотых долей.")
    st.markdown("**🔄 Промысловый конвертер долей дюйма (выберите значения из паспорта):**")
    
    col_num, col_den = st.columns(2)
    with col_num:
        numerator = st.selectbox("Числитель дроби:", [1, 3, 5, 7, 9, 11, 13, 15], index=3)
    with col_den:
        denominator = st.selectbox("Знаменатель дроби:", [2, 4, 8, 16], index=3)
        
    mm_result = (numerator / denominator) * 25.4
    st.success(f"📐 Результат перевода доли **{numerator}/{denominator}''** в метрическую систему: **{mm_result:.2f} мм**")
    st.markdown("---")

# --- 6. ОБРАБОТКА ДОБАВЛЕНИЯ НОВОГО ОБОРУДОВАНИЯ ---
if selected_brand == "➕ НОВЫЙ ПОСТАВЩИК / МОДЕЛЬ":
    st.success("🛠️ Окно добавления нового оборудования в локальную базу данных:")
    custom_brand = st.text_input("Введите название завода/поставщика:", value="Буринтех")
    custom_model = st.text_input("Введите габарит или шифр серии двигателя (например, 172ТС):", value="172 мм")
    custom_limit = st.number_input("Установите предельный осевой люфт по паспорту (мм):", min_value=0.0, max_value=25.0, value=5.5, step=0.1)
    custom_group = st.selectbox("Укажите категорию габарита для привязки норм Заказчиков:", ["малый", "средний", "большой"], index=1)
    
    if st.button("💾 Сохранить и внести двигатель в реестр"):
        if custom_brand and custom_model:
            if custom_brand not in st.session_state.custom_vzd:
                st.session_state.custom_vzd[custom_brand] = {}
            st.session_state.custom_vzd[custom_brand][custom_model] = {
                "axial": custom_limit, 
                "group": custom_group
            }
            st.toast(f"Двигатель {custom_brand} {custom_model} успешно добавлен в списки!", icon="✔️")
            
    vzd_model_name = custom_brand + " " + custom_model
    limit_wear = custom_limit
    size_group = custom_group

else:
    current_brand_models = base_vzd[selected_brand].copy()
    if selected_brand in st.session_state.custom_vzd:
        current_brand_models.update(st.session_state.custom_vzd[selected_brand])
        
    selected_diameter = st.selectbox("3. Выберите габарит / шифр модели:", list(current_brand_models.keys()))
    vzd_model_name = selected_brand + " " + selected_diameter
    
    if isinstance(current_brand_models[selected_diameter], dict):
        limit_wear = current_brand_models[selected_diameter]["axial"]
        size_group = current_brand_models[selected_diameter]["group"]
    else:
        limit_wear = current_brand_models[selected_diameter]
        small_markers = ["43", "54", "73", "75", "88", "95", "98", "106", "120", "127", "5''"]
        large_markers = ["195", "210", "240", "8''", "9-5/8''"]
        if any(m in selected_diameter for m in small_markers):
            size_group = "малый"
        elif any(m in selected_diameter for m in large_markers):
            size_group = "большой"
        else:
            size_group = "средний"

# Расчет номинала (50% от лимита износа)
limit_nominal = limit_wear * 0.50

# --- 7. АЛГОРИТМ СРАВНЕНИЯ И СВЕРКИ С ЗАКАЗЧИКАМИ ---
if selected_client != "🔄 Без учета ограничений Заказчика":
    client_rule_axial = client_limits_db[selected_client][size_group]
    effective_max_axial = min(limit_wear, client_rule_axial)
    st.info(f"🔷 **Нормы контроля:** Паспорт завода = {limit_wear:.2f} мм | Ограничение {selected_client} = {client_rule_axial:.2f} мм")
    st.warning(f"🎯 **Целевой критерий отбраковки на устье:** Осевой до **{effective_max_axial:.2f} мм**")
else:
    effective_max_axial = limit_wear
    st.info(f"🎯 **Целевой критерий отбраковки (Паспортный):** Осевой до **{effective_max_axial:.2f} мм**")

# --- 8. ВВОД ФАКТИЧЕСКИХ ЗАМЕРОВ ---
st.markdown("---")
st.subheader("📥 4. Фактические замеры на устье скважины")
col_input1, col_input2 = st.columns(2)

with col_input1:
    size_a = st.number_input("Размер 'А' (шпиндель максимально выдвинут), мм:", min_value=0.0, max_value=50.0, value=10.0, step=0.01)
with col_input2:
    size_b = st.number_input("Размер 'Б' (шпиндель максимально разгружен), мм:", min_value=0.0, max_value=50.0, value=5.5, step=0.01)

calculated_delta = size_a - size_b

# --- 9. ПОЛНАЯ ОЦЕНКА, ИНДИКАЦИЯ И ВЫВОДЫ ---
st.markdown("### РЕЗУЛЬТАТЫ РАСЧЕТА:")
st.write(f"**Фактический осевой люфт (Δh):** {calculated_delta:.2f} мм")
st.write(f"**Допустимый предел по паспорту:** {limit_wear:.2f} мм")

if calculated_delta > effective_max_axial:
    res_text = "🚨 КРИТИЧЕСКИЙ ИЗНОС ОПОР ШПИНДЕЛЯ! СПУСК В СКВАЖИНУ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕН!"
    st.error(res_text)
elif calculated_delta <= 0:
    res_text = "⚠️ Ошибка измерений! Размер 'А' должен быть больше размера 'Б'. Перепроверьте ИЧ."
    st.warning(res_text)
else:
    res_text = "✔️ ЛЮФТ В НОРМЕ. Двигатель ДОПУЩЕН к спуску в скважину."
    st.success(res_text)

# --- 10. БЕЗОПАСНАЯ ГЕНЕРАЦИЯ КОРПОРАТИВНОГО HTML-АКТА ЧЕРЕЗ F-СТРОКИ ---
act_status_color = "red" if calculated_delta > effective_max_axial else "green"

# Переводим переменные в безопасный строковый формат на случай, если они пустые
c_time = str(current_time) if 'current_time' in locals() else ""
f_name = str(field_name) if 'field_name' in locals() else ""
w_num = str(well_number) if 'well_number' in locals() else ""
e_name = str(engineer_name) if 'engineer_name' in locals() else ""
m_name = str(vzd_model_name) if 'vzd_model_name' in locals() else ""
p_num = str(vzd_passport_number) if 'vzd_passport_number' in locals() else ""

html_vzd = f"""
<div style='border:3px solid #1E3A8A; padding:25px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'>
    <h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРЬЯ-СЕРВИС»</h2>
    <h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>АКТ ТЕХНИЧЕСКОГО КОНТРОЛЯ ШПИНДЕЛЯ ВЗД</h3>
    <hr style='border:1px solid #1E3A8A; margin-bottom:20px;'>
    <p><b>Дата/Время:</b> {c_time} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> {f_name}</p>
    <p><b>Объект / Скважина:</b> {w_num} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> {e_name}</p>
    <p><b>Оборудование:</b> ВЗД {m_name} (Паспорт: {p_num})</p>
    <p><b>Параметры замера шпинделя:</b> Размер А = {size_a:.2f} мм | Размер Б = {size_b:.2f} мм</p>
    <h4 style='color:#1E3A8A; margin-top:20px; border-bottom:1px solid #D1D5DB; padding-bottom:5px;'>ЗАКЛЮЧЕНИЕ ПРОВЕРКИ:</h4>
    <p style='font-size:15px;'>Фактический осевой люфт шпинделя составляет <b>{calculated_delta:.2f} мм</b> при паспортном лимите износа <b>{limit_wear:.2f} мм</b>.</p>
    <p style='font-size:16px; color:{act_status_color};'><b>СТАТУС: {res_text}</b></p>
    <p style='font-size:12px; color:#6B7280; text-align:center; margin-top:35px; border-top:1px dashed #D1D5DB; padding-top:10px;'>Сгенерировано в цифровом модуле • Для печати нажмите Ctrl + P</p>
</div>
"""

# Жесткий вывод без каких-либо условий проверки строки report_text
st.markdown("---")
st.subheader("📥 Официальный бланк замера для рапорта:")
st.markdown(html_vzd, unsafe_allow_html=True)

# --- 11. ФУТЕРЫ СТРАНИЦЫ И ИНСТРУКЦИЯ ПО ПЕЧАТИ ---
st.markdown(" ")
st.info("💡 **Как распечатать или сохранить в PDF:** Нажмите комбинацию клавиш **`Ctrl + P`** (или три точки браузера ➡️ Печать), выберите принтер «Сохранить как PDF» и заберите готовый документ!")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 30px;'><b>Разработчик цифрового модуля:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ • Цифровая экосистема ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
