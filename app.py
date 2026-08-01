import streamlit as st

# 1. НАСТРОЙКА СТРАНИЦЫ
st.set_page_config(page_title="Помощник инженера «Траектория-Сервис»", page_icon="🧭", layout="wide")

# 2. CSS ДЛЯ МЕНЮ (Стилизация)
st.markdown("<style>div[data-testid='stSidebarNavItems'] a span { font-size: 0 !important; } ...</style>", unsafe_allow_html=True) # Полный стиль в источнике [1]

# 3. АВТОРИЗАЦИЯ
def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    st.title("🔐 Авторизация в системе ННБ")
    # ... (логика авторизации в источнике [1])
    if st.button("Войти"):
        # ... (проверка в источнике [1])
        pass
    return False

# 4. ОСНОВНОЙ ИНТЕРФЕЙС
if check_password():
    if st.sidebar.button("🔒 Выйти"):
        st.session_state["authenticated"] = False
        st.rerun()

    st.title("🧭 Цифровой помощник инженера")
    # ... (код отрисовки колонок col1-col6 с описанием модулей в источнике [1])

    # Корпоративный футер
    st.markdown("<div style='text-align: center; ...'>© 2026 Траектория-Сервис</div>", unsafe_allow_html=True)
