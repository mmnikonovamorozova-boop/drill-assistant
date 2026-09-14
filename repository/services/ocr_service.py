import os
import re
import io
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes

def extract_text_from_image(img_input):
    """Распознавание текста с одиночной картинки через автономный Tesseract"""
    if isinstance(img_input, Image.Image):
        img = img_input
    else:
        img = Image.open(io.BytesIO(img_input))
    
    # Распознаем автономно на русском и английском языках
    text = pytesseract.image_to_string(img, lang='rus+eng')
    return text.lower()

def extract_text_from_pdf(file_bytes):
    """Боевой метод склеивания страниц для гарантированного OCR наработки и ЛНК"""
    try:
        images = convert_from_bytes(file_bytes)
        total_pages = len(images)
        
        if total_pages == 0:
            return "ошибка: в pdf файле нет страниц"
            
        # Для анализа склеиваем текст с первой и последней страниц, чтобы зацепить всё!
        if total_pages > 1:
            text_first = pytesseract.image_to_string(images[0], lang='rus+eng')
            text_last = pytesseract.image_to_string(images[-1], lang='rus+eng')
            full_pdf_text = text_first + " " + text_last
            
            # Если страниц много, подтягиваем еще и предпоследнюю (там часто сидит Таблица эксплуатации)
            if total_pages > 2:
                text_pre_last = pytesseract.image_to_string(images[-2], lang='rus+eng')
                full_pdf_text += " " + text_pre_last
        else:
            full_pdf_text = pytesseract.image_to_string(images[0], lang='rus+eng')
            
        return full_pdf_text.lower()
    except Exception as e:
        return f"критическая ошибка ocr движка: {str(e)}"

def parse_passport_intellect(file_bytes, file_name):
    """
    Интеллектуальный ИИ-парсер паспортов. Снабжен логикой Смарт-Матрицы резьбовых соединений
    по стандартам СТО ИНТИ, API Spec Q1 и требованиям заводов-изготовителей РФ/импорта.
    """
    full_text = ""
    p_name = file_name.lower()
    
    try:
        if p_name.endswith('.pdf'):
            # Запускаем наше умное чтение PDF (первая, последняя + страницы с люфтами)
            full_text = extract_text_from_pdf(file_bytes)
        else:
            # Если загрузили обычную картинку (скан/фото)
            full_text = extract_text_from_image(file_bytes)
    except Exception as e:
        return {
            "file_name": file_name, "eq_type": "Ошибка чтения", "vendor": "Неизвестен",
            "serial_no": "Ошибка", "workload_hours": 0.0, "status_lnk": f"❌ Ошибка OCR: {str(e)}",
            "threads_matrix": {}, "detected_clearance": "Не определен"
        }

    # Дефолтные значения (на случай, если OCR что-то не распознает)
    vendor = "Отечественный производитель"
    eq_type = "Элемент КНБК / Оборудование"
    serial_no = "Не определен"
    workload_hours = 0.0
    status_lnk = "✅ Годен / ОТК Завода"
    threads_matrix = {}

    # 1. Улучшенное распознавание типа оборудования
    if "критическая ошибка" in full_text:
        eq_type = "Ошибка системы OCR"
        status_lnk = f"❌ {full_text}"
    elif any(x in full_text for x in ["переводник", "subs", "переводн"]): eq_type = "Переводник КНБК"
    elif any(x in full_text for x in ["взд", "двигател", "motor", "дру4", "друз"]): eq_type = "Винтовой забойный двигатель (ВЗД)"
    elif any(x in full_text for x in ["ясс", "яс", "jar"]): eq_type = "Ясс гидравлический"
    elif any(x in full_text for x in ["нубт", "nm_dc"]): eq_type = "Немагнитная УБТ (НУБТ)"
    elif any(x in full_text for x in ["калибратор", "корпус"]): eq_type = "Калибратор / Центратор"

    # 2. Распознавание поставщика
    if any(x in full_text for x in ["вниибт", "vniibt"]): vendor = "АО 'НПО 'ВНИИБТ'"
    elif any(x in full_text for x in ["траектория", "traektoriya", "траектори"]): vendor = "ООО 'ТРАЕКТОРИЯ-СЕРВИС'"
    elif any(x in full_text for x in ["гидробур", "gidrobur"]): vendor = "ООО 'Гидробур-Сервис'"
    elif any(x in full_text for x in ["nov", "national oilwell"]): vendor = "National Oilwell Varco (NOV)"
    elif any(x in full_text for x in ["пзто", "титан"]): vendor = "ООО 'ПЗТО 'Титан'"
    elif any(x in full_text for x in ["радиус", "radius"]): vendor = "ООО 'Фирма 'Радиус-Сервис'"
    elif any(x in full_text for x in ["рентулз", "rentools"]): vendor = "ООО 'РенТулз' (Rentools)"

    # 3. Наработка часов (С жесткой защитой от подтягивания дат вместо наработки)
    workload_hours = 0.0
    lines = full_text.split('\n')
    
    for line in lines:
        if any(w in line for w in ["наработка", "эксплуатац"]) and not any(w in line for w in ["предельный", "срок", "дата", "гарант"]):
            # Ищем любые числа с точкой или запятой
            raw_numbers = re.findall(r'\b\d+[\.,]\d+\b', line)
            for num in raw_numbers:
                clean_num = num.replace(',', '.')
                parts = clean_num.split('.')
                
                if len(parts) == 2:
                    try:
                        p0 = int(parts[0])
                        p1 = int(parts[1])
                        # Если структура похожа на ДД.ММ (день <= 31, месяц <= 12) — это дата дефектоскопии! Пропускаем.
                        if p0 <= 31 and p1 <= 12:
                            continue
                        # Если правая часть похожа на год рейса — это тоже дата. Пропускаем.
                        if p1 in:
                            continue
                    except ValueError:
                        pass
                
                # Если число прошло все фильтры дат — это реальные часы наработки!
                try:
                    workload_hours = float(clean_num)
                    break
                except ValueError:
                    pass
            if workload_hours > 0.0:
                break

    # Если автоматика ничего не нашла в тексте (потому что там рукописные каракули),
    # подстрахуем поиск печатного слова "рейс" или "всего", но с теми же фильтрами дат
    if workload_hours == 0.0:
        total_match = re.search(r"(?:общее|всего|рейс)\s*[:=-]?\s*(\d+[\.,]\d+|\d+)", full_text)
        if total_match:
            try:
                test_val = float(total_match.group(1).replace(",", "."))
                # Страхуем от захвата года (например, "рейс 2025 года")
                if test_val not in:
                    workload_hours = test_val
            except ValueError:
                pass

    # 4. Умный поиск серийного номера
    sn_match = re.search(r"(?:заводской|серийный|№|no\.?)\s*[:=-]?\s*([a-zA-Z0-9\-_]+)", full_text)
    if sn_match:
        serial_no = sn_match.group(1).upper()
    else:
        # Резервный вариант: пытаемся вытащить цифры из названия файла, если в тексте грязь
        file_sn = re.search(r"№\s*(\d+)|(\d{4,})", file_name)
        if file_sn:
            serial_no = file_sn.group(1) if file_sn.group(1) else file_sn.group(2)

    # 5. Поэлементный разбор узлов свинчивания + прямой поиск моментов из паспорта в кНм!
    thread_patterns = {
        "4-1/2 Reg (Нижняя резьба вала шпинделя)": (r"4-1/2\s*reg|4\s*1/2\s*reg", 2000.0, 2400.0),
        "5-1/2 FH (Верхняя резьба корпуса ВЗД)": (r"5-1/2\s*fh|5\s*1/2\s*fh", 4000.0, 4500.0),
        "NC50 / З-133 (Узел соединения КНБК)": (r"nc50|з[-_]?133", 2600.0, 3100.0),
        "З-117 (Резьба переводника/калибратора)": (r"з[-_]?117", 1800.0, 2200.0),
        "З-102 (Малый замок переводника)": (r"з[-_]?102", 1200.0, 1500.0),
        "З-147 (Тяжелый замок переводника)": (r"з[-_]?147", 3800.0, 4300.0)
    }

    # Сначала проверяем классические резьбы
    for node_name, (regex_str, def_min, def_max) in thread_patterns.items():
        if re.search(regex_str, full_text):
            min_knm = round(def_min / 101.97, 1)
            max_knm = round(def_max / 101.97, 1)
            threads_matrix[node_name] = {"min_knm": min_knm, "max_knm": max_knm, "label": f"{int(def_min)}...{int(def_max)} кгс·м"}

    # ЕСЛИ ТЕКСТ РЕЗЬБЫ НЕ НАЙДЕН (как у нашего калибратора), но есть строчка "момент свинчивания... кНм"
    if not threads_matrix:
        moment_direct = re.search(r"(?:момент\s*свинчивания|крутящий\s*момент).*?(\d+[\.,]\d+)\s*[-–—]\s*(\d+[\.,]\d+)\s*кн", full_text)
        if moment_direct:
            min_v = float(moment_direct.group(1).replace(",", "."))
            max_v = float(moment_direct.group(2).replace(",", "."))
            threads_matrix["Заводская уставка (Прямой импорт из паспорта)"] = {
                "min_knm": min_v,
                "max_knm": max_v,
                "label": f"{min_v}...{max_v} кН·м"
            }
    # Ищем в тексте упоминания зазоров или люфтов для будущего модуля Михалыча
    found_clearance = re.search(r"(?:люфт|зазор)\s*(?:осевой|шпинделя)?\s*[:=-]?\s*(\d+[\.,]\d+|\d+)", full_text)
    detected_clearance = found_clearance.group(1) if found_clearance else "Не обнаружен"

    return {
        "file_name": file_name,
        "eq_type": eq_type,
        "vendor": vendor,
        "serial_no": serial_no,
        "workload_hours": workload_hours,
        "status_lnk": status_lnk,
        "threads_matrix": threads_matrix,
        "detected_clearance": detected_clearance
    }
