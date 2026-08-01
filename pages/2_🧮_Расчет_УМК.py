import streamlit as st
import math
from datetime import datetime

st.set_page_config(page_title="Расчет УМК", layout="wide")

st.title("🧮 Модуль автоматической корректировки момента УМК")
st.caption("РАСЧЕТ КОРРЕКЦИИ КРУТЯЩЕГО МОМЕНТА С УЧЕТОМ ГЕОМЕТРИИ КЛЮЧА И ТОЛЩИНЫ ТРОСА")
st.markdown("---")

# Сдержанная техническая отметка о соответствии стандартам ИНТИ
st.markdown("<div style='color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #9CA3AF; margin-bottom: 20px;'><b>Верификация стандартов:</b> Данный алгоритм инженерных расчетов разработан в строгом соответствии с требованиями отраслевых стандартов <b>СТО ИНТИ S.QS.7 (п. 7.4.2)</b> в части технологического контроля параметров сборки премиальных и замковых резьбовых соединений КНБК, а также <b>СТО ИНТИ S.QS.8 (п. 5.3.1)</b> в части учета геометрических отклонений, плеча рычага ключа и тарировки моментомеров бурового подрядчика на устье скважины.</div>", unsafe_allow_html=True)

# Данные из боковой панели
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

st.subheader("🛠️ Входные параметры для пересчета момента")

# Официальная база данных ключей УМК (заводы-изготовители РФ)
vzd_key_type = st.selectbox(
    "Выберите верифицированную модель ключа УМК (база ГОСТ / ТУ РФ):",
    [
        "УМК-10/1 (Эталонное плечо L = 0.715 м)", 
        "УМК-35 (Эталонное плечо L = 1.000 м)", 
        "УМК-48 (Эталонное плечо L = 1.200 м)", 
        "УМК-75 (Эталонное плечо L = 1.500 м)",
        "УМК-90 (Эталонное плечо L = 1.500 м)",
        "Фактический замер рулеткой на устье (вручную)"
    ]
)

# Жесткое определение плеча на основе официальных паспортов
base_l = 1.000
if "УМК-10/1" in vzd_key_type:
    base_l = 0.715
if "УМК-35" in vzd_key_type:
    base_l = 1.000
if "УМК-48" in vzd_key_type:
    base_l = 1.200
if "УМК-75" in vzd_key_type or "УМК-90" in vzd_key_type:
    base_l = 1.500

# Входные числовые данные
p_moment = st.number_input("1. Требуемый паспортный момент затяжки резьбы из План-программы, кН*м:", value=25.0, step=0.5)

if vzd_key_type == "Фактический замер рулеткой на устье (вручную)":
    fact_l = st.number_input("2. Введите фактическую длину плеча ключа L (от оси трубы до пальца), м:", value=1.000, step=0.001, format="%.3f")
else:
    fact_l = st.number_input(f"2. Длина плеча ключа L по официальному паспорту завода, м:", value=base_l, step=0.001, format="%.3f", disabled=True)

tros_d = st.number_input("3. Фактический диаметр (толщина) стального натяжного троса лебедки, мм:", value=16.0, step=1.0)
angle_alpha = st.number_input("4. Измеренный угол натяжения троса лебедки к рычагу ключа (идеал 90°), град.:", value=70.0, step=1.0)

# ФИЗИКА ПРОЦЕССА И МАТЕМАТИЧЕСКАЯ КОРРЕКЦИЯ
rad_alpha = math.radians(angle_alpha)
sin_alpha = math.sin(rad_alpha)

# Расчет смещения оси за счет толщины натяжного каната (в метрах)
delta_r = (tros_d / 2.0) / 1000.0
effective_l = fact_l + delta_r

# Расчет целевой уставки момента для пульта бурильщика
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

# Технологические ограничения СТО ИНТИ
if loss_percent > 10.0:
    st.error("🚨 КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО пытаться 'дотянуть' резьбу завышением давления на гидравлическом пульте! Потери превышают критический лимит СТО ИНТИ 10%. Остановите работы и потребуйте от бурового подрядчика переставить натяжную лебедку буровой установки под угол 90°.")
else:
    st.success("✔️ Величина погрешности находится в пределах допустимого технологического диапазона ИНТИ. Момент свинчивания признан контролируемым.")

# Сборка HTML бланка распоряжения (поддерживает печать через Ctrl + P)
html_print = "<div style='border:2px solid #1E3A8A; padding:20px; border-radius:8px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'>"
html_print += "<h3 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРИЯ-СЕРВИС»</h3>"
html_print += "<h4 style='text-align:center; color:#4B5563; margin-top:-10px;'>РЕКОМЕНТАЦИ ТЕХНОЛОГА ННБ НА СВИНЧИВАНИЕ РЕЗЬБЫ КНБК</h4>"
html_print += "<p style='font-size:11px; text-align:center; color:#6B7280; margin-top:-5px;'>Расчет выполнен согласно СТО ИНТИ S.QS.7 (п. 7.4.2) и СТО ИНТИ S.QS.8 (п. 5.3.1)</p>"
html_print += "<hr style='border:1px solid #1E3A8A; margin-bottom:15px;'>"
html_print += "<p><b>Дата/Время:</b> " + current_time + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> " + field_name + "</p>"
html_print += "<p><b>Скважина / Куст:</b> " + well_number + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер по бурению (ННБ):</b> " + engineer_name + "</p>"
html_print += "<hr style='border:1px dashed #D1D5DB; margin:15px 0;'>"
html_print += "<p style='font-size:15px;'><b>Используемый инструмент:</b> " + str(vzd_key_type.split(' (')[0]) + " (Эффективное плечо с учетом троса: " + f"{effective_l:.3f}" + " м)</p>"
html_print += "<p style='font-size:15px;'><b>Паспортный требуемый момент затяжки соединения:</b> " + f"{p_moment:.2f}" + " кН*м</p>"
html_print += "<p style='font-size:15px;'><b>Фактические параметры линии:</b> Плечо ключа = " + f"{fact_l:.3f}" + " м, Толщина троса = " + f"{tros_d:.1f}" + " мм, Угол натяжения = " + f"{angle_alpha:.1f}" + "°</p>"
html_print += "<p style='font-size:16px; color:#1E3A8A;'><b>👉 РЕКОМЕНДУЕМАЯ УСТАВКА МОМЕНТА ДЛЯ КЛЮЧА УМК: " + f"{target_setting:.2f}" + " кН*м</b></p>"
html_print += "<p style='font-size:13px; color:#4B5563;'><i>Примечание: Данное значение передается буровому мастеру для контроля уставки гидравлического манометра машинного ключа.</i></p>"
html_print += "<p style='font-size:11px; color:#4B5563; text-align:center; margin-top:25px; border-top:1px solid #E5E7EB; padding-top:10px;'><b>Разработчик:</b> Старший инженер по качеству ОСМК • Экосистема цифровых сервисов ООО «Траектория-Сервис»</p>"
html_print += "</div>"

st.markdown("---")
st.subheader("📥 Официальный бланк распоряжения для буровой бригады:")
st.markdown(html_print, unsafe_allow_html=True)

st.markdown(" ")
st.info("💡 **Инструкция для печати:** Нажмите комбинацию клавиш **`Ctrl + P`**, выберите принтер «Сохранить как PDF» и прикрепите готовое распоряжение к суточному рапорту инженера.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 30px;'><b>Разработчик цифрового модуля:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ • Цифровая экосистема ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
