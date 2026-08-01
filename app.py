import streamlit as st

# 1. Настройка страницы
st.set_page_config(page_title="Помощник инженера «Траектория-Сервис»", page_icon="🧭", layout="wide")

# 2. ИСПРАВЛЕНИЕ МЕНЮ (CSS)
st.markdown("""
<style>
/* Скрываем латинский текст, подставляем русский с эмодзи */
a[href="/"] span::before { content: "🧭 Главная"; font-size: 14px !important; font-weight: bold; }
a[href*="vhodnoy_kontrol"] span::before { content: "📋 1. Входной контроль"; font-size: 14px !important; }
/* ... (остальные пункты) ... */
</style>
""", unsafe_allow_html=True)

# 3. ФУНКЦИЯ АВТОРИЗАЦИИ
def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    st.title("🔐 Авторизация")
    # ... (логика ввода пароля через st.secrets)
    return False

# 4. КОНТЕНТ
if check_password():
    st.title("🧭 Цифровой помощник")
    # ... (остальной контент)
