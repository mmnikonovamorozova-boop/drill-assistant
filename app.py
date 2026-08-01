import streamlit as st

# 1. НАСТРОЙКА СТРАНИЦЫ (ДОЛЖНА БЫТЬ ПЕРВОЙ)
st.set_page_config(
    page_title="Помощник инженера «Траектория-Сервис»",
    page_icon="🧭",
    layout="wide"
)

# 2. ИСПРАВЛЕНИЕ БОКОВОГО МЕНЮ ЧЕРЕЗ КОРНЕВОЙ CSS (Порядковое переименование строк)
st.markdown("""
<style>
/* Скрываем исходный системный текст у всех ссылок в меню */
[data-testid="stSidebarNav"] ul li a span {
    font-size: 0 !important;
}

/* Намертво вписываем русские названия по порядку строк сверху вниз */
[data-testid="stSidebarNav"] ul li:nth-child(1) a span::before {
    content: "🧭 Главная страница";
    font-size: 14px !important;
    font-weight: bold;
}
[data-testid="stSidebarNav"] ul li:nth-child(2) a span::before {
    content: "📋 1. Входной контроль";
    font-size: 14px !important;
}
[data-testid="stSidebarNav"] ul li:nth-child(3) a span::before {
    content: "🧮 2. Расчет УМК";
    font-size: 14px !important;
}
[data-testid="stSidebarNav"] ul li:nth-child(4) a span::before {
    content: "🔨 3. Технологические карты";
    font-size: 14px !important;
}
[data-testid="stSidebarNav"] ul li:nth-child(5) a span::before {
    content: "📏 4. Люфт ВЗД";
    font-size: 14px !important;
}
[data-testid="stSidebarNav"] ul li:nth-child(6) a span::before {
    content: "🧪 5. Контроль раствора";
    font-size: 14px !important;
}
[data-testid="stSidebarNav"] ul li:nth-child(7) a span::before {
    content: "📚 6. База знаний";
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)

# 3. ФУНКЦИЯ ПРОФЕССИОНАЛЬНОЙ АВТОРИЗАЦИИ ПЕРСОНАЛА
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

# 4. ВЫВОД ОСНОВНОГО ИНТЕРФЕЙСА ЭКОСИСТЕМЫ
if check_password():

    # Универсальная кнопка выхода в сайдбаре
    if st.sidebar.button("🔒 Выйти из аккаунта"):
        st.session_state["authenticated"] = False
        st.rerun()

    # Заголовок главной страницы
    st.title("🧭 Цифровой помощник инженера по ННБ")
    st.write("Добро пожаловать в единую экосистему для верификации оборудования, входного контроля и технологических расчетов.")
    st.markdown("---")

    # Сетка модулей (Верхний ряд: Колонки 1, 2, 3)
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

    # Сетка модулей (Нижний ряд: Колонки 4, 5, 6)
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
