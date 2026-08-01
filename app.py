import streamlit as st

# 1. Настройка страницы (ДОЛЖНА БЫТЬ ПЕРВОЙ)
st.set_page_config(
    page_title="Помощник инженера «Траектория-Сервис»",
    page_icon="🧭",
    layout="wide"
)

# 2. ФУНКЦИЯ АВТОРИЗАЦИИ Персонала
def check_password():
    """Возвращает True, если пользователь ввел правильный логин и пароль."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Если уже авторизован, просто пропускаем
    if st.session_state["authenticated"]:
        return True

    # Форма ввода логина и пароля на экране
    st.title("🔐 Авторизация в системе ННБ")
    st.caption("ООО «Траектория-Сервис» • Защищенный корпоративный доступ")
    
    input_user = st.text_input("Введите логин (Username):")
    input_pass = st.text_input("Введите пароль (Password):", type="password")
    
    if st.button("Войти в систему"):
        # Извлекаем списки разрешенных пользователей из Secrets
        allowed_users = st.secrets["credentials"]["usernames"]
        allowed_passwords = st.secrets["credentials"]["passwords"]
        
        # Проверяем, есть ли такой логин и соответствует ли ему пароль
        if input_user in allowed_users:
            user_index = allowed_users.index(input_user)
            if input_pass == allowed_passwords[user_index]:
                st.session_state["authenticated"] = True
                st.success("🎉 Авторизация успешна! Перенаправление...")
                st.rerun() # Мгновенно перезагружаем страницу бурового ассистента
                return True
                
        st.error("❌ Неверный логин или пароль. Доступ заблокирован.")
        return False

# 3. ПРОВЕРКА ДОСТУПА
# Если функция возвращает False, код ниже (меню и контент) вообще не запустится
if check_password():

    # Кнопка "Выйти из системы" в самом низу бокового меню
    if st.sidebar.button("🔒 Выйти из аккаунта"):
        st.session_state["authenticated"] = False
        st.rerun()

    # --- ЗДЕСЬ ИДЕТ ВЕСЬ ВАШ ОСТАЛЬНОЙ РАБОЧИЙ КОД ИЗ APP.PY ---
    # CSS для меню
    st.markdown("""
    <style>
    a[href*="vhodnoy_kontrol"] span, a[href*="raschet_umk"] span, a[href*="tech_cards"] span,
    a[href*="lyuft_vzd"] span, a[href*="kontrol_rastvora"] span, a[href="/"] span { font-size: 0 !important; }
    a[href="/"] span::before { content: "🧭 Главная страница"; font-size: 14px !important; font-weight: bold; }
    a[href*="vhodnoy_kontrol"] span::before { content: "📋 1. Входной контроль"; font-size: 14px !important; }
    a[href*="raschet_umk"] span::before { content: "🧮 2. Расчет УМК"; font-size: 14px !important; }
    a[href*="tech_cards"] span::before { content: "🔨 3. Технологические карты"; font-size: 14px !important; }
    a[href*="lyuft_vzd"] span::before { content: "📏 4. Люфт ВЗД"; font-size: 14px !important; }
    a[href*="kontrol_rastvora"] span::before { content: "🧪 5. Контроль раствора"; font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🧭 Цифровой помощник инженера по ННБ")
    st.write("Добро пожаловать в единую экосистему для верификации оборудования, входного контроля и технологических расчетов.")
    st.markdown("---")

    # Сетка модулей
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

    col4, col5, col_empty = st.columns(3)
    with col4:
        st.subheader("📏 4. Люфт ВЗД")
        st.write("Комплексный расчет осевого износа опор шпиндельной секции ВЗД.")
    with col5:
        st.subheader("🧪 5. Контроль раствора")
        st.write("Мониторинг параметров бурового раствора и гидравлического оборудования.")

    st.markdown("---")
    st.info("👉 Выберите интересующий вас рабочий модуль в левом боковом меню приложения для начала инженерных расчетов!")
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'><b>Разработчик цифровой экосистемы:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ • Цифровая экосистема ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
