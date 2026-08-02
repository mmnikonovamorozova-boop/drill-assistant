import streamlit as st
import base64

# 1. Настройка страницы
st.set_page_config(
    page_title="6. База знаний",
    page_icon="📚",
    layout="wide"
)

# 2. ПРОВЕРКА АВТОРИЗАЦИИ ИНЖЕНЕРА
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пожалуйста, пройдите авторизацию на Главной странице приложения.")
    st.stop()

# 3. КОНТЕНТ СТРАНИЦЫ БАЗЫ ЗНАНИЙ
st.title("📚 Центральная база нормативно-технической документации")
st.caption("Единый реестр стандартов ИНТИ и регламентов ООО «Траектория-Сервис»")
st.markdown("---")

# Функция для безопасного кодирования и отображения PDF внутри Streamlit
def display_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        # Создаем встроенное окно просмотра (высота 700 пикселей)
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"🚨 Файл '{file_path}' не найден в папке docs/. Проверьте точное имя файла на GitHub.")

# Выпадающий список для выбора документа
selected_doc = st.selectbox(
    "💬 Выберите нормативный документ для онлайн-просмотра на экране:",
    [
        "Пожалуйста, выберите документ из списка...",
        "СТО ИНТИ S.100.3-2024 (Инспекция и сборка КНБК)",
        "Инструкция по креплению резьбовых соединений ключами УМК"
    ]
)

st.markdown("---")

# Логика интерактивного переключения документов
if "СТО ИНТИ" in selected_doc:
    st.info("📖 Отображается: СТО ИНТИ S.100.3-2024. Вы можете читать, масштабировать и печатать документ прямо отсюда.")
    display_pdf("docs/inti_s100.pdf")

elif "Инструкция" in selected_doc:
    st.info("📖 Отображается: Инструкция по ключам УМК ООО «Траектория-Сервис».")
    display_pdf("docs/instrukciya_umk.pdf")

else:
    st.markdown("""
    <div style='color: #4B5563; font-size: 14px; background-color: #F3F4F6; padding: 20px; border-radius: 6px; text-align: center; font-family: Arial, sans-serif;'>
        <b>💡 Подсказка для инженера:</b><br><br>
        Выберите необходимый регламент или стандарт в выпадающем списке выше.<br>
        Документ откроется в интерактивном окне. Скачивание файла на устройство не требуется.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'>Отдел систем менеджмента качества (ОСМК) • ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
