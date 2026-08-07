import streamlit as st
from datetime import datetime

import streamlit as st

# ПРОВЕРКА: Если инженер не залогинился на главной странице — выкидываем его назад
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пожалуйста, перейдите на Главную страницу приложения и введите пароль.")
    st.stop() # Полностью останавливаем выполнение кода этой страницы КНБК

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

# =========================================================================
# БЛОК 1: ИНИЦИАЛИЗАЦИЯ И РАЗВЕРНУТЫЙ СБОР ТЕХНОЛОГИЧЕСКИХ ПАРАМЕТРОВ ЗАМЕРА
# =========================================================================

# Синхронизация состояний для модуля валидации (выполняется один раз при старте)
if "val_size_a" not in st.session_state: st.session_state["val_size_a"] = 10.0
if "val_size_b" not in st.session_state: st.session_state["val_size_b"] = 5.5
if "val_radial_ich" not in st.session_state: st.session_state["val_radial_ich"] = 0.20

# 1. Выбор Заказчика по центру страницы с нормализацией имени
selected_client = st.selectbox(
    "1. Выберите Заказчика (Недропользователя) для применения ограничений ТК:",
    ["ПАО Роснефть", "ПАО Газпром", "ПАО Лукойл", "🔄 Без учета ограничений Заказчика"],
    key="main_client_select"
)
normalized_client_name = str(selected_client).replace("ПАО ", "").strip()

st.markdown("---")

# 2. Поля ввода геометрических измерений шпиндельной секции
st.subheader("📋 Результаты прямых измерений износа на устье скважины:")
# --- ЧАСТЬ 1.1: ТРЕХКОЛОНОЧНЫЙ ИНТЕРФЕЙС ИЗМЕРЕНИЙ ---
col_meas1, col_meas2, col_meas3 = st.columns(3)

with col_meas1:
    size_a = st.number_input("Размер 'А' (максимально выдвинут), мм:", min_value=0.0, max_value=50.0, value=10.0, step=0.01, key="val_size_a")

with col_meas2:
    size_b = st.number_input("Размер 'Б' (максимально разгружен), мм:", min_value=0.0, max_value=50.0, value=5.5, step=0.01, key="val_size_b")

with col_meas3:
    st.markdown("<p style='margin-bottom: 8px; font-size: 14px;'>Фактический радиальный зазор (по ИЧ), мм:</p>", unsafe_allow_html=True)
    radial_ich = st.number_input("Радиальный люфт", min_value=0.0, max_value=10.0, value=0.20, step=0.01, label_visibility="collapsed", key="val_radial_ich")

calculated_axial_delta = size_a - size_b

# Вычисление фактического осевого перемещения
calculated_axial_delta = size_a - size_b

# =========================================================================
# БЛОК 2: НОРМАТИВНЫЕ БАЗЫ ДАННЫХ И КАТЕГОРИРОВАНИЕ ВЗД - ЧАСТЬ 2.1
# =========================================================================

# --- ЧАСТЬ 2.1.1: ПОЛНАЯ БАЗА ДАННЫХ ВЗД (НАЧАЛО) ---
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
    "ВНИИБТ": {
        "Д-43": 1.5, "Д-54": 1.5, "Д-73": 1.5, "Д-76": 2.0, "Д-85": 2.0,
        "Д-88": 2.0, "Д-95": 2.5, "Д-106": 3.0, "Д-127": 3.0, "Д-165": 4.5,
        "Д-172": 4.5, "Д-195": 5.0, "Д-240М": 6.0
    },
    "ООО НГТ": {
        "Д1-54": 2.0, "Д1-73": 2.0, "Д1-88": 2.5, "Д1-106": 3.0, "Д1-127": 3.5,
        "Д1-172": 5.0, "Д1-195": 5.5, "Д1-240": 6.5
    },
    "NOV": {
        "4-3/4''": 6.35, "6-1/2''": 9.52, "8''": 12.70, "9-5/8''": 15.87
    }
} # Закрывающая скобка всего словаря base_vzd

# Выбор производителя из полного списка
selected_brand = st.selectbox("2. Выберите производителя:", list(base_vzd.keys()), key="b4_brand_select")
# =========================================================================
# БЛОК 2: АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ КАТЕГОРИИ ГАБАРИТА ВЗД - ЧАСТЬ 2.2
# =========================================================================

# Вытягиваем список моделей для выбранного завода-изготовителя
current_brand_models = base_vzd[selected_brand]
selected_diameter = st.selectbox("3. Выберите габарит / шифр модели:", list(current_brand_models.keys()), key="b4_model_select")

# Фиксируем паспортный лимит износа для выбранного габарита
limit_wear = current_brand_models[selected_diameter]

# Интеллектуальный поиск категории по расширенной матрице ключевых слов
if any(marker in selected_diameter for marker in ["43", "54", "73", "75", "76", "85", "88", "95", "98", "106", "120", "127", "4-3/4''", "5''"]):
    size_group = "малый"
elif any(marker in selected_diameter for marker in ["195", "210", "240", "8''", "9-5/8''"]):
    size_group = "большой"
else:
    size_group = "средний"
# =========================================================================
# БЛОК 2: НОРМАТИВНЫЕ ЛИМИТЫ - ЧАСТЬ 2.3 (ФИНАЛЬНЫЙ РАСЧЕТ ДОПУСКА)
# =========================================================================

# Логика подбора лимитов в зависимости от выбранного ВИНК
if selected_client != "🔄 Без учета ограничений Заказчика":
    # Извлекаем норму Заказчика на основе весовой группы габарита
    client_rule_axial = client_limits_db[selected_client][size_group]
    # Выбираем наиболее жесткий критерий отбраковки (минимальный)
    effective_max_axial = min(limit_wear, client_rule_axial)
    
    st.info(f"🔷 **Анализ лимитов:** Паспорт завода = {limit_wear:.2f} мм | Регламент {selected_client} ({size_group}) = {client_rule_axial:.2f} мм")
    st.warning(f"🎯 **Итоговый критерий:** Осевой люфт шпинделя на устье до **{effective_max_axial:.2f} мм**")
else:
    # Если Заказчик не выбран, контролируем строго по паспорту завода
    effective_max_axial = limit_wear
    st.info(f"🎯 **Итоговый критерий (Паспортный):** Осевой люфт шпинделя на устье до **{effective_max_axial:.2f} мм**")

# Устанавливаем жесткий нормативный радиальный предел отбраковки по СТО ИНТИ
effective_max_radial = 1.00

# =========================================================================
# БЛОК 2: НОРМАТИВНЫЕ ЛИМИТЫ - ЧАСТЬ 2.2 (РАСЧЕТ КРИТЕРИЯ ОТБРАКОВКИ)
# =========================================================================

# --- ЧАСТЬ 2.2.1: ОПРЕДЕЛЕНИЕ КАТЕГОРИИ ГАБАРИТА ---
current_brand_models = base_vzd[selected_brand]
selected_diameter = st.selectbox("3. Выберите габарит / шифр модели:", list(current_brand_models.keys()), key="b4_model_select")

# Присваиваем базовый лимит
limit_wear = current_brand_models[selected_diameter]

# Маркеры для сканирования и присвоения группы
if any(m in selected_diameter for m in ["43", "54", "73", "75", "88", "95", "98", "106", "120", "127", "5''"]):
    size_group = "малый"
elif any(m in selected_diameter for m in ["195", "210", "240", "8''", "9-5/8''"]):
    size_group = "большой"
else:
    size_group = "средний"
# --- ЧАСТЬ 2.2.2: СВЕРКА ЛИМИТОВ С РЕГЛАМЕНТАМИ ЗАКАЗЧИКОВ ---
# Если выбран конкретный Заказчик, извлекаем его норму на основе весовой группы
if selected_client != "🔄 Без учета ограничений Заказчика":
    client_rule_axial = client_limits_db[selected_client][size_group]
    effective_max_axial = min(limit_wear, client_rule_axial)
    
    st.info(f"🔷 **Анализ:** Паспорт завода = {limit_wear:.2f} мм | Ограничение {selected_client} ({size_group}) = {client_rule_axial:.2f} мм")
    st.warning(f"🎯 **Критерий (устье):** Осевой люфт до **{effective_max_axial:.2f} мм**")
else:
    effective_max_axial = limit_wear
    st.info(f"🎯 **Критерий (Паспортный):** Осевой люфт до **{effective_max_axial:.2f} мм**")

# Результирующий жесткий радиальный предел отбраковки для всех габаритов
effective_max_radial = 1.00

# =========================================================================
# БЛОК 3: ИНТЕЛЛЕКТУАЛЬНЫЙ ИИ-АУДИТ И ЭКСПЕРТНЫЙ АНАЛИЗ РИСКОВ (СППР)
# =========================================================================
st.markdown(" ")
st.markdown(f"##### 🔬 Технический ИИ-анализ состояния и уязвимостей опор для вендора: {selected_brand}")

# Формируем глубокую аналитическую базу под каждого производителя КНБК
if selected_brand == "Радиус-Сервис":
    vzd_expert_review = (
        f"📎 **Экспертная оценка силовой пары {selected_brand}:** Двигатели данного типа обладают повышенной "
        f"жесткостью осевых опор шпинделя. Однако при превышении осевого люфта свыше паспортного значения **({limit_wear:.2f} мм)** "
        f"резко возрастает риск циклического усталостного разрушения упорно-торцевых полок вала. "
    )
    if radial_ich > 0.30:
        vzd_expert_review += "🚨 **КРИТИЧЕСКИЙ СДВИГ:** Повышенный радиальный зазор указывает на интенсивный износ нижнего радиального подшипника (втулки). Это приведет к радиальному биению долота, разрушению его вооружения и ускоренной деградации телесистемы (MWD) из-за вибраций."
    else:
        vzd_expert_review += "🟢 Текущее радиальное центрирование вала находится в пределах технологической нормы."

elif selected_brand == "NOV":
    vzd_expert_review = (
        f"📎 **Экспертная оценка шпиндельной секции {selected_brand}:** Американские шпиндельные узлы NOV "
        f"проектируются под высокие гидравлические и осевые нагрузки. "
    )
    if calculated_axial_delta > limit_nominal:
        vzd_expert_review += "⚠️ **Внимание:** Осевой люфт перешагнул за 50% от паспортного лимита отбраковки. Наблюдается частичное выкрашивание дорожек качения многорядных шарикоподшипников. Бурение допускается, но с ограничением нагрузки на долото (WOB) на 15-20%."
    else:
        vzd_expert_review += "🟢 Механическое состояние подшипниковых пакетов стабильно."

elif selected_brand == "ВНИИБТ":
    vzd_expert_review = (
        f"📎 **Экспертная оценка турбобуров/ВЗД {selected_brand}:** Классическая многоступенчатая осевая опора (резинометаллическая пята). "
        f"Износ идет за счет гидроабразивного смыва резиновых обкладок средних ступеней. "
    )
    if sand_input_val > 0.5 if 'sand_input_val' in locals() else False:
        vzd_expert_review += "🚨 **Абразивный износ:** Высокое содержание песка в растворе ускорит износ этих резинометаллических элементов в 2-3 раза. Требуется непрерывный контроль перепада давления на стояке."
    else:
        vzd_expert_review += "⚠️ Требуется регулярный замер люфта после каждого рейса для отслеживания динамики притирки ступеней."

else:
    vzd_expert_review = f"📎 **Общее техническое заключение:** Состояние опор оценивается по базовому регламенту входного контроля КНБК. Особое внимание уделить проверке люфтов после СПО."

# Выводим развернутое ИИ-заключение на экран в синюю рамку инфо-панели
st.info(vzd_expert_review)
# =========================================================================
# БЛОК 4: ФИНАЛЬНАЯ КЛАССИФИКАЦИЯ РЕЗУЛЬТАТОВ РАСЧЕТА И ОТБРАКОВКА ОПОР
# =========================================================================
st.markdown("---")
st.markdown("#### Результаты комплексной проверки шпиндельного узла:")

# Вывод численных параметров замера инженеру на экран
col_out1, col_out2 = st.columns(2)
with col_out1:
    st.write(f"**Фактический осевой люфт (Δh):** {calculated_axial_delta:.2f} мм (Предел: {effective_max_axial:.2f} мм)")
with col_out2:
    st.write(f"**Фактический радиальный люфт:** {radial_ich:.2f} мм (Предел: {effective_max_radial:.2f} мм)")

# --- МАТЕМАТИЧЕСКАЯ ЛОГИКА МНОГООСЕВОЙ ОТБРАКОВКИ ---
is_axial_failed = calculated_axial_delta > effective_max_axial
is_radial_failed = radial_ich > effective_max_radial
is_measurement_error = calculated_axial_delta <= 0

if is_measurement_error:
    # Защита от некорректного замера ИЧ
    res_text = "ОШИБКА ИЗМЕРЕНИЙ! РАЗМЕР 'А' ДОЛЖЕН БЫТЬ СТРОГО БОЛЬШЕ РАЗМЕРА 'Б'. ПЕРЕПРОВЕРЬТЕ ПОКАЗАНИЯ ИНДИКАТОРА ЧАСОВОГО ТИПА."
    status_box_color = "#F59E0B"  # Оранжевый предупреждающий цвет
    status_text_color = "#795203"
    status_bg = "#FEF3C7"
    is_vzd_allowed = False

elif is_axial_failed or is_radial_failed:
    # Формируем жесткий отбраковочный статус (КРАСНЫЙ КАПСЛОК)
    failures_reasons = []
    if is_axial_failed: failures_reasons.append(f"ОСЕВОМУ ЛЮФТУ ({calculated_axial_delta:.2f} мм > {effective_max_axial:.2f} мм)")
    if is_radial_failed: failures_reasons.append(f"РАДИАЛЬНОМУ ЛЮФТУ ({radial_ich:.2f} мм > {effective_max_radial:.2f} мм)")
    
    reasons_str = " И ".join(failures_reasons)
    res_text = f"🚨 КРИТИЧЕСКИЙ ИЗНОС ОПОР ШПИНДЕЛЯ ПО {reasons_str}! СПУСК ЗАБОЙНОГО ДВИГАТЕЛЯ В СКВАЖИНУ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕН! ТРЕБУЕТСЯ СРОЧНАЯ ЗАМЕНА ВЗД НА БУРОВОЙ!"
    
    # Перевод финального текста в КАПСЛОК
    res_text = res_text.upper()
    status_box_color = "#EF4444"  # Строгий красный цвет
    status_text_color = "#991B1B"
    status_bg = "#FEE2E2"
    is_vzd_allowed = False

else:
    # Оборудование полностью исправно (Зеленый цвет)
    res_text = f"Технологический статус в норме. Осевой зазор ({calculated_axial_delta:.2f} мм) и радиальный зазор ({radial_ich:.2f} мм) соответствуют критериям безопасной эксплуатации КНБК. Двигатель допущен к спуску в скважину."
    status_box_color = "#10B981"  # Насыщенный зеленый цвет
    status_text_color = "#065F46"
    status_bg = "#D1FAE5"
    is_vzd_allowed = True

# Рендеринг динамической плашки статуса контроля на экран
st.markdown(
    f'<div style="color: {status_text_color}; background-color: {status_bg}; padding: 12px; border-radius: 4px; font-weight: bold; border-left: 5px solid {status_box_color}; margin-top: 10px; line-height: 1.4;">'
    f'{res_text}</div>',
    unsafe_allow_html=True
)
# =========================================================================
# БЛОК 5: ОФИЦИАЛЬНЫЙ СВОДНЫЙ АКТ И ВЫГРУЗКА ДОКУМЕНТАЦИИ (БЕЗ ИКОНОК)
# =========================================================================
st.markdown("---")
st.subheader("📥 Официальный бланк замера для рапорта:")

# --- 1. ПЕРЕМЕННЫЕ И ЦВЕТА ---
rep_time = datetime.now().strftime("%d.%m.%Y %H:%M")
html_status_color = "red" if (is_axial_failed or is_radial_failed) else "green"

# --- 2. ГЕНЕРАЦИЯ HTML-БЛАНКА ---
html_vzd = f"""
<div style='border:2px solid #333; padding:20px; font-family:Arial, sans-serif;'>
<h2 style='text-align:center;'>ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>
<h3 style='text-align:center;'>АКТ ТЕХНИЧЕСКОГО КОНТРОЛЯ ШПИНДЕЛЯ ВЗД</h3>
<p><b>Дата:</b> {rep_time} | <b>Инженер:</b> {engineer_name}</p>
<p><b>Скважина:</b> {well_number} | <b>Месторождение:</b> {field_name}</p>
<p><b>Двигатель:</b> {vzd_model_name} (№: {vzd_passport_number})</p>
<hr>
<p><b>Осевой люфт:</b> {calculated_axial_delta:.2f} мм (Предел: {effective_max_axial:.2f})</p>
<p><b>Радиальный люфт:</b> {radial_ich:.2f} мм (Предел: {effective_max_radial:.2f})</p>
<p style='color:{html_status_color}; font-weight:bold; font-size:16px;'>ЗАКЛЮЧЕНИЕ: {res_text}</p>
</div>
"""
st.markdown(html_vzd, unsafe_allow_html=True)

# --- 3. ПОДГОТОВКА ДАННЫХ И КНОПКИ ЭКСПОРТА ---
txt_report = f"АКТ ВЗД {well_number}\nДата: {rep_time}\nСтатус: {res_text}\nОсевой: {calculated_axial_delta:.2f}\nРадиальный: {radial_ich:.2f}"
csv_row = f"{rep_time},{well_number},{calculated_axial_delta:.2f},{radial_ich:.2f},{res_text}"

st.markdown(" ")
col1, col2 = st.columns(2)
col1.download_button("📄 .txt Акт", txt_report, file_name="akt.txt")
col2.download_button("📊 .csv Данные", csv_row, file_name="data.csv")
# =========================================================================
# БЛОК 6: МОДУЛЬ ОНЛАЙН-ВАЛИДАЦИИ И СТРЕСС-ТЕСТИРОВАНИЯ ГЕОМЕТРИЧЕСКОГО ЯДРА
# =========================================================================
st.markdown("---")

with st.expander("🛠 Модуль онлайн-валидации и стресс-тестирования геометрического ядра"):
    st.markdown("##### Симуляция критических дефектов шпиндельной секции")
    st.caption("Выберите тестовый сценарий для проверки устойчивости алгоритмов многоосевой отбраковки КНБК:")
    
    # --- ФУНКЦИИ-КОЛБЭКИ ДЛЯ ИЗМЕНЕНИЯ СЕССИИ ---
    def set_test_critical_axial():
        st.session_state["val_size_a"], st.session_state["val_size_b"], st.session_state["val_radial_ich"] = 15.00, 5.00, 0.20

    def set_test_critical_radial():
        st.session_state["val_size_a"], st.session_state["val_size_b"], st.session_state["val_radial_ich"] = 10.00, 8.50, 1.80

    def set_test_measurement_error():
        st.session_state["val_size_a"], st.session_state["val_size_b"], st.session_state["val_radial_ich"] = 5.00, 10.00, 0.15

    # Кнопки стресс-тестов
    c1, c2, c3 = st.columns(3)
    c1.button("🔴 Тест 1: Критический осевой люфт", on_click=set_test_critical_axial, use_container_width=True)
    c2.button("🔥 Тест 2: Критический радиальный износ", on_click=set_test_critical_radial, use_container_width=True)
    c3.button("⚠️ Тест 3: Симуляция ошибки замера", on_click=set_test_measurement_error, use_container_width=True)

    st.markdown("##### Сводный лог валидации геометрии (СТО ИНТИ):")
    
    # Валидация и логирование (упрощено для читаемости)
    geo_logs = []
    geo_passed = True
    
    if calculated_axial_delta < 0:
        geo_logs.append("❌ Осевой зазор < 0. Ошибка ввода!")
        geo_passed = False
    else:
        geo_logs.append(f"✅ Осевой зазор Δh ({calculated_axial_delta:.2f} мм) ОК.")
        
    if radial_ich > 5.00:
        geo_logs.append("❌ Радиальный зазор > 5 мм. Физически невозможен.")
        geo_passed = False
    elif radial_ich == 0:
        geo_logs.append("⚠️ Радиальный люфт = 0. Требуется проверка.")
    else:
        geo_logs.append(f"✅ Радиальный зазор ({radial_ich:.2f} мм) ОК.")

    # Вывод логов
    for log in geo_logs:
        st.write(log)
        
    if geo_passed: st.success("🎯 Авто-аудит пройден.")
    else: st.error("🚨 Обнаружены математические аномалии!")

# --- 11. ФУТЕРЫ СТРАНИЦЫ И ИНСТРУКЦИЯ ПО ПЕЧАТИ ---
st.markdown(" ")
st.info("💡 **Инструкция по сохранению:** Для вывода Акта на печать или сохранения в PDF нажмите **`Ctrl + P`**.")
st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'><b>Разработчик:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • СТО ИНТИ • ООО «Траектория-СЕРВИС» © 2026</div>", unsafe_allow_html=True)









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
    <h2 style='text-align:center; color:#1E3A8A; margin-top:0;'>ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>
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
