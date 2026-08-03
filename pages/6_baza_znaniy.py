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
    "1 Стандарты ИНТИ": "https://disk.yandex.ru/d/rqQpRbIZndCIUg",
    "2 Инструкции и Регламенты": "https://disk.yandex.ru/d/6G47YrLJzz1Hfw",
    "3 Руководство по бурению": "https://disk.yandex.ru/d/ybfkwoSWz67ekw"
}

BASE_PUBLIC_URL = "https://cloud-api.yandex.net/v1/disk/public/resources"

st.title("📚 Центральная база нормативно-технической документации")
st.caption("Документы защищены от копирования и скачивания. Доступен только просмотр.")
st.markdown("---")

# Сдержанная техническая отметка о соответствии стандартам ИНТИ
st.markdown(
    '<div style="color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #1E3A8A; margin-bottom: 20px; line-height: 1.5; font-family: Arial, sans-serif;">'
    '<b>Верификация стандартами:</b> Данный программный модуль безопасного хранения, визуализации и актуализации нормативно-технической документации разработан в строгом соответствии с требованиями '
    '<b>СТО ИНТИ S.QS.7 (п. 7.5.3)</b> в части управления документированной информацией, обеспечения ее доступности и защиты от несанкционированного копирования '
    'и <b>СТО ИНТИ S.QS.8 (п. 4.2.4)</b> в части оперативного обеспечения персонала буровой площадки актуальными версиями регламентов и стандартов организации.'
    '</div>',
    unsafe_allow_html=True
)

# Функция получения файлов из публичной папки Яндекса
def get_public_folder_files(public_key):
    try:
        enc_key = urllib.parse.quote(public_key)
        # Добавляем параметр &path=/ для гарантированного чтения корня публичной ссылки
        res = requests.get(f"{BASE_PUBLIC_URL}?public_key={enc_key}&path=/&limit=100")
        if res.status_code == 200:
            items = res.json().get("_embedded", {}).get("items", [])
            # Делаем проверку расширения регистра-независимой через .lower()
            return [i for i in items if i["type"] == "file" and str(i["name"]).lower().endswith('.pdf')]
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
# Инициализируем выбранный блок в памяти приложения, если его еще нет
if "current_block" not in st.session_state:
    st.session_state["current_block"] = list(BLOCKS.keys())[0]

st.markdown("### 🗂 Выберите интересующий раздел базы знаний:")

# Создаем сетку из 3 больших кнопок-плиток в один ряд
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button("🏛 1. СТАНДАРТЫ ИНТИ", use_container_width=True, type="secondary" if st.session_state["current_block"] != "1 Стандарты ИНТИ" else "primary"):
        st.session_state["current_block"] = "1 Стандарты ИНТИ"
        st.rerun()

with col_btn2:
    if st.button("📜 2. ИНСТРУКЦИИ И РЕГЛАМЕНТЫ", use_container_width=True, type="secondary" if st.session_state["current_block"] != "2 Инструкции и Регламенты" else "primary"):
        st.session_state["current_block"] = "2 Инструкции и Регламенты"
        st.rerun()

with col_btn3:
    if st.button("📘 3. РУКОВОДСТВО ПО БУРЕНИЮ", use_container_width=True, type="secondary" if st.session_state["current_block"] != "3 Руководство по бурению" else "primary"):
        st.session_state["current_block"] = "3 Руководство по бурению"
        st.rerun()

st.markdown("---")

# Логика обработки документов для выбранного через кнопку раздела
active_block = st.session_state["current_block"]
public_link = BLOCKS[active_block]

st.markdown(f"#### 📂 Активный раздел: <span style='color:#1E3A8A;'>{active_block}</span>", unsafe_allow_html=True)

with st.spinner("Загрузка списка документов..."):
    files = get_public_folder_files(public_link)
    
if not files:
    st.info("📂 В этом разделе пока нет PDF-документов или ссылка неверна.")
else:
    file_names = [f["name"] for f in files]
    selected_file_name = st.selectbox(
        "💬 Выберите нормативный документ для просмотра:",
        ["Пожалуйста, выберите документ..."] + file_names,
        key=f"sel_{active_block}"
    )
    
    if selected_file_name != "Пожалуйста, выберите документ...":
        selected_file_obj = next((f for f in files if f["name"] == selected_file_name), None)
        if selected_file_obj:
            with st.spinner("🔒 Безопасная загрузка документа..."):
                pdf_bytes = download_public_file(public_link, selected_file_obj["path"])
            if pdf_bytes:
                try:
                    # Конвертация PDF в изображения для безопасного просмотра
                    images = convert_from_bytes(pdf_bytes, dpi=110)
                    st.info(f"📖 Страниц в документе: {len(images)}.")
                    for i, page in enumerate(images):
                        img_byte_arr = io.BytesIO()
                        page.save(img_byte_arr, format='JPEG')
                        st.image(img_byte_arr.getvalue(), use_container_width=True)
                except Exception:
                    st.error("🚨 Ошибка обработки PDF.")
            else:
                st.error("🚨 Ошибка загрузки.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 30px;'><b>Разработчик цифрового модуля:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ • Цифровая экосистема ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)

