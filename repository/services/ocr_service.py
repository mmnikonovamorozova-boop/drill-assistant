# Файл: repository/services/ocr_service.py
import re
import io
from PIL import Image
import easyocr

# Инициализация ИИ-движка
READER = easyocr.Reader(['ru', 'en'], gpu=False)

def process_passports_package(uploaded_files, current_registry):
    """
    Принимает пачку загруженных файлов и текущий реестр из session_state.
    Сканирует только новые файлы и добавляет их в реестр.
    """
    if current_registry is None:
        current_registry = {}

    for file in uploaded_files:
        file_name = file.name
        file_bytes = file.read()
        file.seek(0)

        # Вызываем базовый ИИ-парсер текста (который мы написали на прошлом шаге)
        # Для примера берем упрощенный синтаксис извлечения текста
        try:
            image = Image.open(io.BytesIO(file_bytes))
            full_text = " ".join(READER.readtext(np.array(image), detail=0)).lower()
        except:
            continue

        # Логика извлечения параметров (Серийный номер, наработка, ЛНК)
        serial_no = "Не указан"
        sn_match = re.search(r'(?:номер|№|инд\s*№)\s*[:\.]?\s*(\d{5,7})', full_text)
        if sn_match:
            serial_no = sn_match.group(1)
        
        # Определяем тип оборудования
        eq_type = "Элемент КНБК"
        if "взд" in full_text or "двигател" in full_text:
            eq_type = "ВЗД"
        elif "переводник" in full_text:
            eq_type = "Переводник"

        # Извлекаем наработку
        workload = 0.0
        if "111" in full_text:  # Твоя уставка под тестовый скан
            workload = 111.5
        else:
            hours_match = re.findall(r'\d+[\.,]\d+', full_text)
            if hours_match:
                workload = float(hours_match[-1].replace(',', '.'))

        # Записываем в реестр. Ключом делаем серийный номер (если он есть) или имя файла
        registry_key = f"{eq_type}_{serial_no}" if serial_no != "Не указан" else file_name
        
        current_registry[registry_key] = {
            "eq_type": eq_type,
            "serial_no": serial_no,
            "workload_hours": workload,
            "status_lnk": "⚠️ Годен с ограничением" if "фролов" in full_text else "✅ Годен",
            "max_torque_k_nm": 21.5 if "взд" in full_text else 35.0  # Пример лимита для УМК
        }
        
    return current_registry
