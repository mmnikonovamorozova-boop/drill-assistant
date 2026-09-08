import streamlit as st

# ==============================================================================
# 1. ГЛОБАЛЬНАЯ КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ
# ==============================================================================
st.set_page_config(
    page_title="Помощник инженера ННБ",
    layout="wide"
)

# Инициализируем переменные сквозного шлюза в сессии, если их еще нет
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "engineer_name" not in st.session_state:
    st.session_state["engineer_name"] = ""
if "well_number" not in st.session_state:
    st.session_state["well_number"] = ""
if "field_name" not in st.session_state:
    st.session_state["field_name"] = ""
if "bha_number" not in st.session_state:
    st.session_state["bha_number"] = "1"

# ==============================================================================
# 2. ИНТЕЛЛЕКТУАЛЬНЫЙ ЭКРАН АВТОРИЗАЦИИ И РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЯ
# ==============================================================================
def login_screen():
    st.title("🔒 Вход в систему и регистрация рейса")
    st.caption("Введите корпоративные учетные данные СМК и параметры текущих работ")
    
    # Контейнер авторизации (Безопасность)
    with st.container(border=True):
        st.subheader("🔑 Учетные данные")
        col_auth1, col_auth2 = st.columns(2)
        with col_auth1:
            username = st.text_input("Логин:")
        with col_auth2:
            password = st.text_input("Пароль:", type="password")
            
    st.markdown(" ")
    
    # Контейнер регистрации (Сквозной шлюз данных для наследования модулями)
    with st.container(border=True):
        st.subheader("📋 Регистрация параметров полевой партии (СТО ИНТИ)")
        
        engineer_name_input = st.text_input("ФИО ответственного инженера по ННБ / ТМС:", value=st.session_state["engineer_name"])
        
        col_reg1, col_reg2, col_reg3 = st.columns(3)
        with col_reg1:
            well_number_input = st.text_input("Номер скважины / Кустовая площадка:", value=st.session_state["well_number"], placeholder="например, Скв. № 101, Куст 5")
        with col_reg2:
            field_name_input = st.text_input("Название месторождения:", value=st.session_state["field_name"], placeholder="например, Приобское")
        with col_reg3:
            bha_number_input = st.text_input("Порядковый номер сборки КНБК:", value=st.session_state["bha_number"])

    st.markdown(" ")
    # База данных Заказчиков бурения РФ по холдингам (Актуальность: 2026 г.)
vink_database = {
    "Роснефть": ["ООО РН-Юганскнефтегаз", "ООО РН-Ванкор", "АО Самотлорнефтегаз", "АО Верхнечонскнефтегаз", "АО Сузун", "ООО РН-Уватнефтегаз", "ООО РН-Пурнефтегаз", "АО Самаранефтегаз", "АО Оренбургнефть", "ООО Башнефть-Добыча", "ООО Таас-Юрях Нефтегазодобыча"],
    "Газпром нефть": ["ООО Газпромнефть-Хантос", "ООО Газпромнефть-Ноябрьскнефтегаз", "ООО Газпромнефть-Восток", "ООО Газпромнефть-Заполярье", "ООО Газпромнефть-Ямал", "ООО Газпромнефть-Оренбург", "ООО Мессояханефтегаз"],
    "ЛУКОЙЛ": ["ООО ЛУКОЙЛ-Западная Сибирь", "ООО ЛУКОЙЛ-Коми", "ООО ЛУКОЙЛ-ПЕРМЬ", "ООО ЛУКОЙЛ-Нижневолжскнефть", "ООО ЛУКОЙЛ-Калининградморнефть"],
    "НОВАТЕК": ["ООО НОВАТЕК-Юрхаровнефтегаз", "ООО Арктик СПГ 2", "ОАО Ямал СПГ", "ООО НОВАТЕК-Таркосаленефтегаз"],
    "Сургутнефтегаз": ["НГДУ Лянторнефть", "НГДУ Федоровскнефть", "НГДУ Быстринскнефть", "НГДУ Сургутнефть", "НГДУ Талаканнефть"],
    "Независимый оператор (Ввод вручную)": ["Ввести параметры компании вручную"]
}

st.markdown("##### 🏢 Привязка к контракту Заказчика:")
col_v1, col_v2 = st.columns(2)

with col_v1:
    main_vink = st.selectbox("Холдинг / Оператор (ВИНК):", list(vink_database.keys()), key="main_vink_select")
    st.session_state["main_page_company"] = main_vink

with col_v2:
    main_dor = st.selectbox("Конкретное предприятие (Заказчик):", vink_database[main_vink], key="main_dor_select")
    
# Если выбран ручной ввод, даем инженеру текстовое поле для новой компании
if main_vink == "Независимый оператор (Ввод вручную)":
    custom_co = st.text_input("Введите название независимого оператора:", value="АО ИНК", key="main_custom_co")
    st.session_state["shared_dor_name"] = custom_co
else:
    st.session_state["shared_dor_name"] = main_dor

    # Кнопка верификации и отправки в систему
    if st.button("🚀 Авторизоваться и запустить систему", use_container_width=True):
        if username == "engineer_nnb" and password == "Traektoriya 2026":
            if not engineer_name_input or not well_number_input or not field_name_input:
                st.error("🚨 ОШИБКА РЕГИСТРАЦИИ: Все поля параметров рейса обязательны для заполнения по регламенту Р-ТС-35.")
            else:
                # Намертво фиксируем данные в сессии для сквозного шлюза
                st.session_state.authenticated = True
                st.session_state["engineer_name"] = engineer_name_input
                st.session_state["well_number"] = well_number_input
                st.session_state["field_name"] = field_name_input
                st.session_state["bha_number"] = bha_number_input
                st.success("✅ Авторизация и регистрация параметров успешно завершены!")
                st.rerun()
        else:
            st.error("❌ Доступ отклонен: Неверный логин или пароль СМК.")

# ==============================================================================
# 3. НАВИГАЦИОННАЯ СТРУКТУРА 8 МОДУЛЕЙ И ГЛОБАЛЬНЫЙ САЙДБАР
# ==============================================================================
if not st.session_state.authenticated:
    login_screen()
else:
    # ИНФОРМАЦИОННЫЙ ИНСТРУМЕНТАЛЬНЫЙ САЙДБАР (Данные заблокированы для изменения, только чтение)
    st.sidebar.markdown("### 💼 Активный профиль рейса")
    st.sidebar.markdown(f"**Инженер:** `{st.session_state['engineer_name']}`")
    st.sidebar.markdown(f"**Скважина/Куст:** `{st.session_state['well_number']}`")
    st.sidebar.markdown(f"**Месторождение:** `{st.session_state['field_name']}`")
    st.sidebar.markdown(f"**Компоновка КНБК №:** `{st.session_state['bha_number']}`")
    st.sidebar.markdown("---")
    
    # Кнопка безопасного выхода и сброса шлюза данных
    if st.sidebar.button("🚪 Выйти из системы", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    # Сквозная навигационная структура всех 8 модулей (с учетом переименования папок и файлов)
    pg = st.navigation([
        st.Page("pages/1_vhodnoy_kontrol.py", title="1. Входной контроль"),
        st.Page("pages/2_raschet_umk.py", title="2. Расчет УМК"),
        st.Page("pages/3_tech_cards.py", title="3. Техкарты"),
        st.Page("pages/8_lyuft_vzd.py", title="4. Люфт ВЗД"),  # Автоматически подтянет твой файл со скриншота!
        st.Page("pages/4_matrix_and_lnd.py", title="5. Матрица и ЛНД"),
        st.Page("pages/5_kontrol_rastvora.py", title="6. Контроль раствора"),
        st.Page("pages/6_baza_znaniy.py", title="7. База знаний"),
        st.Page("pages/7_prognoz_traektorii.py", title="8. Прогноз траектории"),
    ])
    
    # Запуск выбранного модуля
    pg.run()
