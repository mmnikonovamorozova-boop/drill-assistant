import streamlit as st

# 1. Настройка страницы (Конфигурация для браузера)
st.set_page_config(
    page_title="6. База знаний",
    page_icon="📚",
    layout="wide"
)

# 2. ПРИНУДИТЕЛЬНЫЙ ПЕРЕХВАТ СТИЛЕЙ МЕНЮ (чтобы оно не слетало на латиницу)
st.markdown("<style>a[href*='vhodnoy_kontrol'] span, a[href*='raschet_umk'] span, a[href*='tech_cards'] span, a[href*='lyuft_vzd'] span, a[href*='kontrol_rastvora'] span, a[href*='baza_znaniy'] span, a[href='/'] span { font-size: 0 !important; } a[href='/'] span::before { content: '🧭 Главная страница'; font-size: 14px !important; font-weight: bold; } a[href*='vhodnoy_kontrol'] span::before { content: '📋 1. Входной контроль'; font-size: 14px !important; } a[href*='raschet_umk'] span::before { content: '🧮 2. Расчет УМК'; font-size: 14px !important; } a[href*='tech_cards'] span::before { content: '🔨 3. Технологические карты'; font-size: 14px !important; } a[href*='lyuft_vzd'] span::before { content: '📏 4. Люфт ВЗД'; font-size: 14px !important; } a[href*='kontrol_rastvora'] span::before { content: '🧪 5. Контроль раствора'; font-size: 14px !important; } a[href*='baza_znaniy'] span::before { content: '📚 6. База знаний'; font-size: 14px !important; }</style>", unsafe_allow_html=True)

# 3. ПРОВЕРКА АВТОРИЗАЦИИ ИНЖЕНЕРА
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пожалуйста, пройдите авторизацию на Главной странице приложения.")
    st.stop()

# 4. КОНТЕНТ СТРАНИЦЫ БАЗЫ ЗНАНИЙ
st.title("📚 Центральная база нормативно-технической документации")
st.caption("Единый реестр стандартов ИНТИ и регламентов ООО «Траектория-Сервис»")
st.markdown("---")

st.write("Приветствую, {}. Ниже представлены актуальные производственные инструкции и стандарты, регламентирующие работу инженера по ННБ на устье скважины.".format(st.session_state.get("username", "Коллега")))

# Сетка категорий документов
col_inti, col_corp = st.columns(2)

with col_inti:
    st.subheader("🌐 Отраслевые стандарты ИНТИ")
    st.markdown("---")
    
    # Кнопка скачивания СТО ИНТИ S.100.3
    try:
        with open("docs/inti_s100.pdf", "rb") as file_inti:
            st.download_button(
                label="📥 Скачать СТО ИНТИ S.100.3 (Сборка и ВИК КНБК)",
                data=file_inti,
                file_name="STO_INTI_S100_3.pdf",
                mime="application/pdf"
            )
    except FileNotFoundError:
        st.info("📑 Документ СТО ИНТИ S.100.3 станет доступен для скачивания, как только вы загрузите файл в папку docs/inti_s100.pdf на GitHub.")

    # Место для второго документа ИНТИ (например, по качеству)
    st.write("• **СТО ИНТИ S.QS.7** — Системы менеджмента качества (доступно на устье)")
    st.write("• **СТО ИНТИ S.QS.8** — Требования к метрологическому обеспечению оборудования")

with col_corp:
    st.subheader("🏢 Корпоративные регламенты и РД")
    st.markdown("---")
    
    # Кнопка скачивания Инструкции по УМК
    try:
        with open("docs/инструкция_умк.pdf", "rb") as file_umk:
            st.download_button(
                label="📥 Скачать Инструкцию по креплению резьбовых соединений ключами УМК",
                data=file_umk,
                file_name="Instrukciya_UMK.pdf",
                mime="application/pdf"
            )
    except FileNotFoundError:
        st.info("📑 Инструкция по ключам УМК станет доступна для скачивания, как только вы загрузите файл в папку docs/инструкция_умк.pdf на GitHub.")

    st.write("• **РД-01-2026** — Инструкция по входному контролю долотных элементов")
    st.write("• **РД-02-2026** — Методика замера осевых люфтов шпинделя ВЗД")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'>Отдел систем менеджмента качества (ОСМК) • ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
