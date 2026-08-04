import streamlit as st

# ==============================================================================
# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИЗАЦИЯ ИНТЕРФЕЙСА
# ==============================================================================
st.set_page_config(
    page_title="Помощник инженера ННБ",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация состояния авторизации (если еще не создано)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ==============================================================================
# 2. ФУНКЦИЯ ЭКРАНА АВТОРИЗАЦИИ
# ==============================================================================
def login_screen():
    st.title("🔒 Авторизация в системе ННБ")
    st.caption("ООО «Траектория-Сервис» • Защищенный корпоративный доступ")
    
    with st.container(border=True):
        username = st.text_input("Введите логин (Username):")
        password = st.text_input("Введите пароль (Password):", type="password")
        
        if st.button("Войти в систему", type="primary"):
            # Простейшая заглушка для теста (замените на ваши реальные логины/пароли)
            if username == "admin" and password == "nnb2026":
                st.session_state.authenticated = True
                st.success("Успешный вход! Перенаправление...")
                st.rerun()
            else:
                st.error("Неверный логин или пароль. Пожалуйста, повторите ввод.")

# ==============================================================================
# 3. ОСНОВНАЯ ЛОГИКА И СИСТЕМА НАВИГАЦИИ (ДЛЯ STREAMLIT >= 1.35)
# ==============================================================================
if not st.session_state.authenticated:
    # Если пользователь не авторизован — показываем только экран входа
    login_screen()
else:
    # Кнопка выхода в боковом меню (для удобства СМК)
    if st.sidebar.button("🚪 Выйти из системы"):
        st.session_state.authenticated = False
        st.rerun()

    st.sidebar.markdown("---")

    # Объявляем список страниц (переменная 'pages'), строго соответствующий вашему меню
    # ПРИМЕЧАНИЕ: Файлы .py должны лежать в той же корневой папке репозитория
    pages = [
        st.Page("pages/vhodnoy_kontrol.py", title="Входной контроль", icon="📋"),
        st.Page("pages/raschet_umk.py", title="Расчет УМК", icon="🔧"),
        st.Page("pages/tech_cards.py", title="Техкарты", icon="📄"),
        st.Page("pages/lyuft_vzd.py", title="Люфты ВЗД", icon="⚙️"),
        st.Page("pages/kontrol_rastvora.py", title="Контроль раствора", icon="🧪"),
        st.Page("pages/baza_znaniy.py", title="База знаний", icon="📚"),
        st.Page("pages/prognoz_traektorii.py", title="Прогноз траектории", icon="📈"),
    ]


    # Инициализация и запуск навигации (строго без лишних отступов в начале строк)
    pg = st.navigation(pages)
    pg.run()
