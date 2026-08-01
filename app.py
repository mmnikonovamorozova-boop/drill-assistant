import streamlit as st

# Конфигурация и авторизация (с использованием secrets)
st.set_page_config(page_title="Помощник инженера «Траектория-Сервис»", page_icon="🧭", layout="wide")

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    st.title("🔐 Авторизация в системе ННБ")
    input_user = st.text_input("Username:")
    input_pass = st.text_input("Password:", type="password")
    if st.button("Войти") and input_user in st.secrets["credentials"]["usernames"]:
        user_index = st.secrets["credentials"]["usernames"].index(input_user)
        if input_pass == st.secrets["credentials"]["passwords"][user_index]:
            st.session_state["authenticated"] = True
            st.rerun()
    st.error("❌ Неверный логин или пароль")
    return False

if check_password():
    # Штатная навигация (вместо CSS-инъекций)
    pg = st.navigation([
        st.Page("app.py", title="Главная", icon="🧭"),
        st.Page("pages/1_vhodnoy_kontrol.py", title="1. Входной контроль", icon="📋"),
        st.Page("pages/2_raschet_umk.py", title="2. Расчет УМК", icon="🧮"),
        st.Page("pages/3_tech_cards.py", title="3. Технологические карты", icon="🔨"),
        st.Page("pages/4_lyuft_vzd.py", title="4. Люфт ВЗД", icon="📏"),
        st.Page("pages/_kontrol_rastvora.py", title="5. Контроль раствора", icon="🧪"),
        st.Page("pages/6_baza_znaniy.py", title="6. База знаний", icon="📚")
    ])
    
    if st.sidebar.button("🔒 Выйти"):
        st.session_state["authenticated"] = False
        st.rerun()
        
    pg.run()

    # Главная страница (исправлен синтаксис col4, col5, col6)
    if pg.title == "Главная":
        st.title("🧭 Цифровой помощник инженера")
        c1, c2, c3 = st.columns(3)
        # ... (здесь размещается UI-контент) ...
        c4, c5, c6 = st.columns(3) # Исправлено
