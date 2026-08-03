import streamlit as st
import requests
import io
from pdf2image import convert_from_bytes

# 1. Настройка страницы
st.set_page_config(page_title="6. База знаний", page_icon="📚", layout="wide")

# 2. ПРОВЕРКА АВТОРИЗАЦИИ
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пожалуйста, пройдите авторизацию на Главной странице.")
    st.stop()

# Проверка токена в Secrets
if "YANDEX_TOKEN" not in st.secrets:
    st.error("🚨 Ошибка безопасности: Не настроен ключ доступа к хранилищу.")
    st.stop()

TOKEN = st.secrets["YANDEX_TOKEN"]
HEADERS = {"Authorization": f"OAuth {TOKEN}"}
BASE_URL = "https://yandex.net"
ROOT_DIR = "disk:/drill_docs"

st.title("📚 Центральная база нормативно-технической документации")
st.caption("Документы защищены от копирования и скачивания. Доступен только просмотр.")
st.markdown("---")

# Функция получения структуры папок из Яндекс Диска
@st.cache_data(ttl=600)  # Кэшируем структуру на 10 минут
def get_yandex_structure(path):
    try:
        res = requests.get(f"{BASE_URL}?path={path}", headers=HEADERS)
        if res.status_code == 200:
            return res.json().get("_embedded", {}).get("items", [])
        return []
    except Exception:
        return []

# Функция скачивания файла в оперативную память сервера
def download_yandex_file(file_path):
    try:
        res = requests.get(f"{BASE_URL}/download?path={file_path}", headers=HEADERS)
        if res.status_code == 200:
            download_url = res.json().get("href")
            file_res = requests.get(download_url)
            if file_res.status_code == 200:
                return file_res.content
        return None
    except Exception:
        return None

# Собираем блоки (папки)
folders = [f for f in get_yandex_structure(ROOT_DIR) if f["type"] == "dir"]

if not folders:
    st.warning("⚠️ База знаний пуста. Создайте папки внутри `drill_docs` на Яндекс Диске.")
else:
    # Создаем вкладки по именам папок (блоки)
    tab_names = [f["name"].replace("_", " ") for f in folders]
    tabs = st.tabs(tab_names)

    for tab, folder in zip(tabs, folders):
        with tab:
            # Получаем список файлов внутри блока
            files = [file for file in get_yandex_structure(folder["path"]) if file["type"] == "file" and file["name"].lower().endswith('.pdf')]
            file_names = [f["name"] for f in files]
            
            selected_file_name = st.selectbox(
                "💬 Выберите нормативный документ для просмотра:", 
                ["Пожалуйста, выберите документ..."] + file_names, 
                key=f"sel_{folder['name']}"
            )

            if selected_file_name != "Пожалуйста, выберите документ...":
                selected_file_obj = next(f for f in files if f["name"] == selected_file_name)
                
                with st.spinner("🔒 Безопасная загрузка документа..."):
                    pdf_bytes = download_yandex_file(selected_file_obj["path"])
                    
                    if pdf_bytes:
                        try:
                            images = convert_from_bytes(pdf_bytes, dpi=120)
                            st.info(f"📖 Отображается страниц: {len(images)}. Скачивание оригинального файла заблокировано.")
                            
                            for i, page in enumerate(images):
                                img_byte_arr = io.BytesIO()
                                page.save(img_byte_arr, format='JPEG')
                                st.image(img_byte_arr.getvalue(), use_container_width=True, caption=f"Страница {i+1}")
                        except Exception as e:
                            st.error("🚨 Не удалось обработать структуру документа. Убедитесь, что PDF не поврежден.")
                    else:
                        st.error("🚨 Не удалось безопасно получить файл из облака.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px;'>ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
