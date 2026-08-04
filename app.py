import streamlit as st
import os

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

# 3. НАВИГАЦИЯ С АВТО-ПОДБОРОМ ПУТИ
if not st.session_state.authenticated:
    login_screen()
else:
    if st.sidebar.button("🚪 Выйти"):
        st.session_state.authenticated = False
        st.rerun()
    
    # Автоматическое определение префикса папки
    prefix = "pages/" if os.path.exists("pages/vhodnoy_kontrol.py") else ""
    
    pg = st.navigation([
        st.Page(f"{prefix}1_vhodnoy_kontrol.py", title="Входной контроль"),
        st.Page(f"{prefix}2_raschet_umk.py", title="Расчет УМК"),
        st.Page(f"{prefix}3_tech_cards.py", title="Техкарты"),
        st.Page(f"{prefix}4_lyuft_vzd.py", title="Люфты ВЗД"),
        st.Page(f"{prefix}5_kontrol_rastvora.py", title="Контроль раствора"),
        st.Page(f"{prefix}6_baza_znaniy.py", title="База знаний"),
        st.Page(f"{prefix}7_prognoz_traektorii.py", title="Прогноз траектории"),
    ])
    pg.run()
