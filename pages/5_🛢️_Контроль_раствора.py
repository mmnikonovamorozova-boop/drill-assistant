import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Контроль раствора", layout="wide")

st.title("🛢️ Контроль параметров бурового раствора")
st.caption("АВТОМАТИЗАЦИЯ РАСЧЕТОВ И ФОРМИРОВАНИЕ АКТа ЗАМЕРОВ ПО ГОСТ 33213-2014")
st.markdown("---")

# Боковая панель для метаданных Акта
st.sidebar.header("📝 Сведения для Акта замера")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")
current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

st.info("Инструкция: Введите фактические показания лабораторных приборов. Программа автоматически выполнит расчеты реологии по формулам API/ГОСТ.")

# Основные параметры отбора пробы
st.markdown("### 📋 1. Условия отбора пробы раствора")
col_env1, col_v_r = st.columns(2)
with col_env1:
    mud_type = st.selectbox("Тип бурового раствора:", ["РВО (На водной основе)", "РУО (На углеводородной основе)"])
    sample_place = st.text_input("Место отбора пробы (например, Желобная система, Емкость №2):", value="Желобная система")
with col_v_r:
    current_depth = st.number_input("Текущая глубина забоя (вертикаль/ствол), м:", value=3700.0, step=10.0)
    current_operation = st.text_input("Выполняемая операция на скважине:", value="Бурение")

st.markdown("---")

# Плотность и Вязкость
st.markdown("### ⚖️ 2. Плотность и Условная вязкость")
col_p1, col_p2 = st.columns(2)
with col_p1:
    density = st.number_input("Плотность раствора (Рычажные весы API), г/см³:", value=1.20, step=0.01, format="%.2f")
with col_p2:
    uv_seconds = st.number_input("Условная вязкость (Воронка Марша, замер 946 мл), сек:", value=43.0, step=1.0)

st.markdown("---")

# Расчет реологии по вискозиметру FANN 35 / OFITE 800
st.markdown("### 🔄 3. Замер реологии на вискозиметре (FANN 35 / OFITE 800)")
st.caption("Показания шкалы прибора для автоматического вычисления ПВ и ДНС:")

col_f1, col_f2 = st.columns(2)
with col_f1:
    f600 = st.number_input("Показание при 600 об/мин:", value=54.0, step=1.0)
with col_f2:
    f300 = st.number_input("Показание при 300 об/мин:", value=35.0, step=1.0)

# Математический расчет реологии по формулам из методички ТС
# ПВ = 600 rpm - 300 rpm
pv_calculated = f600 - f300
# ДНС = 300 rpm - ПВ
dns_calculated = f300 - pv_calculated

col_res1, col_res2 = st.columns(2)
with col_res1:
    st.metric(label="Пластическая вязкость (ПВ), мПа*с:", value=f"{pv_calculated:.0f}")
with col_res2:
    st.metric(label="Динамическое напряжение сдвига (ДНС), фунт/100 фут²:", value=f"{dns_calculated:.0f}")

st.markdown("---")

# Контроль СНС и Фильтрации
st.markdown("### 📈 4. Структурно-механические свойства")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    sns_10s = st.number_input("СНС за 10 сек (Gel 10s), фунт/100 фут²:", value=6.0, step=1.0)
with col_s2:
    sns_10m = st.number_input("СНС за 10 мин (Gel 10m), фунт/100 фут²:", value=10.0, step=1.0)
with col_s3:
    filtr_30 = st.number_input("Фильтрация за 30 мин (Фильтр-пресс), мл:", value=5.0, step=0.1)

# Автоматический анализ критического прогрессирования СНС
if sns_10m - sns_10s >= 5.0:
    st.warning("⚠️ ВНИМАНИЕ: Прогрессирующий показатель СНС! Большой разрыв между 10с и 10м указывает на наработку активной твердой фазы или загрязнение раствора растворимыми солями/цементом.")

st.markdown("---")

# Химические параметры (pH, Мел, Песок)
st.markdown("### 🧪 5. Физико-химические параметры")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    ph_value = st.number_input("Показатель pH пробы (электронный pH-метр):", value=9.5, step=0.1)
with col_c2:
    ca_content = st.number_input("Содержание карбоната кальция (Мел), кг/м³:", value=25.0, step=1.0)
with col_c3:
    sand_content = st.number_input("Содержание песка (Сито 74 мкм), %:", value=0.5, step=0.1)

if sand_content > 1.0:
    st.error("🚨 КРИТИЧЕСКИЙ РИСК: Содержание песка превышает нормальный предел! Высокая абразивность вызовет лавинообразный износ насадок долота и статора ВЗД.")

# Сборка официального печатного Акта по ГОСТ 33213-2014 в HTML
html_mud_report = "<div style='border:3px solid #1E3A8A; padding:25px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'>"
html_mud_report += "<h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРЬЯ-СЕРВИС»</h2>"
html_mud_report += "<h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>АКТ КОНТРОЛЬНОГО ЗАМЕРА ПАРАМЕТРОВ БУРОВОГО РАСТВОРА</h3>"
html_mud_report += "<h5 style='text-align:center; color:#6B7280; margin-top:-5px;'>(Форма Акта согласно Приложению К ГОСТ 33213-2014)</h5>"
html_mud_report += "<hr style='border:1px solid #1E3A8A; margin-bottom:20px;'>"

html_mud_report += "<p><b>Дата и время замера:</b> " + current_time + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> " + field_name + "</p>"
html_mud_report += "<p><b>Объект / Скважина:</b> " + well_number + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер по ННБ:</b> " + engineer_name + "</p>"
html_mud_report += "<p><b>Текущий забой:</b> " + str(current_depth) + " м &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Выполняемая операция:</b> " + current_operation + "</p>"
html_mud_report += "<p><b>Тип раствора:</b> " + mud_type + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Место отбора пробы:</b> " + sample_place + "</p>"

html_mud_report += "<h4 style='color:#1E3A8A; margin-top:20px; border-bottom:1px solid #D1D5DB; padding-bottom:5px;'>ФАКТИЧЕСКИЕ СВОЙСТВА БУРОВОГО РАСТВОРА:</h4>"

html_mud_report += "<table style='width:100%; border-collapse:collapse; font-size:14px;'>"
html_mud_report += "<tr style='background-color:#E5E7EB;'>"<th style='padding:8px; border:1px solid #CBD5E1; text-align:left;'>Контролируемый параметр</th><th style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>Ед. изм.</th><th style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>Значение</th></tr>"
html_mud_report += "<tr><td style='padding:8px; border:1px solid #CBD5E1;'>Плотность бурового раствора</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>г/см³</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'><b>" + f"{density:.2f}" + "</b></td></tr>"
html_mud_report += "<tr><td style='padding:8px; border:1px solid #CBD5E1;'>Условная вязкость (Воронка Марша)</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>сек</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'><b>" + str(uv_seconds) + "</b></td></tr>"
html_mud_report += "<tr><td style='padding:8px; border:1px solid #CBD5E1;'>Пластическая вязкость (ПВ)</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>мПа*с</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'><b>" + f"{pv_calculated:.0f}" + "</b></td></tr>"
html_mud_report += "<tr><td style='padding:8px; border:1px solid #CBD5E1;'>Динамическое напряжение сдвига (ДНС)</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>фунт/100фут²</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'><b>" + f"{dns_calculated:.0f}" + "</b></td></tr>"
html_mud_report += "<tr><td style='padding:8px; border:1px solid #CBD5E1;'>Статическое напряжение сдвига (СНС 10с / 10мин)</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>фунт/100фут²</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'><b>" + str(sns_10s) + " / " + str(sns_10m) + "</b></td></tr>"
html_mud_report += "<tr><td style='padding:8px; border:1px solid #CBD5E1;'>Показатель фильтрации за 30 минут</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>мл</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'><b>" + f"{filtr_30:.1f}" + "</b></td></tr>"
html_mud_report += "<tr><td style='padding:8px; border:1px solid #CBD5E1;'>Водородный показатель (pH)</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>-</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'><b>" + f"{ph_value:.1f}" + "</b></td></tr>"
html_mud_report += "<tr><td style='padding:8px; border:1px solid #CBD5E1;'>Содержание карбоната кальция (Мел)</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>кг/м³</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'><b>" + str(ca_content) + "</b></td></tr>"
html_mud_report += "<tr><td style='padding:8px; border:1px solid #CBD5E1;'>Содержание абразивного песка</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'>%</td><td style='padding:8px; border:1px solid #CBD5E1; text-align:center;'><b>" + f"{sand_content:.1f}" + "</b></td></tr>"
html_mud_report += "</table>"

html_mud_report += "<table style='width:100%; margin-top:30px; font-size:14px;'>"
html_mud_report += "<tr><td>________________________<br>Представитель Заказчика</td><td>________________________<br>Инженер по растворам</td><td>________________________<br>Инженер по ННБ (ООО ТС)</td></tr>"
html_mud_report += "</table>"
html_mud_report += "<p style='font-size:11px; color:#6B7280; text-align:center; margin-top:25px; border-top:1px dashed #D1D5DB; padding-top:10px;'>Сгенерировано в цифровом модуле растворного сервиса • Для печати Акта нажмите Ctrl + P</p>"
html_mud_report += "</div>"

st.markdown("---")
st.subheader("📥 Официальный бланк Акта контроля замеров:")
st.markdown(html_mud_report, unsafe_allow_html=True)
