import streamlit as st
import pandas as pd
from datetime import datetime

import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 1. Проверяем, авторизован ли пользователь. Если нет — останавливаем выполнение модуля
if not st.session_state.get("authenticated", False):
    st.warning("🔒 Пожалуйста, авторизуйтесь на главной странице приложения.")
    st.stop()

# 2. Извлекаем метаданные рейса из сквозного шлюза сессии
engineer = st.session_state.get("engineer_name", "Не указано")
well = st.session_state.get("well_number", "Не указано")
field = st.session_state.get("field_name", "Не указано")
bha = st.session_state.get("bha_number", "1")

# 3. (Опционально) Отображаем аккуратную плашку с метаданными вверху страницы модуля
st.info(f"📋 **Рейс:** {field} | Скв/Куст: {well} | КНБК №{bha} | **Инженер:** {engineer}")
st.divider()
st.set_page_config(page_title="1. Входной контроль", page_icon="📋", layout="wide")

st.title("📋 Рапорт входного контроля оборудования")
st.caption("МОДУЛЬ ВЕРИФИКАЦИИ ПАРАМЕТРОВ ЭЛЕМЕНТОВ КНБК, ВЗД И ДОЛОТ ПЕРЕД СПУСКОМ")
st.markdown("---")

with st.expander("🔰 Паспорт верификации стандартов СТО ИНТИ", expanded=False):
    st.markdown("### Требования отраслевых стандартов СТО ИНТИ S.QS.7 (п. 7.4.1) и СТО ИНТИ S.QS.8 (п. 5.1.2):")
    st.markdown("""
    * **Метрологический контроль:** Обязательная проверка калибровки и свидетельств о поверке всего мерительного инструмента на буровой площадке.
    * **Поштучная приемка:** Визуально-инструментальный контроль каждого поступающего элемента КНБК, ВЗД и долот перед спуском в скважину.
    * **Сопроводительная документация:** Проверка оригиналов заводских паспортов, актов неразрушающего контроля (дефектоскопии) со сроком действия не старше 12 месяцев.
    * **Технологическая безопасность:** Контроль наличия защитных элементов резьбовых соединений и проверка шаблонирования/проходимости узлов.
    """)

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

st.subheader("🔍 Локальная номенклатура КНБК")

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
html_form += "<p><b>Дата/Время:</b> " + current_time + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> " + field + "</p>"
html_form += "<p><b>Объект / Скважина:</b> " + well + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> " + engineer + "</p>"
html_form += "<hr style='border:1px dashed #D1D5DB; margin:15px 0;'>"
html_form += "<p style='font-size:15px; color:#1E3A8A;'><b>🔎 СВЕДЕНИЯ ОБ ИСПЫТУЕМОМ ЭЛЕМЕНТЕ:</b></p>"
html_form += "<p style='font-size:15px;'><b>Наименование оборудования (из базы проекта):</b> " + str(element_name) + "</p>"
html_form += "<p style='font-size:15px;'><b>Заводской серийный номер (ввод вручную):</b> " + (str(element_serial) if element_serial else "<span style='color:red;'>НЕ ВВЕДЕН</span>") + "</p>"
html_form += "<hr style='border:1px dashed #D1D5DB; margin:15px 0;'>"
html_form += "<h4 style='color:#1E3A8A; margin-top:10px; padding-bottom:5px;'>РЕЗУЛЬТАТЫ ВЕРИФИКАЦИИ УЗЛОВ КНБК:</h4>"
html_form += f"<p style='font-size:14px;'><b>1. Общий контроль элементов КНБК и УМК:</b> <span style='color:{color_k};'><b>{res_k}</b></span></p>"

# Если есть замечания по Блоку 1, выводим список того, что НЕ выполнено
if not (k1 and k2 and k3 and k4 and k5 and k6 and k7 and k8 and k9 and k10):
    html_form += "<div style='background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 10px; margin-left: 20px; border-radius: 4px;'>"
    html_form += "<p style='margin: 0 0 5px 0; color: #991B1B; font-weight: bold; font-size: 13px;'>❌ Выявленные несоответствия общего контроля:</p><ul style='margin: 0; padding-left: 20px; color: #B91C1C; font-size: 13px;'>"
    if not k1: html_form += "<li>Не соответствует количество поступившего оборудования указанному в ТТН</li>"
    if not k2: html_form += "<li>Отсутствуют заводские паспорта или акты дефектоскопии (старше 12 месяцев)</li>"
    if not k3: html_form += "<li>Данные в паспортах не соответствуют выбитым номерам на оборудовании</li>"
    if not k4: html_form += "<li>Отсутствует декларация о соответствии или сертификаты качества</li>"
    if not k5: html_form += "<li>Не выполнен замер комплекта шаров циркуляционного переводника на проходимость</li>"
    if not k6: html_form += "<li>Защитные колпаки присутствуют не на всех резьбовых соединениях</li>"
    if not k7: html_form += "<li>Отсутствует поверенный паспорт на моментомер ключа УМК</li>"
    if not k8: html_form += "<li>Предохранительный хомут (ХП) не укомплектован ЗИП, есть дефекты сухарей/шплинтов</li>"
    if not k9: html_form += "<li>Не проведена калибровка мерительного инструмента</li>"
    if not k10: html_form += "<li>На корпус кожуха резистивиметра не нанесена надпись «ВВЕРХ» или не замерены окна</li>"
    html_form += "</ul></div>"

# Выводим результаты блоков в Акт только если они активировались

if "ВЗД" in str(element_name).upper():
    html_form += f"<p style='font-size:14px; margin-top:15px;'><b>2. Специальная проверка забойного двигателя (ВЗД):</b> <span style='color:{color_v};'><b>{res_v}</b></span></p>"
    
    # Если по ВЗД есть замечания, выводим конкретные дефекты
    if not (v1 and v2 and v3 and v4 and v5):
        html_form += "<div style='background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 10px; margin-left: 20px; border-radius: 4px;'>"
        html_form += "<p style='margin: 0 0 5px 0; color: #991B1B; font-weight: bold; font-size: 13px;'>❌ Выявленные несоответствия по ВЗД:</p><ul style='margin: 0; padding-left: 20px; color: #B91C1C; font-size: 13px;'>"
        if not v1: html_form += "<li>Данные о наработке в паспорте ВЗД внесены не полностью или несвоевременно</li>"
        if not v2: html_form += "<li>Выставленные углы перекоса регулятора ВЗД НЕ соответствуют заявленным в паспорте</li>"
        if not v3: html_form += "<li>Визуально обнаружены повреждения резьб муфты или ниппеля ВЗД</li>"
        if not v4: html_form += "<li>Буровая бригада выявила неисправность или заклинивание обратного клапана ВЗД</li>"
        if not v5: html_form += "<li>На корпусе шпинделя или статора присутствует красная отметка дефектоскопии (брак)</li>"
        html_form += "</ul></div>"

if "ДОЛОТО" in str(element_name).upper():
    html_form += f"<p style='font-size:14px; margin-top:15px;'><b>3. Специальный входной контроль бурового долота:</b> <span style='color:{color_d};'><b>{res_d}</b></span></p>"
    
    # Если по долоту есть замечания, выводим конкретные дефекты
    if not (d1 and d2 and d3 and d4):
        html_form += "<div style='background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 10px; margin-left: 20px; border-radius: 4px;'>"
        html_form += "<p style='margin: 0 0 5px 0; color: #991B1B; font-weight: bold; font-size: 13px;'>❌ Выявленные несоответствия по буровому долоту:</p><ul style='margin: 0; padding-left: 20px; color: #B91C1C; font-size: 13px;'>"
        if not d1: html_form += "<li>Отсутствует паспорт долота, акт дефектоскопии или свидетельство о поверке колец</li>"
        if not d2: html_form += "<li>Корпус долота поврежден (микротрещины, эрозия, размывы тела)</li>"
        if not d3: html_form += "<li>Гидромониторные насадки не установлены, не зафиксированы или не соответствуют программе</li>"
        if not d4: html_form += "<li>Твердосплавные элементы/матрица имеют сколы, или шарошки вращаются неравномерно</li>"
        html_form += "</ul></div>"

st.markdown("---")
st.subheader("📥 Официальный бланк Акта приемки:")
st.markdown(html_form, unsafe_allow_html=True)

st.markdown(" ")
st.download_button(
    label="💾 Скачать Акт в формате HTML",
    data=html_form,
    file_name=f"Akt_VH_{well}.html",
    mime="text/html",
    use_container_width=True
)
# Поле для ввода адреса, куда слать отчет
email_recipient = st.text_input("Email получателя отчета:", placeholder="boss@yourcompany.ru")

# Готовим тему и краткий текст для письма (кодируем пробелы для ссылок)
subject_text = f"Акт входного контроля КНБК — {field}, Скв. {well}".replace(" ", "%20")
body_text = f"Приветствую! Акт входного контроля для скважины {well} ({field}) успешно сформирован инженером {engineer}. Пожалуйста, скачайте прикрепленный к этому письму HTML-файл акта (скачайте его по кнопке выше в приложении).".replace(" ", "%20")

# Создаем безопасную ссылку для открытия локальной почты
mailto_link = f"mailto:{email_recipient}?subject={subject_text}&body={body_text}"

# Создаем стандартную кнопку, текст на которой всегда будет идеально контрастным
if st.button("✉ Подготовить письмо в почтовой программе", use_container_width=True):
    # Готовим тему и текст
    subject_text = f"Акт входного контроля КНБК — {field}, Скв. {well}".replace(" ", "%20")
    body_text = f"Приветствую! Акт входного контроля для скважины {well} ({field}) успешно сформирован инженером {engineer}. Пожалуйста, скачайте прикрепленный к этому письму HTML-файл акта (скачайте его по кнопке выше в приложении).".replace(" ", "%20")
    
    # Собираем mailto ссылку
    mailto_link = f"mailto:{email_recipient}?subject={subject_text}&body={body_text}"
    
    # Запускаем JavaScript код, который откроет почту в новой вкладке
    js_code = f'<script>window.open("{mailto_link}", "_blank");</script>'
    st.components.v1.html(js_code, height=0)

st.info("💡 Сгенерированный Акт можно скачать локально на устройство или отправить на корпоративную почту.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 30px;'><b>Разработчик цифрового модуля:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ • Цифровая экосистема ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
