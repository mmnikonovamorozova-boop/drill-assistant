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
        # Использование указанных данных
        if username == "engineer_nnb" and password == "Traektoriya 2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Неверные данные")

# 3. НАВИГАЦИЯ (исправленные пути)
if not st.session_state.authenticated:
    login_screen()
else:
    if st.sidebar.button("🚪 Выйти"):
        st.session_state.authenticated = False
        st.rerun()
    
    # Файлы лежат в корне, папка pages/ убрана
    pg = st.navigation([
        st.Page("vhodnoy_kontrol.py", title="Входной контроль"),
        st.Page("raschet_umk.py", title="Расчет УМК"),
        st.Page("tech_cards.py", title="Техкарты"),
        st.Page("lyuft_vzd.py", title="Люфты ВЗД"),
        st.Page("kontrol_rastvora.py", title="Контроль раствора"),
        st.Page("baza_znaniy.py", title="База знаний"),
        st.Page("prognoz_traektorii.py", title="Прогноз траектории"),
    ])
    pg.run()
