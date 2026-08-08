import streamlit as st

# 1. КОНФИГУРАЦИЯ
st.set_page_config(page_title="Помощник инженера ННБ", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 2. АВТОРИЗАЦИЯ
def login_screen():
    st.title("🔒 Авторизация")
    username = st.text_input("Логин:")
    password = st.text_input("Пароль:", type="password")
    if st.button("Войти"):
        if username == "engineer_nnb" and password == "Traektoriya 2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Неверные данные")

# 3. НАВИГАЦИЯ С ТОЧНЫМИ ПУТЯМИ (С УЧЕТОМ ЦИФР)
if not st.session_state.authenticated:
    login_screen()
else:
    # ГЛОБАЛЬНЫЙ САЙДБАР: Паспорт рейса для всех модулей КНБК
    st.sidebar.markdown("### 📋 Паспорт рейса")
    
    st.session_state["well_number"] = st.sidebar.text_input(
        "Номер скважины / Куст:", 
        value="Скв. № 101, Куст 5",
        help="ℹ️ Используется для автоматического формирования шапки официальных актов и нарядов."
    )
    
    st.session_state["field_name"] = st.sidebar.text_input(
        "Месторождение:", 
        value="Приобское",
        help="ℹ️ Введите название текущего месторождения."
    )
    
    st.session_state["bha_number"] = st.sidebar.text_input(
        "Сборка КНБК №:", 
        value="1",
        help="ℹ️ Порядковый номер компоновки нижнего инструмента."
    )
    
    st.sidebar.markdown("---")

