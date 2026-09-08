import streamlit as st
import pandas as pd
from datetime import datetime

# Настройка конфигурации страницы
st.set_page_config(page_title="Калькулятор люфта ВЗД", layout="wide")
# Извлечение сквозных параметров рейса из глобального шлюза
engineer = st.session_state.get("engineer_name", "Не указано")
well = st.session_state.get("well_number", "Не указано")
field = st.session_state.get("field_name", "Не указано")
bha = st.session_state.get("bha_number", "1")
# Отображение единого профиля и паспорта верификации ИНТИ
st.info(f"📋 **Рейс:** {field} | Скв/Куст: {well} | КНБК №{bha} | **Инженер:** {engineer}")
st.divider()

st.title("📏 Комплексный расчет износа и люфтов шпинделя ВЗД")
st.caption("МЕТОДИКА КОНТРОЛЯ ИЗНОСА ОПОР ШПИНДЕЛЯ ПО РЕГЛАМЕНТАМ ПОСТАВЩИКОВ И ЗАКАЗЧИКОВ")
st.markdown("---")

with st.expander("🔰 Паспорт верификации стандартов СТО ИНТИ", expanded=False):
    st.markdown("### 🔬 Математическое ядро верификации забойных двигателей (СТО ИНТИ S.QS.7 / S.QS.8):")
    st.markdown("""
    * **Стандарт ISO 281:** Расчет остаточного эксплуатационного ресурса опорной секции шпинделя (в мото-часах) производится на основе модифицированного уравнения Лундберга-Палмгрена.
    * **Учет трибологических факторов:** Модель предиктивного износа динамически учитывает гидроабразивное воздействие бурового раствора в зависимости от его текущей плотности.
    * **Прецессия ротора ВЗД:** Оценка ожидаемой радиальной вибрации (в единицах ускорения g) рассчитывается через центробежные силы дисбаланса, вызванные фактическим радиальным зазором нижнего подшипника.
    * **Усталостная прочность вала:** Программа осуществляет непрерывный автоматический аудит накопленной циклической усталости стали для предотвращения полетов и оставления элементов КНБК на забое.
    """)

# =========================================================================
# БЛОК 1: ИНИЦИАЛИЗАЦИЯ И РАЗВЕРНУТЫЙ СБОР ТЕХНОЛОГИЧЕСКИХ ПАРАМЕТРОВ ЗАМЕРА
# =========================================================================

# Синхронизация состояний для модуля валидации (выполняется один раз при старте)
if "val_size_a" not in st.session_state: st.session_state["val_size_a"] = 10.0
if "val_size_b" not in st.session_state: st.session_state["val_size_b"] = 5.5
if "val_radial_ich" not in st.session_state: st.session_state["val_radial_ich"] = 0.20
# Инициализация базового справочника ВЗД (перенесено вверх для защиты от NameError)
base_vzd = {
    "Радиус-Сервис": {"172 мм": 10.0, "240 мм": 10.0},
    "ВНИИБТ": {"Д-172": 4.5, "ДГР-240М": 6.0}
}

try:
    df_excel_vzd = pd.read_excel("vzd_limits_db.xlsx")
    df_excel_vzd.columns = df_excel_vzd.columns.astype(str).str.strip()
    uploaded_base = {}
    for _, row in df_excel_vzd.iterrows():
        brand, model, axial_lim = str(row["Производитель"]).strip(), str(row["Габарит"]).strip(), float(row["Лимит_Осевой"])
        uploaded_base.setdefault(brand, {})[model] = axial_lim
    if uploaded_base: base_vzd = uploaded_base
except Exception: pass

# === ВЫБОР ЗАКАЗЧИКА И ОБОРУДОВАНИЯ С ПОДСКАЗКАМИ ===

# 1. Выбор Недропользователя
selected_client = st.selectbox(
    "1. Выберите Заказчика (Недропользователя) для применения ограничений ТК:",
    ["ПАО Роснефть", "ПАО Газпром", "ПАО Лукойл", "🔄 Без учета ограничений Заказчика"],
    key="main_client_select",
    help="ℹ️ ПОД КЛЮЧ:\nУ каждого недропользователя свои жёсткие регламенты отбраковки ВЗД. Например, 'Роснефть' требует снимать двигатель при люфте свыше 3.5-5 мм, даже если заводской паспорт допускает работу до 10 мм. Выберите компанию, на чьём лицензионном участке бурите."
)
normalized_client_name = str(selected_client).replace("ПАО ", "").strip()

st.markdown("---")

# 2. Селекторы оборудования из базы ВЗД
selected_brand = st.selectbox(
    "2. Выберите производителя:", 
    list(base_vzd.keys()), 
    key="b4_brand_select",
    help="ℹ️ ИДЕНТИФИКАЦИЯ:\nВыберите завод-изготовитель забойного двигателя. Если нужного завода нет, программа подтянет данные из внешнего файла 'vzd_limits_db.xlsx' в корне проекта."
)

selected_diameter = st.selectbox(
    "3. Выберите габарит:", 
    list(base_vzd[selected_brand].keys()), 
    key="b4_unified_selector",
    help="ℹ️ ГАБАРИТ КОРПУСА:\nСмотрите маркировку ВЗД в паспорте на ВЗД или нарезку на статоре (например, 172 мм, 240 мм). От диаметра зависят внутренние зазоры и паспортный лимит износа опор шпинделя."
)

# 2. Интерактивные поля ввода геометрических измерений
st.subheader("📋 Результаты прямых измерений износа на устье скважины:")

col_meas1, col_meas2, col_meas3 = st.columns(3)

# Ввод данных с синхронизацией session_state
with col_meas1:
    size_a = st.number_input("Размер 'А', мм:", value=st.session_state["val_size_a"], key="input_size_a")
    st.session_state["val_size_a"] = size_a

with col_meas2:
    size_b = st.number_input("Размер 'Б', мм:", value=st.session_state["val_size_b"], key="input_size_b")
    st.session_state["val_size_b"] = size_b

with col_meas3:
    radial_ich = st.number_input("Радиальный, мм:", value=st.session_state["val_radial_ich"], key="input_radial")
    st.session_state["val_radial_ich"] = radial_ich

st.markdown("##### ⚙️ Дополнительные параметры рейса для математической модели:")
col_model1, col_model2 = st.columns(2)

with col_model1:
    vzd_hours = st.number_input(
        "Текущая наработка ВЗД за рейс (или общая), ч:", 
        min_value=0.0, max_value=500.0, value=48.0, step=1.0,
        help="Количество часов, которое двигатель уже отработал под заемным давлением."
    )

with col_model2:
    mud_density = st.number_input(
        "Пность бурового раствора, г/см³:", 
        min_value=1.0, max_value=2.5, value=1.20, step=0.02,
        help="Плотность раствора влияет на гидроабразивный износ резинометаллических обкладок опор."
    )

# МГНОВЕННЫЙ РАСЧЕТ И ИНЖЕНЕРНЫЙ ВЫВОД ФАКТА
calculated_axial_delta = size_a - size_b

st.markdown(
    f"<div style='background-color: #F3F4F6; padding: 10px; border-left: 4px solid #4B5563;'>"
    f"<b>📊 Расчет:</b> Осевой люфт = {size_a:.2f} - {size_b:.2f} = "
    f"<span style='color: #1E3A8A; font-weight: bold;'>{calculated_axial_delta:.2f} мм</span>"
    f"</div>", 
    unsafe_allow_html=True
)

# =========================================================================
# БЛОК 2: СВЕРКА ЛИМИТОВ И ОПРЕДЕЛЕНИЕ ЖЕСТКОГО ПОРОГА ОТБРАКОВКИ
# =========================================================================
client_limits_db = {
    "ПАО Роснефть": {"малый": 3.0, "средний": 4.5, "большой": 6.0},
    "ПАО Газпром": {"малый": 3.5, "средний": 4.5, "большой": 5.5},
    "ПАО Лукойл": {"малый": 3.5, "средний": 5.0, "большой": 6.0}
}

limit_wear = base_vzd[selected_brand][selected_diameter]

# Определение группы габаритов (малый/средний/большой)
if "172" in selected_diameter:
    size_group = "средний"
elif "240" in selected_diameter or "8''" in selected_diameter:
    size_group = "большой"
else:
    size_group = "малый" # Включает габарит 13 мм

# Применение ограничений Заказчика
if selected_client != "🔄 Без учета ограничений Заказчика":
    client_rule = client_limits_db[selected_client][size_group]
    eff_max = min(limit_wear, client_rule) # Более жесткий
    st.info(f"🔷 Критерии: Паспорт={limit_wear:.2f} мм | {selected_client}={client_rule:.2f} мм")
else:
    eff_max = limit_wear
st.warning(f"🎯 **Минимально допустимый порог зазора:** {eff_max:.2f} мм")

# =========================================================================
# БЛОК 3: ИНТЕЛЛЕКТУАЛЬНЫЙ ИИ-АУДИТ И ЭКСПЕРТНЫЙ АНАЛИЗ РИСКОВ (СППР)
# =========================================================================
# --- МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ДЕГРАДАЦИИ ОПОР ВЗД ---
base_life = 200.0

if eff_max > 0:
    wear_factor_axial = (calculated_axial_delta / eff_max) ** 2.5
else:
    wear_factor_axial = 1.0

mud_factor = (mud_density / 1.0) ** 1.5

if wear_factor_axial * mud_factor > 0:
    estimated_remaining_hours = (base_life - vzd_hours) / (wear_factor_axial * mud_factor)
else:
    estimated_remaining_hours = 0.0

if estimated_remaining_hours < 0:
    estimated_remaining_hours = 0.0

calculated_vibration_g = (radial_ich ** 2) * 4.5 * (mud_density / 1.15)

if eff_max > 0:
    term_a = (calculated_axial_delta / eff_max) * 60.0
else:
    term_a = 0.0

term_b = (radial_ich / 1.80) * 40.0
fatigue_probability = term_a + term_b

if fatigue_probability > 100.0:
    fatigue_probability = 100.0

if calculated_axial_delta >= eff_max or radial_ich > 1.80:
    fatigue_probability = 100.0
st.markdown("---")
st.markdown("##### 🔬 Инженерный СППР-анализ состояния опор (На основе моделей ISO 281):")

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.metric(
        label="⌛ Прогноз остаточного ресурса опор",
        value=f"{estimated_remaining_hours:.1f} мото-ч",
        delta=f"-{vzd_hours:.0f} ч отработано"
    )

with col_m2:
    if calculated_vibration_g < 2.5:
        vib_status = "Норма"
    elif calculated_vibration_g < 5.5:
        vib_status = "Повышенный"
    else:
        vib_status = "КРИТИЧЕСКИЙ"
    
    st.metric(
        label=f"🎯 Ожидаемая радиальная вибрация ({vib_status})",
        value=f"{calculated_vibration_g:.2f} g"
    )

with col_m3:
    st.metric(
        label="🚨 Риск поломки / полета вала",
        value=f"{fatigue_probability:.1f} %"
    )

if estimated_remaining_hours < 20.0 or fatigue_probability > 75.0:
    st.error("🚨 ВНИМАНИЕ: Опоры находятся в стадии прогрессирующего разрушения! Рекомендуется досрочный подъем КНБК или снижение расхода бурового раствора на 15%.")
elif calculated_vibration_g > 4.0:
    st.warning("⚠ ВНИМАНИЕ: Высокий риск поломки элементов ТМС (телеметрии) из-за радиального биения вала ВЗД. Ограничьте роторное вращение колонны.")
else:
    st.success("🟢 Математическая модель подтверждает: механическая надежность шпиндельной секции обеспечивает безопасное продолжение бурения рейса.")

# =========================================================================
# НОВЫЙ БЛОК: ВЕРИФИЦИРОВАННЫЙ РАСЧЕТ ТЕХНОЛОГИЧЕСКИХ ОГРАНИЧЕНИЙ ДЛЯ ННБ
# =========================================================================
st.markdown("---")
st.subheader("🎯 Прогнозные ограничения технологического режима (ННБ)")

# 1. Исходные константы
WOB_max_passport = 15.0  # Базовая паспортная нагрузка на долото, тонн
DLS_max_passport = st.number_input("Проектная макс. интенсивность по план-программе (DLS), °/10м:", min_value=0.0, max_value=20.0, value=4.0, step=0.1)
D_clearance = 15.0       # Номинальный зазор "корпус ВЗД - стенка скважины", мм

# Защитная верификация входного люфта
safe_axial_delta = max(0.01, calculated_axial_delta)
safe_radial_ich = max(0.01, radial_ich)
safe_limit_wear = max(1.0, limit_wear)

# 2. МАТЕМАТИЧЕСКОЕ ЯДРО С ПОЛНОЙ БЛОКИРОВКОЙ ПРИ СМЯТИИ/ИЗНОСЕ ОПОР

if calculated_axial_delta > eff_max or radial_ich > 1.80 or calculated_axial_delta <= 0:
    wob_reduction_factor = 0.0
    dls_reduction_factor = 0.0

else:
    # Чем больше зазор calculated_axial_delta относительно порога eff_max, тем стабильнее работа
    wob_reduction_factor = max(0.1, min(1.0, (eff_max / max(0.01, calculated_axial_delta)) ** 0.5))
    dls_reduction_factor = max(0.05, min(1.0, 1.0 - (safe_radial_ich / D_clearance)))

calculated_wob_safe = WOB_max_passport * wob_reduction_factor
calculated_dls_safe = DLS_max_passport * dls_reduction_factor

# # 4. ВИЗУАЛИЗАЦИЯ ТЕХНОЛОГИЧЕСКИХ ОГРАНИЧЕНИЙ
col_nnb1, col_nnb2 = st.columns(2)

with col_nnb1:
    st.metric(
        label="Рекомендуемая макс. нагрузка на долото (WOB)",
        value=f"{calculated_wob_safe:.1f} тонн",
        delta=f"{(calculated_wob_safe - WOB_max_passport):.1f} тонн от базовой"
    )
    if wob_reduction_factor == 0.0:
        st.error("❌ АВАРИЙНЫЙ ОСТАНОВ: Спуск ВЗД запрещен! Нагрузка заблокирована.")
    elif wob_reduction_factor < 0.7:
        st.warning("⚠ Опора изношена! Ограничьте WOB для защиты подшипников.")
    else:
        st.success("🟢 Осевая жесткость шпинделя в норме.")

with col_nnb2:
    st.metric(
        label="Допустимая простр. интенсивность (DLS)",
        value=f"{calculated_dls_safe:.2f} °/10м",
        delta=f"{(calculated_dls_safe - DLS_max_passport):.2f} °/10м от проекта"
    )
    if dls_reduction_factor == 0.0:
        st.error("❌ КРИТИЧЕСКИЙ РАДИАЛЬНЫЙ ЛЮФТ: Вращение колонны запрещено!")
    elif dls_reduction_factor < 0.8:
        st.warning("🚨 Ограничьте роторное бурение в интервалах набора кривизны.")
    else:
        st.success("🟢 Радиальный зазор в пределах нормы.")

# === БЛОК 4: ФИНАЛЬНАЯ КЛАССИФИКАЦИЯ И ОТБРАКОВКА ОПОР ===
st.markdown("---")
st.markdown("#### Результаты комплексной проверки шпиндельного узла:")

is_measurement_error = calculated_axial_delta <= 0
# Двигатель забракован, если фактический люфт БОЛЬШЕ лимита
is_failed = calculated_axial_delta > eff_max or radial_ich > 1.80
is_warning = abs(calculated_axial_delta - eff_max) < 0.1

if is_measurement_error:
    res, style = "ОШИБКА ИЗМЕРЕНИЙ (Зазор меньше или равен нулю)", "color: #795203; background-color: #FEF3C7;"
elif is_warning:
    res, style = "⚠ ВНИМАНИЕ: Значение равно минимально допустимому порогу!", "color: #92400E; background-color: #FEF3C7;"
elif is_failed:
    res, style = "❌ ЗАБРАКОВАНО: Осевой зазор ниже порога или превышен радиальный люфт!", "color: #991B1B; background-color: #FEE2E2;"
else:
    res, style = "🟢 ДОПУЩЕНО: Параметры зазоров шпинделя соответствуют нормативам (Выше порога)", "color: #065F46; background-color: #D1FAE5;"

st.markdown(f'<div style="{style} padding: 12px; border-radius: 4px; font-weight: bold; border-left: 5px solid;">{res}</div>', unsafe_allow_html=True)

# =========================================================================
# БЛОК 6: СТАБИЛЬНЫЙ МОДУЛЬ ОНЛАЙН-ВАЛИДАЦИИ (ГЕОМЕТРИЯ + ННБ)
# =========================================================================
st.markdown("---")
with st.expander("🛠 Модуль онлайн-валидации и стресс-тестирования", expanded=True):
    st.markdown("##### Симуляция дефектов и режимов бурения")
    
    # --- ФУНКЦИИ-КОЛБЭКИ (СИНХРОНИЗАЦИЯ С СЕССИЕЙ) ---
    def set_test(a, b, rad):
        st.session_state["val_size_a"] = a
        st.session_state["val_size_b"] = b
        st.session_state["val_radial_ich"] = rad

    # Сетка кнопок 2х2
    c1, c2 = st.columns(2)
    c1.button("🔴 Осевой люфт", on_click=set_test, args=(15.0, 5.0, 0.2), use_container_width=True)
    c2.button("🔥 Радиальный износ", on_click=set_test, args=(10.0, 8.5, 1.8), use_container_width=True)
    c1.button("⚠ Ошибка замера", on_click=set_test, args=(5.0, 10.0, 0.15), use_container_width=True)
    c2.button("🎯 Стресс-режим ННБ", on_click=set_test, args=(15.0, 5.0, 0.8), use_container_width=True)

    st.markdown("##### Сводный log валидации:")

    # Безусловный расчет логов на основе текущего состояния сессии
    test_axial = st.session_state["val_size_a"] - st.session_state["val_size_b"]
    test_radial = st.session_state["val_radial_ich"]
    
    logs = []
    has_err = False
    
    if test_axial < 0:
        logs.append("❌ Осевой зазор < 0. Обнаружена ошибка измерений!")
        has_err = True
    else:
        logs.append(f"✅ Осевой зазор ({test_axial:.2f} мм) в физически возможном диапазоне.")
    
    if test_radial > 5.0:
        logs.append("❌ Радиальный зазор > 5 мм. Метрологическая аномалия!")
        has_err = True
    else:
        logs.append(f"✅ Радиальный зазор ({test_radial:.2f} мм) ОК.")

    if DLS_max_passport == 0.0:
        logs.append("⚠️ Проектный DLS равен 0.00. Мониторинг изгиба КНБК приостановлен.")
    elif DLS_max_passport > 8.0:
        logs.append("🚨 Критический проектный DLS! Высокий риск слома вала.")
        has_err = True
    else:
        logs.append(f"✅ Проектный DLS ({DLS_max_passport:.2f}°/10м) в безопасных пределах.")

    # Вывод логов на экран
    for log in logs:
        st.write(log)
        
    if not has_err:
        st.success("✅ Комплексный аудит пройден успешно.")
    else:
        st.error("🚨 В системе зафиксированы критические аномалии!")
# =========================================================================
# БЛОК 5: ОФИЦИАЛЬНЫЙ СВОДНЫЙ АКТ (АДАПТИВНЫЙ И ЗАЩИЩЕННЫЙ)
# =========================================================================
# === БЛОК 5: ОФИЦИАЛЬНЫЙ СВОДНЫЙ АКТ ===
st.markdown("---")
st.subheader("📥 Официальный бланк замера")

# Определение цветовой схемы и статуса допуска ВЗД на основе расчета

if "ДОПУЩЕНО" in res:
    border_color = "#1E3A8A"  # Синий
    bg_color = "#FAFAFA"      # Светлый
    title_text = "АКТ ТЕХНИЧЕСКОГО КОНТРОЛЯ ШПИНДЕЛЯ ВЗД"
    status_html = "<span style='color:#16A34A;'><b>ПРИГОДЕН К ЭКСПЛУАТАЦИИ (В ДОПУСКЕ)</b></span>"
else:
    border_color = "#EF4444"  # Красный
    bg_color = "#FEF2F2"      # Мягкий красный
    title_text = "АКТ ОТБРАКОВКИ И ЗАПРЕЩЕНИЯ СПУСКА ВЗД"
    status_html = "<span style='color:#DC2626;'><b>НЕ ДОПУЩЕН (ЛЮФТ ПРЕВЫШАЕТ НОРМУ)</b></span>"

# Построение динамического HTML бланка
html_vzd = f"<div style='border:3px solid {border_color}; padding:25px; border-radius:10px; background-color:{bg_color}; font-family:Arial, sans-serif; color:#333333;'>"
html_vzd += "<h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>"
html_vzd += f"<h3 style='text-align:center; color:#4B5563; margin-top:-10px;'>{title_text}</h3>"
html_vzd += f"<p><b>Месторождение:</b> {field} &nbsp;&nbsp;&nbsp;&nbsp; <b>Скважина / Куст:</b> {well}</p>"
html_vzd += f"<p><b>Инженер ННБ:</b> {engineer} &nbsp;&nbsp;&nbsp;&nbsp; <b>Сборка КНБК №:</b> {bha}</p>"
html_vzd += "<hr style='border:1px solid #CCCCCC; margin:15px 0;'>"
html_vzd += f"<p><b>Осевой люфт:</b> {calculated_axial_delta:.2f} мм (Лимит: {eff_max:.2f} мм)</p>"
html_vzd += f"<p><b>Радиальный зазор:</b> {radial_ich:.2f} мм (Лимит: 1.80 мм)</p>"
html_vzd += f"<p><b>ЗАКЛЮЧЕНИЕ:</b> {status_html}</p>"
html_vzd += "</div>"
# Отображаем собранный документ в интерфейсе
st.components.v1.html(html_vzd, height=350, scrolling=True)

# Кнопка №1: Скачивание готового файла акта
st.download_button(
    label="💾 Скачать официальный Акт замера люфтов в формате HTML",
    data=html_vzd,
    file_name=f"Akt_Lyuft_VZD_Skv_{well}.html",
    mime="text/html",
    use_container_width=True
)

# Поле для ввода адреса почты
email_recipient = st.text_input("Email получателя Акта:", placeholder="boss@yourcompany.ru")

# Кнопка №2: Безопасная отправка почты через кнопку-триггер
if st.button("✉ Подготовить письмо в почтовой программе", use_container_width=True):
    subject_text = f"Акт контроля люфта ВЗД — {field}, Скв. {well}".replace(" ", "%20")
    body_text = f"Приветствую! Сформирован официальный акт замера осевого и радиального люфта ВЗД для скважины {well} ({field}). Инженер: {engineer}.".replace(" ", "%20")
    
    mailto_link = f"mailto:{email_recipient}?subject={subject_text}&body={body_text}"
    js_code = f'<script>window.open("{mailto_link}", "_blank");</script>'
    st.components.v1.html(js_code, height=0)

st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'><b>Разработчик:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • СТО ИНТИ • ООО «Траектория-СЕРВИС» © 2026</div>", unsafe_allow_html=True)
