import streamlit as st

# 1. Настройка страницы
st.set_page_config(page_title="Помощник инженера «Траектория-Сервис»", page_icon="🧭", layout="wide")

# 2. Функция авторизации
def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    st.title("🔐 Авторизация в системе ННБ"); st.caption("ООО «Траектория-Сервис»")
    input_user = st.text_input("Username:"); input_pass = st.text_input("Password:", type="password")
    if st.button("Войти"):
        if input_user in st.secrets["credentials"]["usernames"] and input_pass == st.secrets["credentials"]["passwords"][st.secrets["credentials"]["usernames"].index(input_user)]:
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("❌ Неверный логин или пароль.")
    return False

# 3. Навигация и вывод страниц
if check_password():
    pg = st.navigation([
        st.Page("app.py", title="Главная страница", icon="🧭"),
        st.Page("pages/1_vhodnoy_kontrol.py", title="1. Входной контроль", icon="📋"),
        st.Page("pages/2_raschet_umk.py", title="2. Расчет УМК", icon="🧮"),
        st.Page("pages/3_tech_cards.py", title="3. Технологические карты", icon="🔨"),
        st.Page("pages/4_lyuft_vzd.py", title="4. Люфт ВЗД", icon="📏"),
        st.Page("pages/_kontrol_rastvora.py", title="5. Контроль раствора", icon="🧪"),
        st.Page("pages/6_baza_znaniy.py", title="6. База знаний", icon="📚")
    ])
    
    # Исправленное меню с уникальным ключом
    with st.sidebar:
        st.markdown("---")
        if st.button("🔒 Выйти из аккаунта", key="sidebar_logout_unique_key"):
            st.session_state["authenticated"] = False
            st.rerun()
    pg.run()

    # Главная страница (отображается, если не выбрана другая)
    if pg.title == "Главная страница":
        st.title("🧭 Цифровой помощник инженера по ННБ")
        st.write("Добро пожаловать в единую экосистему...")
        st.markdown("---")
        # [Далее идут col1-col5 с описанием модулей, полный код — в GitHub-репозитории]
        st.info("👉 Выберите модуль в левом меню!")
