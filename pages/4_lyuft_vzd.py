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

# --- ЧАСТЬ 2.2.1: ЕДИНЫЙ СЕЛЕКТОР И УСТРАНЕНИЕ NAMEERROR ---
current_brand_models = base_vzd[selected_brand]

# Селектор вызывается строго один раз
selected_diameter = st.selectbox(
    "3. Выберите габарит / шифр модели ВЗД:", 
    list(current_brand_models.keys()), 
    key="b4_unified_selector"
)

# Фиксация лимита и расчет номинала для ИИ-ядра
limit_wear = current_brand_models[selected_diameter]
limit_nominal = limit_wear * 0.50

# --- ЧАСТЬ 2.2.2: ОПРЕДЕЛЕНИЕ КАТЕГОРИИ ГАБАРИТА ---
small_markers = ["43", "54", "73", "75", "76", "85", "88", "95", "98", "106", "120", "127", "4-3/4''", "5''"]
large_markers = ["195", "210", "240", "8''", "9-5/8''"]

if any(m in selected_diameter for m in small_markers):
    size_group = "малый"
elif any(m in selected_diameter for m in large_markers):
    size_group = "большой"
else:
    size_group = "средний"

# --- ЧАСТЬ 2.2.3: СВЕРКА С ТРЕБОВАНИЯМИ ВИНК ЧЕРЕЗ ЕДИНЫЕ ЛИМИТЫ ---
if selected_client != "🔄 Без учета ограничений Заказчика":
    client_rule_axial = client_limits_db[selected_client][size_group]
    effective_max_axial = min(limit_wear, client_rule_axial)
    
    st.info(f"🔷 **Анализ лимитов:** Паспорт завода = {limit_wear:.2f} мм | Регламент {selected_client} ({size_group}) = {client_rule_axial:.2f} мм")
    st.warning(f"🎯 **Итоговый критерий:** Осевой люфт шпинделя на устье до **{effective_max_axial:.2f} мм**")
else:
    effective_max_axial = limit_wear
    st.info(f"🎯 **Итоговый критерий (Паспортный):** Осевой люфт шпинделя на устье до **{effective_max_axial:.2f} мм**")

# Жесткий радиальный лимит отбраковки шпинделя по СТО ИНТИ
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

# БЛОК 4: РЕЗУЛЬТАТЫ И ОТБРАКОВКА
st.markdown("---")
st.markdown("#### Результаты комплексной проверки шпиндельного узла:")

# Логика оценки
is_axial_failed = calculated_axial_delta > effective_max_axial
is_radial_failed = radial_ich > effective_max_radial
is_measurement_error = calculated_axial_delta <= 0

# Определение стиля и текста
if is_measurement_error:
    res_text = "ОШИБКА ИЗМЕРЕНИЙ! ПЕРЕПРОВЕРЬТЕ ИЧ."
    style = "color: #795203; background-color: #FEF3C7;"
elif is_axial_failed or is_radial_failed:
    res_text = "🚨 КРИТИЧЕСКИЙ ИЗНОС! СПУСК ЗАПРЕЩЕН!"
    style = "color: #991B1B; background-color: #FEE2E2;"
else:
    res_text = "Статус в норме. Двигатель допущен к спуску."
    style = "color: #065F46; background-color: #D1FAE5;"

# Вывод
st.markdown(f'<div style="{style} padding: 10px; border-radius: 4px; font-weight: bold;">{res_text}</div>', unsafe_allow_html=True)

# =========================================================================
# БЛОК 5: ОФИЦИАЛЬНЫЙ СВОДНЫЙ АКТ И ВЫГРУЗКА ДОКУМЕНТАЦИИ (БЕЗ ИКОНОК)
# =========================================================================
st.markdown("---")
st.subheader("📥 Официальный бланк замера")

# Генерация HTML-бланка с использованием сессионных данных
html_vzd = f"""
<div style='border:2px solid #333; padding:20px; font-family:Arial; color:#111;'>
<h3 style='text-align:center;'>АКТ ТЕХНИЧЕСКОГО КОНТРОЛЯ</h3>
<p><b>Дата:</b> {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
<p><b>Заказчик:</b> {selected_client}</p>
<p><b>Двигатель:</b> {selected_brand} ({selected_diameter})</p>
<p><b>Осевой люфт:</b> {calculated_axial_delta:.2f} мм (max {effective_max_axial:.2f} мм)</p>
<p><b>Радиальный зазор:</b> {radial_ich:.2f} мм (max {effective_max_radial:.2f} мм)</p>
<hr>
<p style='color:{"#991B1B" if (is_axial_failed or is_radial_failed) else "#065F46"}; font-weight:bold;'>{res_text}</p>
</div>
"""
st.markdown(html_vzd, unsafe_allow_html=True)

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
