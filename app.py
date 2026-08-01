import streamlit as st

# 1. Настройка страницы
st.set_page_config(page_title="Помощник инженера «Траектория-Сервис»", page_icon="🧭", layout="wide")

# 2. Функция авторизации
def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    st.title("🔐 Авторизация")
    input_user = st.text_input("Username:")
    input_pass = st.text_input("Password:", type="password")
    if st.button("Войти"):
        if input_user in st.secrets["credentials"]["usernames"] and input_pass == st.secrets["credentials"]["passwords"][st.secrets["credentials"]["usernames"].index(input_user)]:
            st.session_state["authenticated"] = True
            st.rerun()
    return False

# 3. Навигация
if check_password():
    if st.sidebar.button("🔒 Выйти", key="btn_logout"):
        st.session_state["authenticated"] = False
        st.rerun()

    # Фиксированная навигация
    pg = st.navigation([
        st.Page("app.py", title="🧭 Главная"),
        st.Page("pages/1_vhodnoy_kontrol.py", title="📋 1. Входной контроль"),
        st.Page("pages/2_raschet_umk.py", title="🧮 2. Расчет УМК"),
        st.Page("pages/3_tech_cards.py", title="🔨 3. Тех карты"),
        st.Page("pages/4_lyuft_vzd.py", title="📏 4. Люфт ВЗД"),
        st.Page("pages/_kontrol_rastvora.py", title="🧪 5. Контроль раствора"),
        st.Page("pages/6_baza_znaniy.py", title="📚 6. База знаний")
    ])
    pg.run()

    if pg.title == "🧭 Главная":
        st.title("🧭 Цифровой помощник")
        st.info("Выберите модуль в меню")
