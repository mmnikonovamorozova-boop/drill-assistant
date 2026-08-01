import streamlit as st

# 1. Настройка конфигурации
st.set_page_config(page_title="Помощник ННБ", page_icon="🧭", layout="wide")

# 2. Стилизация бокового меню
st.markdown("""
<style>
[data-testid="stSidebarNav"] a span { font-size: 0 !important; }
[data-testid="stSidebarNav"] a[href="/"] span::before { content: "🧭 Главная"; font-size: 14px !important; font-weight: bold; }
/* Добавьте аналогичные блоки для других модулей при необходимости */
</style>
""", unsafe_allow_html=True)

# 3. Функция авторизации
def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    
    st.title("🔐 Авторизация: Траектория-Сервис")
    input_user = st.text_input("Username:")
    input_pass = st.text_input("Password:", type="password")
    if st.button("Войти"):
        # Замените логику проверки на использование st.secrets
        if input_user == "admin" and input_pass == "123":
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("❌ Ошибка доступа")
    return False

# 4. Основной контент
if check_password():
    if st.sidebar.button("🔒 Выйти"): st.session_state["authenticated"] = False; st.rerun()
    st.title("🧭 Цифровой помощник инженера")
    st.markdown("---")
    
    # 6 модулей (отображение сеткой)
    cols = st.columns(3)
    modules = [
        ("📋 1. Входной контроль", "Приемка долот, ВЗД"),
        ("🧮 2. Расчет УМК", "Моменты свинчивания"),
        ("🔨 3. Техкарты", "Дефекты КНБК"),
        ("📏 4. Люфт ВЗД", "Износ опор ВЗД"),
        ("🧪 5. Контроль раствора", "Параметры раствора"),
        ("📚 6. База знаний", "Документация")
    ]
    for i, (title, desc) in enumerate(modules):
        with cols[i % 3]:
            st.subheader(title)
            st.write(desc)

    st.markdown("---")
    st.info("👉 Выберите модуль в боковом меню.")
    st.markdown("<div style='text-align:center; color:gray; font-size:11px;'>Траектория-Сервис © 2026</div>", unsafe_allow_html=True)
