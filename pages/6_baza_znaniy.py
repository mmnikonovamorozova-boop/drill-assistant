import streamlit as st
import base64
import os

# 1. Настройка страницы
st.set_page_config(page_title="6. База знаний", page_icon="📚", layout="wide")

# 2. ПРОВЕРКА АВТОРИЗАЦИИ (Пример)
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пройдите авторизацию на Главной странице.")
    st.stop()

# 3. КОНТЕНТ СТРАНИЦЫ
st.title("📚 Центральная база нормативно-технической документации")
st.markdown("---")

DOCS_DIR = "docs"

# Функция для отображения PDF
def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Функция для сканирования структуры папок
def get_knowledge_base(base_dir):
    structure = {}
    if not os.path.exists(base_dir): return structure
    for folder in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
            if files: structure[folder] = sorted(files)
    return structure

# Получение данных и создание интерфейса
kb_data = get_knowledge_base(DOCS_DIR)
if not kb_data:
    st.warning("⚠️ Папка `docs/` пуста или не найдена.")
else:
    tab_names = [folder.replace("_", " ") for folder in kb_data.keys()]
    tabs = st.tabs(tab_names)

    for tab, (folder_name, files) in zip(tabs, kb_data.items()):
        with tab:
            selected_file = st.selectbox("📄 Выберите документ:", ["..."] + files, key=f"sel_{folder_name}")
            if selected_file != "...":
                display_pdf(os.path.join(DOCS_DIR, folder_name, selected_file))

st.markdown("---")
