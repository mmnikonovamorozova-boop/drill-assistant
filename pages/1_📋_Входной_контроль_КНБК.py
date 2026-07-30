import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Входной контроль", layout="wide")

st.title("📋 Рапорт входного контроля оборудования")
st.caption("МОДУЛЬ ВЕРИФИКАЦИИ ПАРАМЕТРОВ ЭЛЕМЕНТОВ КНБК, ВЗД И ДОЛОТ ПЕРЕД СПУСКОМ")
st.markdown("---")

well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

st.info("Отметьте параметры, проверенные на устье. Официальный печатный Акт сформируется внизу экрана!")

st.markdown("### 🔹 БЛОК 1: ОБЩИЙ КОНТРОЛЬ КНБК И ИНСТРУМЕНТА")
k1 = st.checkbox("Соответствует количество поступившего оборудования указанному в ТТН?", value=False, key="nk1")
k2 = st.checkbox("В наличии заводские паспорта и акты дефектоскопии (не старше 12 месяцев)?", value=False, key="nk2")
k3 = st.checkbox("Данные в паспортах полностью соответствуют выбитым номерам на оборудовании?", value=False, key="nk3")
k4 = st.checkbox("В наличии декларация о соответствии и сертификаты качества на материал?", value=False, key="nk4")
k5 = st.checkbox("УСПЕШНО выполнен замер комплекта шаров циркуляционного переводника на проходимость?", value=False, key="nk5")
k6 = st.checkbox("Защитные колпаки присутствуют на всех без исключения резьбовых соединениях?", value=False, key="nk6")
k7 = st.checkbox("В наличии поверенный эксплуатационный паспорт на моментомер ключа УМК?", value=False, key="nk7")
k8 = st.checkbox("Предохранительный хомут (ХП) укомплектован ЗИП, сухари и шплинты без дефектов?", value=False, key="nk8")
k9 = st.checkbox("Проведена калибровка мерительного инструмента (металлическая рулетка, штангенциркуль)?", value=False, key="nk9")
k10 = st.checkbox("На корпус кожуха резистивиметра нанесена маркером надпись «ВВЕРХ» и замерены окна?", value=False, key="nk10")

st.markdown("---")
st.markdown("### 🔹 БЛОК 2: ПРИЕМКА ЗАБОЙНОГО ДВИГАТЕЛЯ (ВЗД)")
v1 = st.checkbox("Данные о наработке в паспорте ВЗД внесены своевременно и в полном объеме?", value=False, key="nv1")
v2 = st.checkbox("Выставленные углы перекоса регулятора ВЗД строго соответствуют заявленным в паспорте?", value=False, key="nv2")
v3 = st.checkbox("Визуально подтверждено полное отсутствие повреждений резьб муфты и ниппеля ВЗД?", value=False, key="nv3")
v4 = st.checkbox("Буровая бригада проверила исправность и ход обратного клапана ВЗД нажатием?", value=False, key="nv4")
v5 = st.checkbox("На корпусе шпинделя и статора отсутствует красная отметка дефектоскопии (брак)?", value=False, key="nv5")

st.markdown("---")
st.markdown("### 🔹 БЛОК 3: ВХОДНОЙ КОНТРОЛЬ ДОЛОТА")
d1 = st.checkbox("В наличии паспорт долота, акт дефектоскопии и свидетельство о поверке колец?", value=False, key="nd1")
d2 = st.checkbox("Корпус долота цел, отсутствуют микротрещины, эрозия и размывы тела?", value=False, key="nd2")
d3 = st.checkbox("Все насадки (гидромониторные) установлены, зафиксированы и соответствуют программе?", value=False, key="nd3")
d4 = st.checkbox("Твердосплавные режущие элементы/матрица без сколов, шарошки вращаются плавно?", value=False, key="nd4")

res_k = "УСПЕШНО ДОПУЩЕНО" if (k1 and k2 and k3 and k4 and k5 and k6 and k7 and k8 and k9 and k10) else "ВЫЯВЛЕНЫ ЗАМЕЧАНИЯ"
res_v = "УСПЕШНО ДОПУЩЕНО" if (v1 and v2 and v3 and v4 and v5) else "ВЫЯВЛЕНЫ ЗАМЕЧАНИЯ"
res_d = "УСПЕШНО ДОПУЩЕНО" if (d1 and d2 and d3 and d4) else "ВЫЯВЛЕНЫ ЗАМЕЧАНИЯ"

color_k = "green" if res_k == "УСПЕШНО ДОПУЩЕНО" else "red"
color_v = "green" if res_v == "УСПЕШНО ДОПУЩЕНО" else "red"
color_d = "green" if res_d == "УСПЕШНО ДОПУЩЕНО" else "red"

# Сборка HTML в одну чистую строчку через сложение
html_form = "<div style='border:3px solid #1E3A8A; padding:25px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'>"
html_form += "<h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРЬЯ-СЕРВИС»</h2>"
html_form += "<h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>ОФИЦИАЛЬНЫЙ АКТ ВХОДНОГО КОНТРОЛЯ КНБК</h3>"
html_form += "<hr style='border:1px solid #1E3A8A; margin-bottom:20px;'>"
html_form += "<p><b>Дата/Время:</b> " + current_time + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> " + field_name + "</p>"
html_form += "<p><b>Объект / Скважина:</b> " + well_number + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> " + engineer_name + "</p>"
html_form += "<h4 style='color:#1E3A8A; margin-top:25px; border-bottom:1px solid #D1D5DB; padding-bottom:5px;'>РЕЗУЛЬТАТЫ ВЕРИФИКАЦИИ УЗЛОВ КНБК:</h4>"
html_form += "<p style='font-size:15px;'><b>1. Общий контроль элементов КНБК и УМК:</b> <span style='color:" + color_k + ";'><b>" + res_k + "</b></span></p>"
html_form += "<p style='font-size:15px;'><b>2. Проверка забойного двигателя (ВЗД):</b> <span style='color:" + color_v + ";'><b>" + res_v + "</b></span></p>"
html_form += "<p style='font-size:15px;'><b>3. Входной контроль бурового долота:</b> <span style='color:" + color_d + ";'><b>" + res_d + "</b></span></p>"
html_form += "<p style='font-size:12px; color:#6B7280; text-align:center; margin-top:35px; border-top:1px dashed #D1D5DB; padding-top:10px;'>Сгенерировано в модуле 'Цифровой аудит КНБК' • Версия 2026 г. • Для печати в PDF нажмите Ctrl + P</p>"
html_form += "</div>"

st.markdown("---")
st.subheader("📥 Официальный бланк Акта приемки:")
st.markdown(html_form, unsafe_allow_html=True)

st.markdown(" ")
st.info("💡 **Как распечатать или сохранить в PDF:** Нажмите комбинацию клавиш **`Ctrl + P`** (или три точки браузера ➡️ Печать), выберите принтер «Сохранить как PDF» и заберите готовый документ!")
