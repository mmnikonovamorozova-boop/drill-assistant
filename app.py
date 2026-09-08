import streamlit as st

st.set_page_config(page_title="Помощник инженера ННБ", layout="wide")

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
def login_screen():
    st.title("🔒 Вход в систему и регистрация рейса")
    st.caption("Введите корпоративные учетные данные СМК и параметры текущих работ")

    with st.container(border=True):
        st.subheader("🔑 Учетные данные")
        col_auth1, col_auth2 = st.columns(2)
        with col_auth1:
            username = st.text_input("Логин:")
        with col_auth2:
            password = st.text_input("Пароль:", type="password")

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
    vink_database = {}
    vink_database["Газпром (Газовые ДО)"] = [
        "ООО Газпром добыча Уренгой", "ООО Газпром добыча Ямбург", 
        "ООО Газпром добыча Надым", "ООО Газпром добыча Ноябрьск", 
        "ООО Газпром добыча Оренбург", "ООО Газпром добыча Астрахань", 
        "ООО Газпром добыча Иркутск", "ООО Газпром добыча Красноярск", 
        "ООО Газпром добыча Кузнецк", "ООО Газпром добыча шельф Южно-Сахалинск", 
        "ООО Газпром инвест", "ООО Газпром недра"
    ]
    vink_database["Газпром нефть"] = [
        "ООО Газпромнефть-Хантос", "ООО Газпромнефть-Ноябрьскнефтегаз", 
        "ООО Газпромнефть-Восток", "ООО Газпромнефть-Оренбург", 
        "ООО Газпромнефть-Заполярье", "ООО Газпромнефть-Ямал", 
        "ООО Газпромнефть-Развитие", "ООО Газпромнефть-Бадра", 
        "ООО Газпромнефть-Шельф", "ООО Газпромнефть-Салым", 
        "АО Мессояханефтегаз", "ООО Технологический центр Бажен"
    ]
    vink_database["Роснефть"] = [
        "ООО РН-Юганскнефтегаз", "ООО РН-Ванкор", "АО Самотлорнефтегаз", 
        "АО РОСПАН ИНТЕРНЕШНЛ", "АО Оренбургнефть", "ООО РН-Ставропольнефтегаз", 
        "АО Дагнефтегаз", "ООО РН-Северная нефть", "ООО РН-Пурнефтегаз", 
        "ООО РН-Уватнефтегаз", "АО Верхнечонскнефтегаз", "ООО Таас-Юрях Нефтегазодобыча", 
        "АО Востсибнефтегаз", "АО Самаранефтегаз", "ПАО Удмуртнефть", "ОАО НГК Славнефть"
    ]
    vink_database["ЛУКОЙЛ"] = [
        "ООО ЛУКОЙЛ-Западная Сибирь", "ООО ЛУКОЙЛ-Коми", "ООО ЛУКОЙЛ-Пермь", 
        "ООО ЛУКОЙЛ-Нижневолжскнефть", "ООО ЛУКОЙЛ-Калининградморнефть", "АО РИТЭК"
    ]
    vink_database["Татнефть"] = [
        "ПАО Татнефть", "ООО Татнефть-Самара", "ООО Татнефть-НАО", "ООО... [INDEX]"
    ]
    vink_database["Независимые компании (Выбор из списка)"] = [
        "ПАО Сургутнефтегаз", "ПАО НОВАТЭК", "ООО Арктик СПГ 2", "ООО Ямал СПГ", 
        "АО Независимая нефтегазовая компания (ННК)", "ПАО НК РуссНефть", 
        "ООО Иркутская нефтяная компания (ИНК)", "АО Зарубежнефть", "АО Нефтиса", 
        "ПАО ЯТЭК", "АО РНГ", "ООО УДС нефть"
    ]
    vink_database["Новая компания (Ввод вручную)"] = ["Ввести параметры компании вручную"]

    st.markdown("##### 🏢 Привязка к контракту Заказчика:")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        main_vink = st.selectbox("Холдинг / Оператор (ВИНК):", list(vink_database.keys()), key="main_vink_select")
        st.session_state["main_page_company"] = main_vink
    with col_v2:
        main_dor = st.selectbox("Конкретное предприятие (Заказчик):", vink_database.get(main_vink, []), key="main_dor_select")

    if main_vink == "Новая компания (Ввод вручную)":
        custom_co = st.text_input("Введите название независимого оператора:", value="АО ИНК", key="main_custom_co")
        st.session_state["shared_dor_name"] = custom_co
    else:
        st.session_state["shared_dor_name"] = main_dor
    st.markdown(" ")
    if st.button("🚀 Авторизоваться и запустить систему", use_container_width=True):
        if username == "engineer_nnb" and password == "Traektoriya 2026":
            if not engineer_name_input or not well_number_input or not field_name_input:
                st.error("🚨 ОШИБКА РЕГИСТРАЦИИ: Все поля параметров обязательны.")
            else:
                st.session_state.authenticated = True
                st.session_state["engineer_name"] = engineer_name_input
                st.session_state["well_number"] = well_number_input
                st.session_state["field_name"] = field_name_input
                st.session_state["bha_number"] = bha_number_input
                st.success("✅ Авторизация успешно завершена!")
                st.rerun()
        else:
            st.error("❌ Доступ отклонен: Неверный логин или пароль СМК.")
if not st.session_state.authenticated:
    login_screen()
else:
    st.sidebar.markdown("### 💼 Активный профиль рейса")
    st.sidebar.markdown(f"**Холдинг:** `{st.session_state.get('main_page_company', 'Роснефть')}`")
    st.sidebar.markdown(f"**Заказчик:** `{st.session_state.get('shared_dor_name', 'Не указан')}`")
    st.sidebar.markdown(f"**Инженер:** `{st.session_state['engineer_name']}`")
    st.sidebar.markdown(f"**Скважина:** `{st.session_state['well_number']}`")
    st.sidebar.markdown(f"**Месторождение:** `{st.session_state['field_name']}`")
    st.sidebar.markdown(f"**КНБК №:** `{st.session_state['bha_number']}`")
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Выйти из системы", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    список_страниц = [
    st.Page("pages/1_vhodnoy_kontrol.py", title="1. Входной контроль"),
    st.Page("pages/2_raschet_umk.py", title="2. Расчет УМК"),
    st.Page("pages/3_tech_cards.py", title="3. Техкарты"),
    st.Page("pages/8_lyuft_vzd.py", title="4. Люфт ВЗД")
]

список_страниц.extend([
    st.Page("pages/4_matrix_and_lnd.py", title="5. Матрица и ЛНД"),
    st.Page("pages/5_kontrol_rastvora.py", title="6. Контроль раствора"),
    st.Page("pages/6_baza_znaniy.py", title="7. База знаний"),
    st.Page("pages/7_prognoz_traektorii.py", title="8. Прогноз траектории"),
    st.Page("pages/1_sbor_knbk.py", title="9. Сборка КНБК")
])

st.navigation(список_страниц).run()
