import streamlit as st

# 1. НАСТРОЙКА СТРАНИЦЫ
st.set_page_config(
    page_title="Помощник инженера «Траектория-Сервис»",
    page_icon="🧭",
    layout="wide"
)

# Функция для логаута
def logout_page():
    st.session_state["authenticated"] = False
    st.rerun()

# 2. ФУНКЦИЯ АВТОРИЗАЦИИ ПЕРСОНАЛА
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True

    st.title("🔐 Авторизация в системе ННБ")
    st.caption("ООО «Траектория-Сервис» • Защищенный корпоративный доступ")

    input_user = st.text_input("Введите логин (Username):")
    input_pass = st.text_input("Введите пароль (Password):", type="password")

    if st.button("Войти в систему"):
        allowed_users = st.secrets["credentials"]["usernames"]
        allowed_passwords = st.secrets["credentials"]["passwords"]

        if input_user in allowed_users:
            user_index = allowed_users.index(input_user)
            if input_pass == allowed_passwords[user_index]:
                st.session_state["authenticated"] = True
                st.rerun()
            return True
        st.error("❌ Неверный логин или пароль. Доступ заблокирован.")
    return False

# 3. ЗАПУСК НАВИГАЦИИ ПОСЛЕ АВТОРИЗАЦИИ
if check_password():
        # Задаем структуру меню (Все пути проверены и синхронизированы)
        pages = [
        st.Page("main_page.py", title="Главная страница", icon="🧭"),
        st.Page("pages/1_vhodnoy_kontrol.py", title="1. Входной контроль", icon="📋"),
        st.Page("pages/2_raschet_umk.py", title="2. Расчет УМК", icon="🧮"),
        st.Page("pages/3_tech_cards.py", title="3. Технологические карты", icon="🔨"),
        st.Page("pages/4_lyuft_vzd.py", title="4. Люфт ВЗД", icon="📏"),
        st.Page("pages/5_kontrol_rastvora.py", icon="🧪"),
        st.Page("pages/6_baza_znaniy.py", title="6. База знаний", icon="📚"),
        st.Page("pages/7_prognoz_traektorii.py", title="7. Прогноз траектории", icon="🔮"),
        st.Page(logout_page, title="Выйти из аккаунта", icon="🔒")
    ]

    # Запускаем навигационный движок
pg = st.navigation(pages)
pg.run()
