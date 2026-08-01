import streamlit as st

# 1. Настройка страницы
st.set_page_config(page_title="Помощник инженера", page_icon="🧭", layout="wide")

# 2. ФУНКЦИЯ АВТОРИЗАЦИИ
def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True

    st.title("🔐 Авторизация в системе")
    input_user = st.text_input("Username:")
    input_pass = st.text_input("Password:", type="password")
    
    if st.button("Войти"):
        if input_user == "admin" and input_pass == "1234": # Замените на st.secrets
            st.session_state["authenticated"] = True
            st.rerun()
    return False

# 3. НАВИГАЦИЯ И ЛОГИКА
if check_password():
    # Навигация (st.Page должен указывать на существующие файлы)
    pg = st.navigation([
        st.Page("main.py", title="Главная", icon="🧭"),
        st.Page("pages/1_vhodnoy.py", title="1. Контроль", icon="📋"),
    ])
    
    # Кнопка выхода с уникальным ключом
    if st.sidebar.button("🔒 Выйти", key="btn_logout"):
        st.session_state["authenticated"] = False
        st.rerun()
        
    pg.run()
