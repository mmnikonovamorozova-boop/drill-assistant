import streamlit as st

# 1. НАСТРОЙКА СТРАНИЦЫ
st.set_page_config(
    page_title="Помощник инженера «Траектория-Сервис»",
    page_icon="🧭",
    layout="wide"
)

# Функция для логаута (перенаправление на нее очистит сессию)
def logout_page():
    st.session_state["authenticated"] = False
    st.success("Выход из системы успешен. Перенаправление...")
    st.rerun()

# 2. ФУНКЦИЯ АВТОРИЗАЦИИ ПЕРСОНАЛА
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.title("🔐 Авторизация в системе ННБ")
    st.caption("ООО «Траектория-Сервис» • Защищенный корпоративный доступ")
    
    input_user = st.text_input("Введите логин (Username):")
    input_pass = st.text_input("Введите пароль (Password):", type="password")
    
    if st.button("Войти в систему"):
        allowed_users = st.secrets["credentials"]["usernames"]
        allowed_passwords = st.secrets["credentials"]["passwords"]
        
        if input_user in allowed_users:
            user_index = allowed_users.index(input_user)
            if input_pass == allowed_passwords[user_index]:
                st.session_state["authenticated"] = True
                st.rerun()
                return True
                
        st.error("❌ Неверный логин или пароль. Доступ заблокирован.")
        return False

# 3. ЗАПУСК НАВИГАЦИИ ПОСЛЕ АВТОРИЗАЦИИ
if check_password():
    
    # Задаем структуру меню (строго по путям вашего репозитория)
    pages = [
        st.Page("app.py", title="Главная страница", icon="🧭"),
        st.Page("pages/1_vhodnoy_kontrol.py", title="1. Входной контроль", icon="📋"),
        st.Page("pages/2_raschet_umk.py", title="2. Расчет УМК", icon="🧮"),
        st.Page("pages/3_tech_cards.py", title="3. Технологические карты", icon="🔨"),
        st.Page("pages/4_lyuft_vzd.py", title="4. Люфт ВЗД", icon="📏"),
        st.Page("pages/_kontrol_rastvora.py", title="5. Контроль раствора", icon="🧪"),
        st.Page("pages/6_baza_znaniy.py", title="6. База знаний", icon="📚"),
        st.Page(logout_page, title="Выйти из аккаунта", icon="🔒")
    ]
    
    # Запускаем навигационный движок
    pg = st.navigation(pages)
    pg.run()

    # ВЫВОД КОНТЕНТА ДЛЯ ГЛАВНОЙ СТРАНИЦЫ
    if pg.title == "Главная страница":
        st.title("🧭 Цифровой помощник инженера по ННБ")
        st.write("Добро пожаловать в единую экосистему для верификации оборудования, входного контроля и технологических расчетов.")
        st.markdown("---")

        # Верхний ряд модулей (1, 2, 3)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("📋 1. Входной контроль")
            st.write("Сводный интерактивный чек-лист приемки долот, ВЗД и элементов КНБК.")
        with col2:
            st.subheader("🧮 2. Расчет УМК")
            st.write("Корректировка моментных характеристик свинчивания резьбовых соединений.")
        with col3:
            st.subheader("🔨 3. Технологические карты")
            st.write("Оперативное выявление скрытых дефектов сборки резьбовых соединений КНБК.")

        st.markdown("<br>", unsafe_allow_html=True)

        # Нижний ряд модулей (4, 5, 6)
        col4, col5, col6 = st.columns(3)
        with col4:
            st.subheader("📏 4. Люфт ВЗД")
            st.write("Комплексный расчет осевого износа опор шпиндельной секции ВЗД.")
        with col5:
            st.subheader("🧪 5. Контроль раствора")
            st.write("Мониторинг параметров бурового раствора и гидравлического оборудования.")
        with col6:
            st.subheader("📚 6. База знаний")
            st.write("Центральный реестр нормативной документации, стандартов ИНТИ и регламентов компании.")

        st.markdown("---")
        st.info("👉 Выберите интересующий вас рабочий модуль в левом боковом меню приложения для начала инженерных расчетов!")
        st.markdown("---")

        # Корпоративный футер
        st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'><b>Разработчик цифровой экосистемы:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ • Цифровая экосистема ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
