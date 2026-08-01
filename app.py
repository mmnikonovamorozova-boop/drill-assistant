import streamlit as st

# 1. НАСТРОЙКА СТРАНИЦЫ
st.set_page_config(page_title="Помощник инженера «Траектория-Сервис»", page_icon="🧭", layout="wide")

# 2. ИСПРАВЛЕНИЕ МЕНЮ (CSS по href)
st.markdown("""
<style>
/* Скрываем старые названия, показываем свои по href */
div[data-testid="stSidebarNavItems"] a span { font-size: 0 !important; }
div[data-testid="stSidebarNavItems"] a[href="/"] span::before { content: "🧭 Главная"; font-size: 14px !important; font-weight: bold; }
div[data-testid="stSidebarNavItems"] a[href*="vhodnoy_kontrol"] span::before { content: "📋 1. Входной контроль"; font-size: 14px !important; }
div[data-testid="stSidebarNavItems"] a[href*="tech_cards"] span::before { content: "🔨 3. Тех. карты"; font-size: 14px !important; }
/* ... аналогично для других страниц ... */
</style>
""", unsafe_allow_html=True)

# 3. АВТОРИЗАЦИЯ
def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    st.title("🔐 Авторизация")
    input_user = st.text_input("Логин:")
    input_pass = st.text_input("Пароль:", type="password")
    if st.button("Войти"):
        if input_user == "admin" and input_pass == "password": # Пример
            st.session_state["authenticated"] = True
            st.rerun()
    return False

# 4. ИНТЕРФЕЙС
if check_password():
    st.title("🧭 Цифровой помощник инженера")
    st.write("Выберите модуль в меню.")
