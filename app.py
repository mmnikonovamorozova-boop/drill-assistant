import streamlit as st

# 1. НАСТРОЙКА СТРАНИЦЫ
st.set_page_config(page_title="Помощник инженера «Траектория-Сервис»", page_icon="🧭", layout="wide")

# 2. CSS ДЛЯ КРАСИВОГО БОКОВОГО МЕНЮ (ИСПРАВЛЕНИЕ ОТОБРАЖЕНИЯ)
# Этот CSS скрывает стандартные названия и подставляет красивые имена через ::before
st.markdown("""
<style>
[data-testid="stSidebarNav"] a span { font-size: 0 !important; }
[data-testid="stSidebarNav"] a[href="/"] span::before { content: "🧭 Главная"; font-size: 14px !important; font-weight: bold; }
/* ... (аналогично для остальных 5 пунктов меню) ... */
</style>
""", unsafe_allow_html=True)

# 3. ФУНКЦИЯ АВТОРИЗАЦИИ
def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    st.title("🔐 Авторизация")
    # ... логика ввода логина/пароля ...
    return False

# 4. КОНТЕНТ (Упрощенная структура)
if check_password():
    if st.sidebar.button("🔒 Выйти"): st.session_state["authenticated"] = False; st.rerun()
    st.title("🧭 Цифровой помощник инженера")
    st.markdown("---")
    # ... отображение модулей ...
    st.info("👉 Выберите модуль в меню")
