import streamlit as st

# 1. Настройка страницы (ДОЛЖНА БЫТЬ ПЕРВОЙ Командой)
st.set_page_config(
    page_title="Помощник инженера «Траектория-Сервис»",
    page_icon="🧭",
    layout="wide"
)

# 2. Функция авторизации персонала через Secrets
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True

    st.title("🔐 Авторизация в системе ННБ")
    st.caption("ООО «Траектория-Сервис» • Защищенный корпоративный доступ")
    
    input_user = st.text_input("Username:")
    input_pass = st.text_input("Password:", type="password")
    
    if st.button("Войти"):
        # Проверка логина/пароля через st.secrets
        if input_user in st.secrets["credentials"]["usernames"] and \
           input_pass == st.secrets["credentials"]["passwords"][st.secrets["credentials"]["usernames"].index(input_user)]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ Неверный логин или пароль.")
    return False

# 3. Навигация
if check_password():
    # Объявляем страницы (убедитесь, что файлы существуют)
    pages = [
        st.Page("app.py", title="Главная", icon="🧭"),
        st.Page("pages/1_vhodnoy_kontrol.py", title="Входной контроль", icon="📋"),
        # ... остальные страницы ...
    ]
    
    pg = st.navigation(pages)
    pg.run() # Ключевой метод

    # Размещаем кнопку выхода в сайдбаре БЕЗ конфликтов
    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Выйти", key="logout"):
        st.session_state["authenticated"] = False
        st.rerun()

    # 4. Содержимое главной страницы
    if pg.title == "Главная":
        st.title("🧭 Цифровой помощник")
        # ... ваш контент ...
