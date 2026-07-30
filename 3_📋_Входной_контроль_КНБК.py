import streamlit as st
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Входной контроль", layout="wide")

st.title("📋 Рапорт входного контроля оборудования")
st.caption("МОДУЛЬ ВЕРИФИКАЦИИ ПАРАМЕТРОВ ЭЛЕМЕНТОВ КНБК, ВЗД И ДОЛОТ ПЕРЕД СПУСКОМ")
st.markdown("---")

well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
report_text = ""

st.info("Отметьте параметры, проверенные на устье. Все несоответствия будут занесены в Акт внизу экрана!")

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

res_k = "USPESHNO" if (k1 and k2 and k3 and k4 and k5 and k6 and k7 and k8 and k9 and k10) else "ZAMECHANIYA"
res_v = "USPESHNO" if (v1 and v2 and v3 and v4 and v5) else "ZAMECHANIYA"
res_d = "USPESHNO" if (d1 and d2 and d3 and d4) else "ZAMECHANIYA"

def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(40, 10, "AKT ПRIEMKI OBORUDOVANIYA KNBK")
    pdf.ln(12)
    
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(40, 10, f"Data / Vremya: {current_time}")
    pdf.ln(8)
    pdf.cell(40, 10, f"Mestorozhdenie: {field_name}")
    pdf.ln(8)
    pdf.cell(40, 10, f"Obyekt: {well_number}")
    pdf.ln(8)
    pdf.cell(40, 10, f"Inzhener NNB: {engineer_name}")
    pdf.ln(14)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(40, 10, "REZULTATY INSPEKCII:")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(40, 10, f"1. Obshchiy kontrol KNBK i UMK: {res_k}")
    pdf.ln(8)
    pdf.cell(40, 10, f"2. Proverka dvigatelya (VZD): {res_v}")
    pdf.ln(8)
    pdf.cell(40, 10, f"3. Vhodnoy kontrol dolota: {res_d}")
    pdf.ln(15)
    
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(40, 10, "TSifrovoy pomoshchnik inzhenera 'Traektoriya-Servis'")
    return pdf.output()

pdf_data = create_pdf()

st.markdown("---")
st.subheader("📥 Экспорт результатов проверки")
st.download_button(
    label="📄 Сформировать и скачать официальный отчет (PDF)",
    data=bytes(pdf_data),
    file_name=f"Akt_vhodnogo_kontrolya_{well_number.replace(' ', '_')}.pdf",
    mime="application/pdf"
)
