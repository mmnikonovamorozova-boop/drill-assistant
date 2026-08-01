import streamlit as st

# 1. Задаем общую конфигурацию
st.set_page_config(
    page_title="Помощник инженера «Траектория-Сервис»",
    page_icon="🧭",
    layout="wide"
)

# 2. УЛЬТИМАТИВНОЕ ИСПРАВЛЕНИЕ БОКОВОГО МЕНЮ ЧЕРЕЗ CSS
# Находим ссылки на латинские страницы и принудительно переписываем их текст на русский с эмодзи
st.markdown("""
<style>
/* Скрываем исходный латинский текст пунктов меню */
a[href*="vhodnoy_kontrol"] span,
a[href*="raschet_umk"] span,
a[href*="tech_cards"] span,
a[href*="lyuft_vzd"] span,
a[href*="kontrol_rastvora"] span,
a[href="/"] span {
    font-size: 0 !important;
}

/* Подставляем красивый русский текст с эмодзи через свойство content */
a[href="/"] span::before {
    content: "🧭 Главная страница";
    font-size: 14px !important;
    font-weight: bold;
}
a[href*="vhodnoy_kontrol"] span::before {
    content: "📋 1. Входной контроль";
    font-size: 14px !important;
}
a[href*="raschet_umk"] span::before {
    content: "🧮 2. Расчет УМК";
    font-size: 14px !important;
}
a[href*="tech_cards"] span::before {
    content: "🔨 3. Технологические карты";
    font-size: 14px !important;
}
a[href*="lyuft_vzd"] span::before {
    content: "📏 4. Люфт ВЗД";
    font-size: 14px !important;
}
a[href*="kontrol_rastvora"] span::before {
    content: "🧪 5. Контроль раствора";
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)

# 3. КОНТЕНТ ГЛАВНОЙ СТРАНИЦЫ
st.title("🧭 Цифровой помощник инженера по ННБ")
st.write("Добро пожаловать в единую экосистему для верификации оборудования, входного контроля и технологических расчетов.")
st.markdown("---")

# Сетка модулей (Колонки 1, 2, 3)
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📋 1. Входной контроль")
    st.write("Сводный интерактивный чек-лист приемки долот, ВЗД и элементов КНБК.")

with col2:
    st.subheader("🧮 2. Расчет УМК")
    st.write("Корректировка моментных характеристик свинчивания резьбовых соединений.")

with col3:
    # Здесь иконка уже заменена на цветную 🔨 для идеального единообразия
    st.subheader("🔨 3. Технологические карты")
    st.write("Оперативное выявление скрытых дефектов сборки резьбовых соединений КНБК.")

st.markdown("<br>", unsafe_allow_html=True)

# Колонки 4, 5
col4, col5, col_empty = st.columns(3)

with col4:
    st.subheader("📏 4. Люфт ВЗД")
    st.write("Комплексный расчет осевого износа опор шпиндельной секции ВЗД.")

with col5:
    st.subheader("🧪 5. Контроль раствора")
    st.write("Мониторинг параметров бурового раствора и гидравлического оборудования.")

st.markdown("---")
st.info("👉 Выберите интересующий вас рабочий модуль в левом боковом меню приложения для начала инженерных расчетов!")
st.markdown("---")

# Сдержанный серый корпоративный футер
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'><b>Разработчик цифровой экосистемы:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ • Цифровая экосистема ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
