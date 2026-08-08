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
    # Кнопка безопасного выхода из системы
    if st.sidebar.button("🚪 Выйти из системы", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    # Навигационная структура страниц КНБК
    pg = st.navigation([
        st.Page("pages/1_vhodnoy_kontrol.py", title="Входной контроль"),
        st.Page("pages/2_raschet_umk.py", title="Расчет УМК"),
        st.Page("pages/3_tech_cards.py", title="Техкарты"),
        st.Page("pages/4_lyuft_vzd.py", title="Люфты ВЗД"),
        st.Page("pages/5_kontrol_rastvora.py", title="Контроль раствора"),
        st.Page("pages/6_baza_znaniy.py", title="База знаний"),
        st.Page("pages/7_prognoz_traektorii.py", title="Прогноз траектории"),
    ])
    pg.run()

