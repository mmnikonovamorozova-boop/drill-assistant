import streamlit as st
import requests
import io
import urllib.parse
from pdf2image import convert_from_bytes

# 1. Настройка страницы
st.set_page_config(page_title="6. База знаний", page_icon="📚", layout="wide")

# 2. ПРОВЕРКА АВТОРИЗАЦИИ
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пожалуйста, пройдите авторизацию на Главной странице.")
    st.stop()

# СЮДА ВСТАВЬТЕ ВАШИ ССЫЛКИ НА ПАПКИ С ЯНДЕКС ДИСКА:
BLOCKS = {
    "1 Стандарты ИНТИ": "https://yandex.ru",
    "2 Инструкции и Регламенты": "https://yandex.ru",
    "3 Руководство по бурению": "https://yandex.ru"
}

BASE_PUBLIC_URL = "https://yandex.net"

st.title("📚 Центральная база нормативно-технической документации")
st.caption("Документы защищены от копирования и скачивания. Доступен только просмотр.")
st.markdown("---")

# Функция получения файлов из публичной папки Яндекса
def get_public_folder_files(public_key):
    try:
        enc_key = urllib.parse.quote(public_key)
        res = requests.get(f"{BASE_PUBLIC_URL}?public_key={enc_key}&limit=100")
        if res.status_code == 200:
            items = res.json().get("_embedded", {}).get("items", [])
            return [i for i in items if i["type"] == "file" and i["name"].lower().endswith('.pdf')]
        return []
    except Exception:
        return []

# Функция безопасного скачивания файла в память
def download_public_file(public_key, file_path):
    try:
        enc_key = urllib.parse.quote(public_key)
        enc_path = urllib.parse.quote(file_path)
        res = requests.get(f"{BASE_PUBLIC_URL}/download?public_key={enc_key}&path={enc_path}")
        if res.status_code == 200:
            download_url = res.json().get("href")
            file_res = requests.get(download_url)
            if file_res.status_code == 200:
                return file_res.content
        return None
    except Exception:
        return None

# Создаем вкладки (блоки) на основе нашего словаря BLOCKS
tabs = st.tabs(list(BLOCKS.keys()))

for tab, (block_name, public_link) in zip(tabs, BLOCKS.items()):
    with tab:
        if "ВСТАВЬТЕ_СЮДА" in public_link or not public_link:
            st.warning("⚠️ Ссылка на эту папку еще не настроена в коде GitHub.")
            continue
            
        with st.spinner("Загрузка списка документов..."):
            files = get_public_folder_files(public_link)
        
        if not files:
            st.info("📂 В этом разделе пока нет PDF-документов или ссылка неверна.")
        else:
            file_names = [f["name"] for f in files]
            selected_file_name = st.selectbox(
                "💬 Выберите нормативный документ для просмотра:", 
                ["Пожалуйста, выберите документ..."] + file_names, 
                key=f"sel_{block_name}"
            )

                   if selected_file_name != "Пожалуйста, выберите документ...":
            selected_file_obj = next((f for f in files if f["name"] == selected_file_name), None)
            
            if selected_file_obj:
                with st.spinner("🔒 Безопасная загрузка страниц..."):
                    pdf_bytes = download_public_file(public_link, selected_file_obj["path"])
                    
                    if pdf_bytes:
                        try:
                            images = convert_from_bytes(pdf_bytes, dpi=110)
                            st.info(f"📖 Отображается страниц: {len(images)}. Скачивание файла заблокировано.")
                            
                            for i, page in enumerate(images):
                                img_byte_arr = io.BytesIO()
                                page.save(img_byte_arr, format='JPEG')
                                st.image(img_byte_arr.getvalue(), use_container_width=True, caption=f"Страница {i+1}")
                        except Exception:
                            st.error("🚨 Не удалось обработать структуру документа. Убедитесь, что PDF не поврежден.")
                    else:
                        st.error("🚨 Не удалось безопасно получить файл из облака.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'>ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
