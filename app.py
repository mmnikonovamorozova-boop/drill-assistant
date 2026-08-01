import streamlit as st

# 1. НАСТРОЙКА СТРАНИЦЫ
st.set_page_config(page_title="Помощник инженера «Траектория-Сервис»", page_icon="🧭", layout="wide")

# 2. ФУНКЦИЯ АВТОРИЗАЦИИ (из secrets)
def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True

    st.title("🔐 Авторизация в системе ННБ")
    input_user = st.text_input("Username:")
    input_pass = st.text_input("Password:", type="password")
    if st.button("Войти"):
        # Получение секретов из st.secrets
        allowed_users = st.secrets["credentials"]["usernames"]
        allowed_passwords = st.secrets["credentials"]["passwords"]
        if input_user in allowed_users and input_pass == allowed_passwords[allowed_users.index(input_user)]:
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("❌ Неверный логин или пароль.")
    return False

# 3. КОНТЕНТ (только если авторизован)
if check_password():
    if st.sidebar.button("🔒 Выйти"):
        st.session_state["authenticated"] = False
        st.rerun()

    # Стилизация меню (скрытие имен файлов)
    st.markdown("<style>[data-testid='stSidebarNav'] a span { font-size: 0 !important; }</style>", unsafe_allow_html=True)
    
    st.title("🧭 Цифровой помощник инженера")
    st.write("Добро пожаловать в систему. Используйте меню слева.")
    
    # ... (код разметки страниц, например, st.columns, с описанием)
