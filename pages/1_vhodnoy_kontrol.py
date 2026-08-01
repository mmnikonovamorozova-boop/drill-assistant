import streamlit as st
import pandas as pd
from datetime import datetime

import streamlit as st

# ПРОВЕРКА: Если инженер не залогинился на главной странице — выкидываем его назад
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пожалуйста, перейдите на Главную страницу приложения и введите пароль.")
    st.stop() # Полностью останавливаем выполнение кода этой страницы КНБК

st.set_page_config(page_title="1. Входной контроль", page_icon="📋", layout="wide")

st.title("📋 Рапорт входного контроля оборудования")
st.markdown("<style>a[href*='vhodnoy_kontrol'] span, a[href*='raschet_umk'] span, a[href*='tech_cards'] span, a[href*='lyuft_vzd'] span, a[href*='kontrol_rastvora'] span, a[href*='baza_znaniy'] span, a[href='/'] span { font-size: 0 !important; } a[href='/'] span::before { content: '🧭 Главная страница'; font-size: 14px !important; font-weight: bold; } a[href*='vhodnoy_kontrol'] span::before { content: '📋 1. Входной контроль'; font-size: 14px !important; } a[href*='raschet_umk'] span::before { content: '🧮 2. Расчет УМК'; font-size: 14px !important; } a[href*='tech_cards'] span::before { content: '🔨 3. Технологические карты'; font-size: 14px !important; } a[href*='lyuft_vzd'] span::before { content: '📏 4. Люфт ВЗД'; font-size: 14px !important; } a[href*='kontrol_rastvora'] span::before { content: '🧪 5. Контроль раствора'; font-size: 14px !important; } a[href*='baza_znaniy'] span::before { content: '📚 6. База знаний'; font-size: 14px !important; }</style>", unsafe_allow_html=True)
st.caption("МОДУЛЬ ВЕРИФИКАЦИИ ПАРАМЕТРОВ ЭЛЕМЕНТОВ КНБК, ВЗД И ДОЛОТ ПЕРЕД СПУСКОМ")
st.markdown("---")

# Сдержанная техническая отметка о соответствии стандартам ИНТИ
st.markdown("<div style='color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #9CA3AF; margin-bottom: 20px;'><b>Верификация стандартов:</b> Данный модуль входного контроля и верификации разработан в строгом соответствии с требованиями отраслевых стандартов <b>СТО ИНТИ S.QS.7 (п. 7.4.1)</b> в части проведения поштучной приемки, визуально-инструментального контроля и проверки сопроводительных документов элементов КНБК, а также <b>СТО ИНТИ S.QS.8 (п. 5.1.2)</b> в части контроля исправности и метрологического подтверждения мерительного инструмента на буровой площадке.</div>", unsafe_allow_html=True)

well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

# =========================================================================
# БЛОК МГНОВЕННОГО ЛОКАЛЬНОГО ЧТЕНИЯ ИЗ РЕПОЗИТОРИЯ GITHUB
# =========================================================================
@st.cache_data(ttl=600)
def load_local_nomenclature():
    try:
        df = pd.read_excel("Inventory.xlsx")
        return df
    except Exception as e:
        return None

# Загрузка номенклатуры
nomenclature_df = load_local_nomenclature()

st.subheader("🔍 Локальная номенклатура КНБК (Синхронизация через GitHub)")

col_id1, col_id2 = st.columns(2)

if nomenclature_df is not None and len(nomenclature_df.columns) > 0:
    st.success("✔️ Перечень элементов КНБК успешно подгружен из локального репозитория проекта.")
    with col_id1:
        unique_elements = nomenclature_df.iloc[:, 0].dropna().unique().tolist()
        element_name = st.selectbox("Выберите наименование элемента КНБК:", unique_elements)
else:
    st.error("🚨 Файл 'Inventory.xlsx' не найден в корне вашего GitHub! Пожалуйста, загрузите его.")
    with col_id1:
        element_name = st.selectbox(
            "Выберите наименование элемента КНБК (Аварийный список):",
            ["Винтовой забойный двигатель (ВЗД)", "Гидравлический буровой ЯС", "Телеметрическая система (ТМС)", "Циркуляционный переводник (КЦ)", "Утяжеленная бурильная труба (УБТ)", "Калибратор / Центратор", "Буровое долото"]
        )

with col_id2:
    element_serial = st.text_input("Внесите фактический серийный номер элемента (с корпуса):", value="", placeholder="Например: № 6542")

st.markdown("---")
st.info("Отметьте параметры, проверенные на устье. Официальный печатный Акт сформируется внизу экрана!")

# =========================================================================
# ДИНАМИЧЕСКИЙ ВЫВОД БЛОКОВ КОНТРОЛЯ В ЗАВИСИМОСТИ ОТ ЭЛЕМЕНТА
# =========================================================================

# БЛОК 1: ОТОБРАЖАЕТСЯ ВСЕГДА
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

# Переменные по умолчанию для скрытых блоков
res_v = "НЕ ПРИМЕНИМО"
res_d = "НЕ ПРИМЕНИМО"
v1 = v2 = v3 = v4 = v5 = True
d1 = d2 = d3 = d4 = True

# БЛОК 2: ТОЛЬКО ДЛЯ ВЗД
if "ВЗД" in str(element_name).upper():
    st.markdown("---")
    st.markdown("### 🔹 БЛОК 2: ПРИЕМКА ЗАБОЙНОГО ДВИГАТЕЛЯ (ВЗД)")
    v1 = st.checkbox("Данные о наработке в паспорте ВЗД внесены своевременно и в полном объеме?", value=False, key="nv1")
    v2 = st.checkbox("Выставленные углы перекоса регулятора ВЗД строго соответствуют заявленным в паспорте?", value=False, key="nv2")
    v3 = st.checkbox("Визуально подтверждено полное отсутствие повреждений резьб муфты и ниппеля ВЗД?", value=False, key="nv3")
    v4 = st.checkbox("Буровая бригада проверила исправность и ход обратного клапана ВЗД нажатием?", value=False, key="nv4")
    v5 = st.checkbox("На корпусе шпинделя и статора отсутствует красная отметка дефектоскопии (брак)?", value=False, key="nv5")
    res_v = "УСПЕШНО ДОПУЩЕНО" if (v1 and v2 and v3 and v4 and v5) else "ВЫЯВЛЕНЫ ЗАМЕЧАНИЯ"

# БЛОК 3: ТОЛЬКО ДЛЯ ДОЛОТА
if "ДОЛОТО" in str(element_name).upper():
    st.markdown("---")
    st.markdown("### 🔹 БЛОК 3: ВХОДНОЙ КОНТРОЛЬ ДОЛОТА")
    d1 = st.checkbox("В наличии паспорт долота, акт дефектоскопии и свидетельство о поверке колец?", value=False, key="nd1")
    d2 = st.checkbox("Корпус долота цел, отсутствуют микротрещины, эрозия и размывы тела?", value=False, key="nd2")
    d3 = st.checkbox("Все насадки (гидромониторные) установлены, зафиксированы и соответствуют программе?", value=False, key="nd3")
    d4 = st.checkbox("Твердосплавные режущие элементы/матрица без сколов, шарошки вращаются плавно?", value=False, key="nd4")
    res_d = "УСПЕШНО ДОПУЩЕНО" if (d1 and d2 and d3 and d4) else "ВЫЯВЛЕНЫ ЗАМЕЧАНИЯ"

# Вычисление общего результата для Блока 1
res_k = "УСПЕШНО ДОПУЩЕНО" if (k1 and k2 and k3 and k4 and k5 and k6 and k7 and k8 and k9 and k10) else "ВЫЯВЛЕНЫ ЗАМЕЧАНИЯ"

color_k = "green" if res_k == "УСПЕШНО ДОПУЩЕНО" else "red"
color_v = "gray" if res_v == "НЕ ПРИМЕНИМО" else ("green" if res_v == "УСПЕШНО ДОПУЩЕНО" else "red")
color_d = "gray" if res_d == "НЕ ПРИМЕНИМО" else ("green" if res_d == "УСПЕШНО ДОПУЩЕНО" else "red")

# Сборка динамического HTML бланка
html_form = "<div style='border:3px solid #1E3A8A; padding:25px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;'>"
html_form += "<h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>"
html_form += "<h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>ОФИЦИАЛЬНЫЙ АКТ ВХОДНОГО КОНТРОЛЯ ОБОРУДОВАНИЯ</h3>"
html_form += "<p style='text-align:center; font-size:11px; color:#6B7280; margin-top:-5px;'>Проверка проведена в соответствии с СТО ИНТИ S.QS.7 (п. 7.4.1) и СТО ИНТИ S.QS.8 (п. 5.1.2)</p>"
html_form += "<hr style='border:1px solid #1E3A8A; margin-bottom:20px;'>"
html_form += "<p><b>Дата/Время:</b> " + current_time + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> " + field_name + "</p>"
html_form += "<p><b>Объект / Скважина:</b> " + well_number + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> " + engineer_name + "</p>"
html_form += "<hr style='border:1px dashed #D1D5DB; margin:15px 0;'>"
html_form += "<p style='font-size:15px; color:#1E3A8A;'><b>🔎 СВЕДЕНИЯ ОБ ИСПЫТУЕМОМ ЭЛЕМЕНТЕ:</b></p>"
html_form += "<p style='font-size:15px;'><b>Наименование оборудования (из базы проекта):</b> " + str(element_name) + "</p>"
html_form += "<p style='font-size:15px;'><b>Заводской серийный номер (ввод вручную):</b> " + (str(element_serial) if element_serial else "<span style='color:red;'>НЕ ВВЕДЕН</span>") + "</p>"
html_form += "<hr style='border:1px dashed #D1D5DB; margin:15px 0;'>"
html_form += "<h4 style='color:#1E3A8A; margin-top:10px; padding-bottom:5px;'>РЕЗУЛЬТАТЫ ВЕРИФИКАЦИИ УЗЛОВ КНБК:</h4>"
html_form += "<p style='font-size:14px;'><b>1. Общий контроль элементов КНБК и УМК:</b> <span style='color:" + color_k + ";'><b>" + res_k + "</b></span></p>"

# Вшиваем результаты блоков в Акт только если они активировались
if "ВЗД" in str(element_name).upper():
    html_form += "<p style='font-size:14px;'><b>2. Специальная проверка забойного двигателя (ВЗД):</b> <span style='color:" + color_v + ";'><b>" + res_v + "</b></span></p>"
if "ДОЛОТО" in str(element_name).upper():
    html_form += "<p style='font-size:14px;'><b>3. Специальный входной контроль бурового долота:</b> <span style='color:" + color_d + ";'><b>" + res_d + "</b></span></p>"

html_form += "<p style='font-size:11px; color:#4B5563; text-align:center; margin-top:35px; border-top:1px solid #E5E7EB; padding-top:10px;'><b>Разработчик:</b> Старший инженер-технолог по ННБ • Экосистема цифровых сервисов ООО «Траектория-Сервис»</p>"
html_form += "</div>"

st.markdown("---")
st.subheader("📥 Официальный бланк Акта приемки:")
st.markdown(html_form, unsafe_allow_html=True)

st.markdown(" ")
st.info("💡 **Как распечатать или сохранить в PDF:** Нажмите комбинацию клавиш **`Ctrl + P`** (или три точки браузера ➡️ Печать), выберите принтер «Сохранить как PDF» и заберите готовый документ!")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 30px;'><b>Разработчик цифрового модуля:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ • Цифровая экосистема ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
