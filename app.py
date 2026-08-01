import streamlit as st

# Конфигурация и авторизация (безопасно через secrets)
st.set_page_config(page_title="Помощник инженера", layout="wide")

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True

    st.title("🔐 Авторизация")
    input_user = st.text_input("Username:")
    input_pass = st.text_input("Password:", type="password")
    if st.button("Войти"):
        # Простая проверка через secrets
        if input_user in st.secrets["credentials"]["usernames"]:
            st.session_state["authenticated"] = True
            st.rerun()
    return False

# Навигация (safe way, без HTML)
if check_password():
    if st.sidebar.button("🔒 Выйти"):
        st.session_state["authenticated"] = False
        st.rerun()

    # Укажите точные пути к файлам в папке pages/
    pg = st.navigation([
        st.Page("app.py", title="Главная", icon="🧭"),
        st.Page("pages/1_vhodnoy_kontrol.py", title="1. Входной контроль", icon="📋"),
        st.Page("pages/2_raschet_umk.py", title="2. Расчет УМК", icon="🧮"),
        st.Page("pages/3_tech_cards.py", title="3. Тех карты", icon="🔨"),
        st.Page("pages/4_lyuft_vzd.py", title="4. Люфт ВЗД", icon="📏"),
        st.Page("pages/_kontrol_rastvora.py", title="5. Раствор", icon="🧪"),
        st.Page("pages/6_baza_znaniy.py", title="6. База", icon="📚")
    ])
    pg.run()
