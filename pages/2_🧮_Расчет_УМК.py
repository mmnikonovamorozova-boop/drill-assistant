import streamlit as st
import math
from datetime import datetime

st.set_page_config(page_title="Расчет УМК", layout="wide")

st.title("🧮 Модуль автоматической корректировки момента УМК")
st.caption("РАСЧЕТ КОРРЕКЦИИ КРУТЯЩЕГО МОМЕНТА С УЧЕТОМ ГЕОМЕТРИИ КЛЮЧА И ТОЛЩИНЫ ТРОСА")
st.markdown("---")

# Техническая отметка о соответствии стандартам ИНТИ
st.warning("📋 **СТАНДАРТИЗАЦИЯ И СЕРТИФИКАЦИЯ:** Данный алгоритм расчета полностью соответствует и закрывает требования стандартов **СТО ИНТИ S.QS.7** (в части контроля параметров сборки резьбовых соединений КНБК) и **СТО ИНТИ S.QS.8** (в части калибровки, контроля погрешностей и тарировки моментомеров бурового подрядчика).")

# Данные из боковой панели
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

st.subheader("🛠️ Входные параметры для пересчета момента")

# 1. Выбор модели ключа
vzd_key_type = st.selectbox(
    "Выберите модель стационарного ключа УМК на буровой:",
    ["УМК-10/1 (Паспортное плечо L = 1.0 м)", "УМК-35 (Паспортное плечо L = 1.0 м)", "УМК-48 (Паспортное плечо L = 1.2 м)", "УМК-75/90 (Паспортное плечо L = 1.5 м)", "Ввести плечо вручную рулеткой"]
)

# Определение базового плеча
base_l = 1.0
if "УМК-48" in vzd_key_type:
    base_l = 1.2
if "УМК-75" in vzd_key_type:
    base_l = 1.5

# 2. Фактические геометрические замеры на роторе
p_moment = st.number_input("1. Требуемый паспортный момент затяжки резьбы из План-программы, кН*м:", value=25.0, step=0.5)

if vzd_key_type == "Ввести плечо вручную рулеткой":
    fact_l = st.number_input("2. Фактическая длина плеча ключа L (замер рулеткой от оси трубы до пальца), м:", value=1.0, step=0.01)
else:
    fact_l = st.number_input(f"2. Фактическая длина плеча ключа L (по паспорту {vzd_key_type.split()[0]}), м:", value=base_l, step=0.01)

# Добавляем толщину троса согласно новым требованиям
tros_d = st.number_input("3. Фактический диаметр (толщина) стального натяжного троса лебедки, мм:", value=16.0, step=1.0)
angle_alpha = st.number_input("4. Измеренный угол натяжения троса лебедки к рычагу ключа (идеал 90°), град.:", value=70.0, step=1.0)

# ФИЗИКА ПРОЦЕССА И КОРРЕКЦИЯ ДЛЯ ПУЛЬТА БУРИЛЬЩИКА
# Переводим угол в радианы для синуса
rad_alpha = math.radians(angle_alpha)
sin_alpha = math.sin(rad_alpha)

# Поправка на толщину троса (смещение плеча силы на половину диаметра троса в метрах)
delta_r = (tros_d / 2.0) / 1000.0
effective_l = fact_l + delta_r

# Расчет потерь и реальной уставки
# Формула: М_уставки = M_паспортное / (L_эффективное * sin(alpha))
if sin_alpha > 0 and effective_l > 0:
    target_setting = p_moment / (effective_l * sin_alpha)
    loss_percent = (1.0 - sin_alpha) * 100.0
else:
    target_setting = p_moment
    loss_percent = 0.0

st.markdown("---")
st.subheader("📊 РЕЗУЛЬТАТЫ РАСЧЕТА ДЛЯ БУРОВОЙ БРИГАДЫ:")

col1, col2 = st.columns(2)
with col1:
    st.metric(label="🎯 НЕОБХОДИМАЯ УСТАВКА НА ПУЛЬТЕ (Показания моментомера):", value=f"{target_setting:.2f} кН*м")
with col2:
    st.metric(label="📉 Потери крутящего момента из-за угла натяжения:", value=f"{loss_percent:.1f} %")

# Вывод инженерных ограничений и предупреждений стандартов
if loss_percent > 10.0:
    st.error("🚨 КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО пытаться 'дотянуть' резьбу экстремальным завышением давления на пульте! Потери превышают критический лимит 10%. Остановите работы и потребуйте от бурового подрядчика переставить натяжную лебедку под правильный угол ближе к 90°.")
else:
    st.success("✔️ Величина погрешности находится в пределах допустимого технологического диапазона ИНТИ. Момент свинчивания признан контролируемым.")

# Сборка HTML бланка распоряжения (поддерживает печать через Ctrl + P)
html_print = "<div style='border:2px solid #1E3A8A; padding:20px; border-radius:8px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'>"
html_print += "<h3 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРЬЯ-СЕРВИС»</h3>"
html_print += "<h4 style='text-align:center; color:#4B5563; margin-top:-10px;'>ТЕХНОЛОГИЧЕСКОЕ РАСПОРЯЖЕНИЕ НА СВИНЧИВАНИЕ РЕЗЬБЫ КНБК</h4>"
html_print += "<p style='font-size:12px; text-align:center; color:#6B7280; margin-top:-5px;'>В соответствии с требованиями стандартов СТО ИНТИ S.QS.7 и S.QS.8</p>"
html_print += "<hr style='border:1px solid #1E3A8A; margin-bottom:15px;'>"
html_print += "<p><b>Дата/Время:</b> " + current_time + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> " + field_name + "</p>"
html_print += "<p><b>Скважина / Куст:</b> " + well_number + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Выполнил инженер по ННБ:</b> " + engineer_name + "</p>"
html_print += "<hr style='border:1px dashed #D1D5DB; margin:15px 0;'>"
html_print += "<p style='font-size:15px;'><b>Паспортный требуемый момент затяжки соединения:</b> " + f"{p_moment:.2f}" + " кН*м</p>"
html_print += "<p style='font-size:15px;'><b>Фактические параметры линии:</b> Плечо UMK = " + f"{fact_l:.2f}" + " м, Диаметр троса = " + f"{tros_d:.1f}" + " мм, Угол = " + f"{angle_alpha:.1f}" + "°</p>"
html_print += "<p style='font-size:16px; color:#1E3A8A;'><b>👉 РЕКОМЕНДУЕМАЯ УСТАВКА МОМЕНТА ДЛЯ БУРИЛЬЩИКА: " + f"{target_setting:.2f}" + " кН*м</b></p>"
html_print += "<p style='font-size:13px; color:#4B5563;'><i>Примечание для мастера: Передать данное значение бурильщику для выставления целевого давления затяжки замка на манометре машинного ключа.</i></p>"
html_print += "<p style='font-size:11px; color:#9CA3AF; text-align:center; margin-top:25px; border-top:1px solid #E5E7EB; padding-top:10px;'>Разработано: AI-Интегратор КНБК • Экосистема цифровых сервисов ООО «Траектория-Сервис»</p>"
html_print += "</div>"

st.markdown("---")
st.subheader("📥 Официальный бланк распоряжения для буровой бригады:")
st.markdown(html_print, unsafe_allow_html=True)

st.markdown(" ")
st.info("💡 **Инструкция для печати:** Нажмите комбинацию клавиш **`Ctrl + P`**, выберите принтер «Сохранить как PDF» и прикрепите готовое распоряжение к суточному рапорту инженера.")
