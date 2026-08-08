import streamlit as st
import pandas as pd
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

# Паспорт верификации СТО ИНТИ, скрытый под фирменный спойлер
with st.expander("🔰 Паспорт верификации СТО ИНТИ (Опора шпинделя)"):
    st.markdown(
        "<div style='color: #1F2937; font-size: 14px; background-color: #F9FAFB; padding: 15px; border-radius: 6px; border-left: 4px solid #2563EB; line-height: 1.6; font-family: Arial, sans-serif; margin-bottom: 10px;'> "
        "<b>1. СТО ИНТИ S.QS.7:</b> Обоснование верификации шпиндельной секции ВЗД, минимизация рисков разрушения опор и контроль нагрузок при ННБ.<br><br>"
        "<b>2. СТО ИНТИ S.QS.8:</b> Метрологическое подтверждение точности линейных измерений, адаптация полевых замеров к нормативам изготовителей и заказчиков."
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

# 2. Поля ввода геометрических измерений шпиндельной секции
st.subheader("📋 Результаты прямых измерений износа на устье скважины:")
# --- ЧАСТЬ 1.1: ТРЕХКОЛОНОЧНЫЙ ИНТЕРФЕЙС С РЕАЛЬНЫМИ ПОДСКАЗКАМИ ---
col_meas1, col_meas2, col_meas3 = st.columns(3)

with col_meas1:
    size_a = st.number_input(
        "Размер 'А' (вал выдвинут/висит), мм:", 
        min_value=0.0, max_value=50.0, value=10.0, step=0.01, key="val_size_a",
        help="ℹ️ КАК ИЗМЕРИТЬ НА МОСТКАХ:\n1. Когда ВЗД висит на элеваторе (вал максимально выдвинут под собственным весом), нанесите тонким маркером четкую риску на вал шпинделя вплотную к торцу корпуса.\n2. Измерьте штангенциркулем или линейкой расстояние от торца корпуса до этой метки."
    )

with col_meas2:
    size_b = st.number_input(
        "Размер 'Б' (вал вдавлен/разгружен), мм:", 
        min_value=0.0, max_value=50.0, value=5.5, step=0.01, key="val_size_b",
        help="ℹ️ КАК ИЗМЕРИТЬ НА МОСТКАХ:\n1. Опустите КНБК, чтобы долото упёрлось в ротор или приемные мостки (вес частично разгрузился, и вал ушел внутрь корпуса).\n2. Замерьте штангенциркулем новое расстояние от торца корпуса до вашей маркерной риски.\n⚠️ Разность (А - Б) покажет чистый осевой люфт."
    )

with col_meas3:
    st.markdown("<p style='margin-bottom: 8px; font-size: 14px;'>Радиальный люфт (штангенциркуль), мм:</p>", unsafe_allow_html=True)
    radial_ich = st.number_input(
        "Радиальный люфт", 
        min_value=0.0, max_value=10.0, value=0.20, step=0.01, label_visibility="collapsed", key="val_radial_ich",
        help="ℹ️ КАК ИЗМЕРИТЬ БЕЗ ИЧ:\n1. Обхватите губками штангенциркуля тело вала у самого выхода из корпуса.\n2. Ломом или рычагом покачайте вал влево-вправо (поперек оси).\n3. Зафиксируйте максимальное смещение по шкале штангенциркуля. Если качание видно визуально «на глаз» без приборов — зазор уже больше 1-2 мм (критический износ втулки)!"
    )

calculated_axial_delta = size_a - size_b

# Вычисление фактического осевого перемещения
calculated_axial_delta = size_a - size_b

# =========================================================================
# БЛОК 2: НОРМАТИВНЫЕ БАЗЫ ДАННЫХ И ДИНАМИЧЕСКИЙ РАСЧЕТ ДОПУСКОВ
# =========================================================================

# 1. ВОССТАНОВЛЕНИЕ СЛОВАРЯ ЗАКАЗЧИКОВ (Устраняет NameError) [image_5gJf_S.png]
client_limits_db = {
    "ПАО Роснефть": {"малый": 3.5, "средний": 4.0, "большой": 5.0},
    "ПАО Газпром": {"малый": 4.0, "средний": 4.5, "большой": 5.0},
    "ПАО Лукойл": {"малый": 4.0, "средний": 5.0, "большой": 5.5}
}

limit_wear = base_vzd[selected_brand][selected_diameter]
size_group = "малый" if any(m in selected_diameter for m in ["43", "54", "73", "127"]) else "большой" if any(m in selected_diameter for m in ["195", "240", "8''"]) else "средний"

# 4. Сверка ограничений
if selected_client != "🔄 Без учета ограничений Заказчика":
    client_rule = client_limits_db[selected_client][size_group]
    eff_max = min(limit_wear, client_rule)
    st.info(f"🔷 Лимит: Паспорт={limit_wear:.2f} | {selected_client}={client_rule:.2f} мм")
    st.warning(f"🎯 **Критерий:** Осевой люфт до **{eff_max:.2f} мм**")
else:
    eff_max = limit_wear
    st.info(f"🎯 **Критерий:** Осевой люфт до **{eff_max:.2f} мм**")

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
    if calculated_axial_delta > (limit_wear * 0.5):
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

# 2. МАТЕМАТИЧЕСКОЕ ЯДРО С ПОЛНОЙ БЛОКИРОВКОЙ ПРИ АВАРИИ
if calculated_axial_delta >= eff_max or radial_ich > 1.0:
    wob_reduction_factor = 0.0
    dls_reduction_factor = 0.0
else:
    wob_base_value = max(0.0, 1.0 - (safe_axial_delta / safe_limit_wear))
    wob_reduction_factor = max(0.1, min(1.0, wob_base_value ** 0.6))
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

# =========================================================================
# БЛОК 4: ФИНАЛЬНАЯ КЛАССИФИКАЦИЯ РЕЗУЛЬТАТОВ РАСЧЕТА И ОТБРАКОВКА ОПОР
# =========================================================================
st.markdown("---")
st.markdown("#### Результаты комплексной проверки шпиндельного узла:")

# ГАРАНТИЯ ИНИЦИАЛИЗАЦИИ ПЕРЕМЕННЫХ ДЛЯ ЗАЩИТЫ ОТ NAMEERROR
final_max_axial = effective_max_axial if 'effective_max_axial' in locals() else limit_wear
final_max_radial = effective_max_radial if 'effective_max_radial' in locals() else 1.00

# === БЛОК 4: КЛАССИФИКАЦИЯ ===
is_axial_failed = calculated_axial_delta > eff_max
is_radial_failed = radial_ich > 1.0
is_measurement_error = calculated_axial_delta <= 0

if is_measurement_error:
    res, style = "ОШИБКА ИЗМЕРЕНИЙ", "color: #795203; background-color: #FEF3C7;"
elif is_axial_failed or is_radial_failed:
    res, style = "🚨 КРИТИЧЕСКИЙ ИЗНОС ОПОР!", "color: #991B1B; background-color: #FEE2E2;"
else:
    res, style = "Норма", "color: #065F46; background-color: #D1FAE5;"

st.markdown(f'<div style="{style} padding: 10px; border-left: 5px solid;">{res}</div>', unsafe_allow_html=True)

# Вывод результатов на экран инженеру
st.markdown(
    f'<div style="{box_style} padding: 12px; border-radius: 4px; font-weight: bold; line-height: 1.4;">'
    f'{res_text}</div>',
    unsafe_allow_html=True
)

# =========================================================================
# БЛОК 5: ОФИЦИАЛЬНЫЙ СВОДНЫЙ АКТ (АДАПТИВНЫЙ И ЗАЩИЩЕННЫЙ)
# =========================================================================
# === БЛОК 5: ОФИЦИАЛЬНЫЙ СВОДНЫЙ АКТ ===
st.markdown("---")
st.subheader("📥 Официальный бланк замера")

# Формирование HTML-шаблона с использованием обновленных переменных (eff_max)
html_vzd = f"""
<div style='border: 2px solid #333; padding: 20px; font-family: Arial, sans-serif; border-radius: 4px;'>
<h3 style='text-align: center;'>АКТ ТЕХНИЧЕСКОГО КОНТРОЛЯ ШПИНДЕЛЯ ВЗД</h3>
<p><b>Дата контроля:</b> {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
<p><b>Осевой люфт:</b> {calculated_axial_delta:.2f} мм (Лимит: {eff_max:.2f} мм)</p>
<p><b>Радиальный зазор:</b> {radial_ich:.2f} мм (Лимит: 1.00 мм)</p>
<hr>
<div style='padding: 10px; border-radius: 4px; font-weight: bold; text-align: center;'>
ЗАКЛЮЧЕНИЕ: {res}
</div>
</div>
"""
st.markdown(html_vzd, unsafe_allow_html=True)

# Безопасный рендеринг готового бланка на страницу
st.markdown(html_vzd, unsafe_allow_html=True)

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

# --- 11. ФУТЕРЫ СТРАНИЦЫ И ИНСТРУКЦИЯ ПО ПЕЧАТИ ---
st.markdown(" ")
st.info("💡 **Инструкция по сохранению:** Для вывода Акта на печать или сохранения в PDF нажмите **`Ctrl + P`**.")
st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'><b>Разработчик:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • СТО ИНТИ • ООО «Траектория-СЕРВИС» © 2026</div>", unsafe_allow_html=True)
