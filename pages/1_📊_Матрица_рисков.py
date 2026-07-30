import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Матрица рисков", layout="wide")

st.title("🧭 Цифровой помощник инженера «Траектория-Сервис»")
st.caption("СВОДНАЯ МАТРИЦА РИСКОВ И ИНЖЕНЕРНЫХ РЕШЕНИЙ")
st.markdown("---")

well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

report_text = ""
current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

tab1, tab2, tab3 = st.tabs(["🔧 Входной контроль и ВЗД", "🚨 Осложнения при сборке", "📋 Требования инструкции"])

with tab1:
    st.subheader("Ликвидация осложнений при входном контроле")
    p_type = st.selectbox(
        "Выберите симптом / операцию:",
        ["Не выбрано", "Замер осевого люфта шпинделя ВЗД", "Резьба заклинила на первых витках", "Оценка задиров резьбы", "Обнаружена течь при гидроиспытаниях"],
        key="p_type_key"
    )
    
    if "Замер осевого люфта" in p_type:
        st.info("📝 МЕТОДИКА ЗАМЕРА: Люфт = Размер А (Растянуто) - Размер Б (Сжато)")
        col_vzd1, col_vzd2 = st.columns(2)
        with col_vzd1:
            selected_brand = st.selectbox("Производитель ВЗД:", ["Радиус-Сервис", "ВНИИБТ", "Гидробур", "НГТ", "NOV"])
        with col_vzd2:
            selected_diameter = st.selectbox("Диаметр (типоразмер) двигателя:", ["98 мм", "106 мм", "120 мм", "172 мм", "240 мм"])
            
        limit_wear = 5.0 if selected_diameter == "172 мм" else (6.0 if selected_diameter == "240 мм" else 4.5)
        st.markdown("---")
        
        col_calc1, col_calc2 = st.columns(2)
        with col_calc1:
            size_a = st.number_input("Размер 'А' (Растянуто под своим весом), мм:", min_value=0.0, value=10.0, step=0.1)
        with col_calc2:
            size_b = st.number_input("Размер 'Б' (Сжато при разгрузке на ротор), мм:", min_value=0.0, value=5.5, step=0.1)
        
        calculated_delta = size_a - size_b
        st.markdown("### Результаты анализа шпинделя:")
        st.metric(label="Фактический осевой люфт:", value=f"{calculated_delta:.1f} мм")
        
        if calculated_delta > limit_wear:
            res_text = "КРИТИЧЕСКИЙ ИЗНОС ОПОР! Люфт превышает лимит. СПУСК В СКВАЖИНУ ЗАПРЕЩЕН!"
            st.error(res_text)
            report_text = "ПРОТОКОЛ КОНТРОЛЯ ВЗД\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИнженер: " + engineer_name + "\nИтог: " + res_text
        elif calculated_delta > 0:
            res_text = "ЛЮФТ В НОРМЕ. ДВИГАТЕЛЬ ДОПУЩЕН К СПУСКУ."
            st.success(res_text)
            report_text = "ПРОТОКОЛ КОНТРОЛЯ ВЗД\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИнженер: " + engineer_name + "\nИтог: " + res_text
            
    if p_type == "Резьба заклинила на первых витках":
        st.warning("Действие: СТОП вращение! Открутить назад вручную, смыть смазку.")
        ans = st.radio("Дефекты отсутствуют?", ["Не выбрано", "Да", "Нет"], key="t1_r2")
        if ans == "Да":
            res = "ДОПУСК РЕЗЬБЫ. Смазка 2/3 муфта, 1/3 ниппель. Продолжить сборку."
            st.success(res)
            report_text = "ПРОТОКОЛ КНБК (Резьба)\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res
        if ans == "Нет":
            res = "ОТБРАКОВКА РЕЗЬБЫ. Вызвать резервный переводник/трубу."
            st.error(res)
            report_text = "ПРОТОКОЛ КНБК (Резьба)\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res

    if p_type == "Оценка задиров резьбы":
        st.warning("Действие: Оценить глубину дефектов.")
        ans = st.radio("Возможна ручная зачистка надфилем в пределах допуска?", ["Не выбрано", "Да", "Нет"], key="t1_r3")
        if ans == "Да":
            res = "ДОПУСК. Зачистить надфилем, нанести резьбовую смазку."
            st.success(res)
            report_text = "ПРОТОКОЛ КНБК (Задиры)\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res
        if ans == "Нет":
            res = "ОТБРАКОВКА ЭЛЕМЕНТА. Оформить Акт дефекта."
            st.error(res)
            report_text = "ПРОТОКОЛ КНБК (Задиры)\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res

    if p_type == "Обнаружена течь при гидроиспытаниях":
        st.warning("Действие: СТОП насосы буровой! Сбросить избыточное давление.")
        ans = st.radio("Локализация выхода бурового раствора:", ["Не выбрано", "В замковом стыке", "Из тела корпуса ВЗД"], key="t1_r4")
        if ans == "В замковом стыке":
            res = "ТЕЧЬ В СТЫКЕ. Докрепить соединение ключами УМК до верхнего паспортного предела."
            st.success(res)
            st.info("💡 Используйте модуль 'Расчет УМК' в левом меню для корректировки момента ключа!")
            report_text = "ПРОТОКОЛ ОПРЕССОВКИ\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res
        if ans == "Из тела корпуса ВЗД":
            res = "ТЕЧЬ ИЗ КОРПУСА. ВЗД ЗАБРАКОВАН! Трещина корпуса или уплотнений."
            st.error(res)
            report_text = "ПРОТОКОЛ ОПРЕССОВКИ\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res

with tab2:
    st.subheader("Карта решений при технологических осложнениях")
    p_type_2 = st.selectbox(
        "Выберите зафиксированное отклонение:",
        ["Не выбрано", "Нет пакета данных MWD / Падение давления на тесте", "Отклонение угла натяжения троса ключа УМК от 90°", "Совпадение частоты пульсаций генератора с частотой вышки"],
        key="p_type_2_key"
    )
    
    if p_type_2 == "Нет пакета данных MWD / Падение давления на тесте":
        st.error("Следствие: Срыв этапа наземной проверки КНБК на мостках.")
        st.info("Действие: Контроль сигнала. Поворот КНБК на 90 и 180 градусов.")
        ans = st.radio("Каротаж стабилен?", ["Не выбрано", "Да", "Нет"], key="t2_r1")
        if ans == "Да":
            res = "СПУСК РАЗРЕШЕН. Параметры ТМС в норме."
            st.success(res)
            report_text = "ПРОТОКОЛ ОСЛОЖНЕНИЙ\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res
        if ans == "Нет":
            res = "СТОП! Подъем MWD для ревизии модулей телеметрии."
            st.error(res)
            report_text = "ПРОТОКОЛ ОСЛОЖНЕНИЙ\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res

    if p_type_2 == "Отклонение угла натяжения троса ключа УМК от 90°":
        st.error("Следствие: Скрытый недотяг / перетяг резьбы. Риск аварийного свинчивания КНБК.")
        st.info("Действие: Остановить затяжку. Замерить плечо L. Выставить угол максимально близко к 90°.")
        st.warning("💡 Используйте модуль «Расчет УМК» в левом боковом меню!")
        ans = st.radio("Момент с поправкой на угол соответствует требованиям?", ["Не выбрано", "Да", "Нет"], key="t2_r2")
        if ans == "Да":
            res = "КНБК готова к спуску! Запись в вахтовый журнал."
            st.success(res)
            report_text = "ПРОТОКОЛ УМК\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res
        if ans == "Нет":
            res = "СТОП! Перезатяжка резьбового соединения, повторная выверка угла."
            st.error(res)
            report_text = "ПРОТОКОЛ УМК\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res

    if p_type_2 == "Совпадение частоты пульсаций генератора с частотой вышки":
        st.error("Следствие: Резонанс буровой вышки: опасная вибрация.")
        st.info("Действие: Снизить расход буровых насосов по минимуму.")
        ans = st.radio("Раскачивание металлоконструкций вышки прекратилось?", ["Не выбрано", "Да", "Нет"], key="t2_r3")
        if ans == "Да":
            res = "Тест на пониженном расходе. Безопасный режим работы."
            st.success(res)
            report_text = "ПРОТОКОЛ РЕЗОНАНСА\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res
        if ans == "Нет":
            res = "СТОП НАСОСЫ! Устранение резонанса силами буровой бригады."
            st.error(res)
            report_text = "ПРОТОКОЛ РЕЗОНАНСА\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res

with tab3:
    st.subheader("📋 Чек-лист обязательных требований")
    st.markdown("### 1. Проверка моментомера УМК")
    umk_docs = st.radio("В наличии паспорт и сведения о калибровке на моментомер ключа УМК?", ["Не выбрано", "Да", "Нет"], key="pdf_r1")
    if umk_docs == "Да":
        res = "Разрешено использование ключа."
        st.success(res)
        report_text = "ЧЕК-ЛИСТ УМК\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res
    if umk_docs == "Нет":
        res = "КРИТИЧЕСКИЙ РИСК! Составить Акт о несоответствии."
        st.error(res)
        report_text = "ЧЕК-ЛИСТ УМК\n" + "Дата: " + current_time + "\nОбъект: " + well_number + "\nИтог: " + res

if report_text != "":
    st.markdown("---")
    st.subheader("📥 Экспорт результатов проверки")
    with st.expander("👀 Посмотреть предпросмотр протокола"):
        st.code(report_text, language="text")
    st.download_button(
        label="💾 Скачать отчет (.TXT)",
        data=report_text,
        file_name=f"Протокол_КНБК.txt",
        mime="text/plain"
    )
