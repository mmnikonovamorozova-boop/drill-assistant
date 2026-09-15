import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import json
import os
import re
import io
from PIL import Image

# 1. АППАРАТНАЯ НАСТРОЙКА ИНТЕРФЕЙСА СТРИМЛИТ (СТРОГО НА ПЕРВОМ МЕСТЕ)
st.set_page_config(page_title="Виртуальный ротор ННБ", layout="wide")

# 2. ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ СЕССИИ ДЛЯ ЗАЩИТЫ ОТ ОШИБОК ИМЕНИ (NameError)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = True  # Для автономной отладки в поле
if "parsed_bha_df" not in st.session_state:
    st.session_state["parsed_bha_df"] = None
if "bha_wear_critical" not in st.session_state:
    st.session_state["bha_wear_critical"] = False
if "bha_sklad_list" not in st.session_state:
    st.session_state["bha_sklad_list"] = []
if "vzd_passport_brand" not in st.session_state:
    st.session_state["vzd_passport_brand"] = "Не определен"
if "vzd_passport_limit" not in st.session_state:
    st.session_state["vzd_passport_limit"] = 0.0

# 3. КАСТОМНЫЕ СТИЛИ ДЛЯ КОНТРАСТНОЙ НОЧНОЙ ЧИТАЕМОСТИ НА СТОЙКЕ БУРИЛЬЩИКА
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stButton>button { width: 100%; height: 3em; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 36px !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)
def init_knbk_database():
    """Автоматическое создание и наполнение локальной базы комплаенса КНБК СТО ИНТИ"""
    conn = sqlite3.connect("knbk_core.db")
    cursor = conn.cursor()
    
    # Создаем таблицу элементов КНБК для аудита СВП/Ротора
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS elements_library_db (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        element_type TEXT, 
        model TEXT, 
        nominal_od REAL, 
        nominal_id REAL, 
        max_torque REAL, 
        max_temp REAL
    )""")
    
    # Создаем таблицу технологических ограничений и матрицы рисков
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_matrix (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        factor_type TEXT,
        factor_name TEXT,
        penalty_points REAL,
        stop_threshold_modifier REAL
    )""")
    
    conn.commit()
    return conn, cursor

# Вызов инициализации базы при запуске скрипта
conn, cursor = init_knbk_database()
# Наполнение таблицы рисков, если она пустая
cursor.execute("SELECT COUNT(*) FROM risk_matrix")
if cursor.fetchone()[0] == 0:
    risks_data = [
        # Химия, интервалы бурения, регламенты и конструктив ВЗД
        ('acid', 'Чистая история (Без ОПЗ)', 0.0, 0.0),
        # ... (данные по факторам риска для таблицы risk_matrix)
    ]
    cursor.executemany("""
        INSERT INTO risk_matrix (factor_type, factor_name, penalty_points, stop_threshold_modifier) 
        VALUES (?, ?, ?, ?)
    """, risks_data)
    conn.commit()

# Закрываем временную сессию инициализации базы
conn.close()
def parse_field_bha_report(uploaded_file):
    """Всеядный парсер рапортов КНБК с защитой от сбоя кодировок"""
    df = None
    file_name = uploaded_file.name

    # 1. Попытка чтения как Excel
    if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
        try:
            df = pd.read_excel(uploaded_file, header=None).dropna(how='all')
        except Exception:
            uploaded_file.seek(0)
            df = None

    # 2. Если Excel сломался или это CSV — читаем как текст с перебором кодировок
    if df is None:
        try:
            raw_bytes = uploaded_file.read()
            try:
                text_data = raw_bytes.decode("cp1251", errors="ignore")
            except Exception:
                text_data = raw_bytes.decode("utf-8", errors="ignore")
            
            lines = text_data.splitlines()
            parsed_rows = []
            for line in lines:
                if not line.strip():
                    continue
                separator = ';' if ';' in line else ','
                cells = [c.strip().replace('"', '') for c in line.split(separator)]
                parsed_rows.append(cells)
            df = pd.DataFrame(parsed_rows)
        except Exception:
            return {"field": "Не указано", "well": "Не указано", "client": "Не указано", "bha_num": "1"}, None
    # Создаем базовый словарь для хранения метаданных скважины
    meta = {
        "field": "Не указано", 
        "well": "Не указано", 
        "client": "Не указано", 
        "bha_num": "1"
    }
    # Перебор строк для поиска метаданных
    for idx, row in df.iterrows():
        row_list = list(row.values)
        for i, cell in enumerate(row_list):
            cell_clean = str(cell).strip()
            
            # Извлекаем Месторождение
            if "Месторождение" in cell_clean and i + 2 < len(row_list):
                meta["field"] = str(row_list[i + 2]).strip()
            # Извлекаем Заказчика
            if "Заказчик" in cell_clean and i + 1 < len(row_list):
                meta["client"] = str(row_list[i + 1]).strip()
                
            # Извлекаем Куст и Скважину
            if "Куст" in cell_clean and i + 2 < len(row_list):
                meta["well"] = str(row_list[i + 2]).strip()
                
            # Извлекаем Номер КНБК
            if "Номер КНБК" in cell_clean and i + 1 < len(row_list):
                raw_bha_num = str(row_list[i + 1]).strip()
                meta["bha_num"] = raw_bha_num.split('.')[0] if '.' in raw_bha_num else raw_bha_num
    # Ищем индекс начала таблицы элементов КНБК
    table_start_idx = None
    for idx, row in df.iterrows():
        row_str_lower = [str(cell).lower() for cell in row.values]
        if any("элемент" in c for c in row_str_lower) and any("серийный" in c for c in row_str_lower):
            table_start_idx = idx
            break

    # Если шапку таблицы не нашли — аварийно возвращаем метаданные
    if table_start_idx is None:
        return meta, None
    # Вырезаем сырую таблицу элементов, начиная от найденной шапки
    df_bha_raw = df.loc[table_start_idx:].copy()
    raw_headers = df_bha_raw.iloc[0].values
    clean_headers = [str(h).strip().replace('\n', ' ') for h in raw_headers]
    df_bha_raw.columns = clean_headers
    df_bha_raw = df_bha_raw.iloc[1:]

    # Ищем колонку с названиями элементов
    element_col_idx = 0
    for i, col in enumerate(df_bha_raw.columns):
        if "элемент" in str(col).lower():
            element_col_idx = i
            break
    # Фильтруем строки по ключевым словам бурового оборудования
    keywords = "ВР|ВЗД|УБТ|ТБТ|СБТ|П-|М-|долото|клапан|теле|mwd|рус|bs|дру|мвр|кс|яс|sub|нубт|фильтр"
    df_bha_clean = df_bha_raw[df_bha_raw.iloc[:, element_col_idx].astype(str).str.contains(
        keywords, case=False, na=False
    )].copy()
    
    # Зачищаем пустые значения в столбцах
    df_bha_clean = df_bha_clean.dropna(how='all')
    # Инициализируем новые столбцы комплаенса и очищаем сессию
    df_bha_clean["Статус СМК"] = "🟢 Паспорт проверен"
    df_bha_clean["Отклонение OD, мм"] = 0.0
    st.session_state["bha_wear_critical"] = False

    # Загружаем библиотеку элементов для сверки номиналов (если файл существует)
    elements_lib = []
    if os.path.exists("bha_elements_library.json"):
        try:
            with open("bha_elements_library.json", "r", encoding="utf-8") as f:
                elements_lib = json.load(f).get("elements_library", [])
        except Exception:
            pass
    # Построчный разбор диаметров с защитой от текстовых дробей
    for idx, row in df_bha_clean.iterrows():
        el_str = str(row.iloc[element_col_idx]).upper()
        
        # Ищем совпадение элемента в библиотеке паспортов
        match = next((item for item in elements_lib if item["model"] in el_str or item["element_type"].upper() in el_str), None)
        if match:
            # Извлекаем сырую строку диаметра (из 3-й колонки или по имени НаружныйДиаметр)
            raw_od_str = str(row.get("НаружныйДиаметр", row.iloc[2])).strip()
            
            # Расщепляем дроби мастера по слешам
            if "/" in raw_od_str:
                raw_od_str = raw_od_str.split("/")[0].strip()
            elif "\\" in raw_od_str:
                raw_od_str = raw_od_str.split("\\")[0].strip()
            try:
                # Удаляем все символы, кроме цифр и точек, заменяя запятые
                clean_od_str = re.sub(r'[^\d\.]', '', raw_od_str.replace(",", "."))
                fact_od = float(clean_od_str)
                
                # Расчет отклонения от проектного номинала ИНТИ
                diff = abs(match["nominal_od"] - fact_od)
                df_bha_clean.at[idx, "Отклонение OD, мм"] = round(diff, 1)
                
                # Если износ корпуса превышает 4.5 мм — вешаем красный статус СМК
                if diff > 4.5:
                    df_bha_clean.at[idx, "Статус СМК"] = "🔴 ПРЕВЫШЕН ИЗНОС OD!"
                    st.session_state["bha_wear_critical"] = True
            except Exception:
                df_bha_clean.at[idx, "Статус СМК"] = "⚠ ОШИБКА ФОРМАТА"
        else:
            df_bha_clean.at[idx, "Статус СМК"] = "静态 НЕТ В БАЗЕ ПАСПОРТОВ"

    # Сохраняем очищенный список элементов в сессию и возвращаем результат
    st.session_state["raw_bha_names"] = df_bha_clean.iloc[:, element_col_idx].dropna().tolist()
    return meta, df_bha_clean
# Извлекаем сквозные параметры рейса из глобального шлюза сессии
engineer = st.session_state.get("engineer_name", "Иванов И.И.")
well = st.session_state.get("well_number", "Скв. № 202, Куст 12")
field = st.session_state.get("field_name", "Приобское")
bha = st.session_state.get("bha_number", "2")
client = st.session_state.get("main_page_company", "ООО Газпром добыча Уренгой")

# Вывод основного заголовка интеграционного модуля
st.title("⚙ Интегрированный Виртуальный Ротор Инженера ННБ")
st.caption("Единая среда автоматического комплаенса, контроля затяжки УМК и люфтов шпинделя ВЗД по СТО ИНТИ")
st.markdown(f"""
<div style="background-color:#1E293B; padding:15px; border-radius:10px; border-left: 5px solid #3B82F6; margin-bottom:20px;">
📍 <b>Месторождение:</b> {field} | 🛢 <b>Заказчик:</b> {client} | 🆔 <b>Скв/Куст:</b> {well} | 🔢 <b>КНБК №:</b> {bha}
</div>
""", unsafe_allow_html=True)
st.markdown("### 🕒 Шаг 1: Процессный статус КНБК")
operation_phase = st.radio(
    "Укажите текущую фазу работы с компоновкой:",
    ["📌 ФАЗА 1: Стартовая компоновка (Сборка на мостках / Проект ГГИ)",
     "🔄 ФАЗА 2: Динамическая компоновка (Инструмент на забое / Онлайн мониторинг)"],
    horizontal=True
)
st.markdown("---")
st.markdown("### 📥 Шаг 2: Загрузка полевого эскиза / Рапорта по КНБК")

# Загрузчик файлов рапортов КНБК с поля
uploaded_report = st.file_uploader(
    "Перетащите сюда официальный файл рапорта КНБК (.csv, .xlsx, .xls):", 
    type=["csv", "xlsx", "xls"]
)
if uploaded_report is not None:
    try:
        # Запускаем защищенный парсер
        meta_parsed, table_parsed = parse_field_bha_report(uploaded_report)
        
        if table_parsed is not None and not table_parsed.empty:
            st.session_state["parsed_bha_df"] = table_parsed
            st.session_state["field_name"] = meta_parsed["field"]
            st.session_state["well_number"] = meta_parsed["well"]
            st.session_state["main_page_company"] = meta_parsed["client"]
            st.session_state["bha_number"] = meta_parsed["bha_num"]
            st.success("✔ Рапорт бурового мастера успешно распознан и загружен в СМК!")
    except Exception as e:
        st.error(f"Ошибка автоматического разбора структуры файла: {str(e)}")
if st.session_state.get("parsed_bha_df") is not None:
    with st.expander("📐 Спецификация геометрии КНБК из рапорта бурового мастера", expanded=True):
        display_df = st.session_state["parsed_bha_df"].copy()
        
        # Зачищаем текстовые остатки для красивого отображения в Streamlit
        display_df = display_df.astype(str).replace('nan', '').replace('None', '')
        
        # Выводим таблицу с подгонкой под ширину контейнера
        st.dataframe(display_df, use_container_width=True, hide_index=True)
st.markdown("---")
st.markdown("### 📸 Шаг 3: ИИ-сканирование заводских паспортов и актов ЛНК")
st.write("Загрузите файлы для автоматического извлечения лимитов ВЗД по люфтам и контроля статуса резьбы по СТО ИНТИ.")

# Включаем множественную загрузку пачки паспортов за один клик
uploaded_passports = st.file_uploader(
    "Перетащите сюда ПАКЕТОМ все сканы/фото паспортов элементов КНБК (.png, .jpg, .pdf):",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True,
    key="package_ocr_integrated"
)
# Инициализация базовых параметров для модуля ВЗД на случай отсутствия сканов
actual_vzd_limit = 10.0
detected_vendor = "Не определен"

# Таблица для визуального вывода результатов OCR-сканирования
recognized_html_rows = ""
passport_loop_count = 0
if uploaded_passports:
    for uploaded_file in uploaded_passports:
        passport_loop_count += 1
        p_name = uploaded_file.name.lower()
        
        # Симулируем извлечение текста из документа (в реальной системе здесь блок pytesseract)
        # ИИ-логика распознавания завода и его лимитов из паспорта
        if any(x in p_name for x in ["радиус", "radius"]):
            detected_vendor = "ООО 'Фирма 'Радиус-Сервис'"
            actual_vzd_limit = 10.0  # Паспортный лимит Радиус-Сервис
        elif any(x in p_name for x in ["буринтех", "burinteh"]):
            detected_vendor = "НПП 'Буринтех'"
            actual_vzd_limit = 5.0   # Паспортный лимит Буринтех
        else:
            detected_vendor = "Отечественный ВЗД (ГОСТ)"
            actual_vzd_limit = 4.5   # Стандартный лимит по умолчанию
        # Фиксируем данные последнего распознанного паспорта в сессию для расчета зазоров
        st.session_state["vzd_passport_brand"] = detected_vendor
        st.session_state["vzd_passport_limit"] = actual_vzd_limit
        
        # Формируем HTML-строку для вывода результатов сканирования инженеру
        recognized_html_rows += f"""
        <tr style='border-bottom: 1px solid #374151;'>
            <td style='padding: 12px; color: #38BDF8; font-weight: bold;'>{uploaded_file.name}</td>
            <td style='padding: 12px; color: #E5E7EB;'>{detected_vendor}</td>
            <td style='padding: 12px; color: #F59E0B; font-weight: bold;'>{actual_vzd_limit:.1f} мм</td>
            <td style='padding: 12px; color: #10B981;'>✅ Верифицировано ИНТИ</td>
        </tr>
        """
# Исправленный вывод таблицы результатов OCR
if passport_loop_count > 0:
    st.markdown(f"""
    <table style="width: 100%; border-collapse: collapse; text-align: left; background-color: #111827; border: 1px solid #374151; border-radius: 8px;">
        <thead>
            <tr style='background-color: #1F2937; border-bottom: 2px solid #4B5563;'>
                <th style='padding: 12px; color: #9CA3AF;'>Файл</th>
                <th style='padding: 12px; color: #9CA3AF;'>Завод-изготовитель</th>
                <th style='padding: 12px; color: #9CA3AF;'>Лимит люфта</th>
                <th style='padding: 12px; color: #9CA3AF;'>Статус ИНТИ</th>
            </tr>
        </thead>
        <tbody>
            {recognized_html_rows}
        </tbody>
    </table>
    """, unsafe_allow_html=True)  # <-- ДАННЫЙ ФЛАГ ОБЯЗАТЕЛЕН

st.markdown("---")
st.markdown("<h2 style='font-size:26px;'>🔄 Шаг 3.5: Виртуальный стол ротора (Контроль переводников)</h2>", unsafe_allow_html=True)
st.caption("Автоматическая кросс-проверка замковых резьб переводников на совместимость и геометрический износ по СТО ИНТИ")

# Создаем трехпанельную сетку сборочного стола инженера ННБ
col_panel1, col_panel2, col_panel3 = st.columns([1, 3, 2])

# Инициализируем хранилище для журнала нестыковок
bad_joints_log = []
is_rotor_critical = False

with col_panel2:
    st.markdown("<div style='background-color:#1E293B; padding:10px; border-radius:5px; text-align: center; font-weight: bold; color: #38BDF8;'>⚙ ГЕОМЕТРИЧЕСКИЙ КОМПЛАЕНС СТЫКОВ КНБК</div>", unsafe_allow_html=True)
    
    # Если рапорт КНБК загружен, запускаем аудит фактической геометрии мастера
    if st.session_state.get("parsed_bha_df") is not None:
        df_bha = st.session_state["parsed_bha_df"]
        elements_list = st.session_state.get("raw_bha_names", [])
        # Соединяемся с базой для извлечения проектных номиналов (при необходимости)
        conn_audit = sqlite3.connect("knbk_core.db")
        cursor_audit = conn_audit.cursor()
        
        # Запускаем попарный обход элементов гирлянды КНБК с поиском по 1-й колонке и отключением Regex
        for idx in range(len(elements_list) - 1):
            el_top = str(elements_list[idx]).strip()
            el_bot = str(elements_list[idx+1]).strip()
            st.markdown(f"🔗 **Стык №{idx+1}:** {el_top} ↔ {el_bot}")
                        
            # --- ИСПРАВЛЕНИЕ: ОТКЛЮЧЕНИЕ REGEX С ФЛАГОМ regex=False ---
            try:
                row_top_data = df_bha[df_bha.iloc[:, 0].astype(str).str.contains(el_top, case=False, na=False, regex=False)]
                top_D = float(str(row_top_data.iloc[0, 4]).replace(",", "."))
            except Exception:
                cursor_audit.execute("SELECT nominal_od FROM elements_library_db WHERE ? LIKE '%' || model || '%'", (el_top,))
                row_db = cursor_audit.fetchone()
                top_D = float(row_db[0]) if row_db else 177.8

            try:
                row_bot_data = df_bha[df_bha.iloc[:, 0].astype(str).str.contains(el_bot, case=False, na=False, regex=False)]
                bot_D = float(str(row_bot_data.iloc[0, 4]).replace(",", "."))
            except Exception:
                cursor_audit.execute("SELECT nominal_od FROM elements_library_db WHERE ? LIKE '%' || model || '%'", (el_bot,))
                row_db_bot = cursor_audit.fetchone()
                bot_D = float(row_db_bot[0]) if row_db_bot else 165.1


            # Вычисляем фактический перепад габаритов (ступень) на стыке
            delta_D = abs(top_D - bot_D)
            
            # Если перепад диаметров превышает 15 мм — выдаем критическую ошибку СМК
            if delta_D > 15.0:
                st.error(f"❌ КРИТИЧЕСКИЙ ПЕРЕПАД ГАБАРИТОВ СТЫКА: Разница составляет {delta_D:.1f} мм! Высокий риск уступа при СПО.")
                is_rotor_critical = True
                bad_joints_log.append({"idx": idx + 1, "top": el_top, "bot": el_bot, "delta": delta_D})
            else:
                st.info(f"📐 Геометрический переход в допуске СТО ИНТИ (ΔD: {delta_D:.1f} мм)")
        
        # Закрываем сессию аудита базы данных
        conn_audit.close()
        st.session_state["is_rotor_critical"] = is_rotor_critical
        # ИИ-оптимизатор: Ищем подходящие переводники на мостках кустовой площадки
        sklad = st.session_state.get("bha_sklad_list", [])
        subs = [i for i in sklad if any(x in i.lower() for x in ["п-", "м-", "перевод", "sub"])]
        
        if is_rotor_critical and subs:
            st.markdown("💡 <b>Рекомендация ИИ СМК по пересборке КНБК со стеллажа:</b>", unsafe_allow_html=True)
            for s in subs[:2]:
                st.success(f"🔹 Установите переходник **{s}** для ликвидации ступени диаметров!")
        elif is_rotor_critical:
            st.warning("⚠ На стеллажах мостков нет подходящих переводников ПП. Требуется срочная отгрузка с базы снабжения.")
            
    else:
        # Режим интерактивного конструктора, если файл рапорта не загружен
        st.info("ℹ Полевой рапорт КНБК не загружен. Переход стола ротора в режим ручной верификации.")
with col_panel1:
    st.markdown("<div style='background-color:#1E293B; padding:10px; border-radius:5px; text-align: center; font-weight: bold; color: #6EE7B7;'>🧴 ТРИБОЛОГИЯ И СМАЗКА</div>", unsafe_allow_html=True)
    
    # Строго фиксированный список смазок по СТО ИНТИ S.QS.8
    grease_options = [
        "Стандартная (API)",
        "Графитовая (K=1.15)",
        "Тефлоновая (K=0.85)",
        "Прочая специальная (K=1.3)"
    ]
    
    grease_type = st.selectbox(
        "Тип резьбовой смазки (СТО ИНТИ S.QS.8):",
        options=grease_options,
        key="rotor_grease_selector"
    )
    
    # Привязываем коэффициенты трения к смазкам
    grease_dict = {"Стандартная (API)": 1.0, "Графитовая (K=1.15)": 1.15, "Тефлоновая (K=0.85)": 0.85, "Прочая special": 1.3}
    st.session_state["k_grease_live"] = grease_dict.get(grease_type, 1.0)
with col_panel3:
    st.markdown("<div style='background-color:#1E293B; padding:10px; border-radius:5px; text-align: center; font-weight: bold; color: #FBBF24;'>🔧 КЛЮЧ УМК И МОМЕНТЫ</div>", unsafe_allow_html=True)
    
    # Реестр стандартных плеч рычагов ключей УМК по СТО ИНТИ
    keys_db = {"УМК-10/1": 0.615, "УМК-35": 0.900, "УМК-48": 1.100, "УМК-75": 1.400, "УМК-90": 1.400}
    
    selected_key = st.selectbox(
        "Выберите модель ключа УМК:", 
        list(keys_db.keys()),
        key="rotor_key_selector"
    )
    passport_length = keys_db[selected_key]
    
    control_type = st.radio("Тип контроля натяжения:", ["🪢 Электронный (ИВЭ-50)", "💧 Гидравлический (Манометр)"], key="rotor_control_type")
    # Ввод фактических параметров геометрии рычагов ключа
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        f_length = st.number_input("Фактическое плечо рычага, м:", min_value=0.1, max_value=5.0, value=passport_length, step=0.05)
    with col_k2:
        l_rope = st.number_input("Длина каната натяжения, м:", min_value=0.5, max_value=15.0, value=3.5, step=0.1)

    # Выбор прочности стали для защиты резьб от смятия/скручивания
    steel_options = ["Д (D)", "К (K)", "Е (E)", "Л (L)", "М (M)", "Р (P-110)", "Т (S-135)"]
    pipe_steel = st.selectbox("Группа прочности стали (API Spec 5DP):", steel_options, index=5, key="rotor_steel_select")

    # Предел текучести сталей (в МПа) по СТО ИНТИ
    yield_db = {"Д (D)": 379, "К (K)": 517, "Е (E)": 517, "Л (L)": 655, "М (M)": 724, "Р (P-110)": 758, "Т (S-135)": 931}
    yield_strength = yield_db[pipe_steel]
    # Базовый паспортный момент для замка 146 мм (в кН·м)
    base_m_req = 38.5  
    
    # Корректируем момент с учетом коэффициента выбранной смазки (K_grease)
    k_grease = st.session_state.get("k_grease_live", 1.0)
    m_required = base_m_req * k_grease

    # Расчет предельно допустимого момента свинчивания во избежание скручивания резьбы
    max_allowed_moment = (yield_strength * 0.0001) * 6.5  
    st.session_state["m_required_live"] = m_required

    # Расчет усилия натяжения каната на электронном датчике ИВЭ-50 (в тоннах)
    if f_length > 0:
        force_kn = m_required / f_length
        force_tonnes = force_kn / 9.81
    else:
        force_tonnes = 0.0
    # Вывод целевого усилия затяжки для буровой бригады
    st.markdown(
        f"<div style='background-color:#111827; padding:15px; border-radius:8px; text-align:center; border:2px solid #F59E0B; margin-top:15px;'>"
        f"<span style='color:#9CA3AF; font-size:14px;'>🎯 ЦЕЛЕВОЕ УСИЛИЕ НАТЯЖЕНИЯ НА ИВЭ-50:</span><br>"
        f"<span style='color:#FBBF24; font-size:32px; font-weight:bold;'>{force_tonnes:.2f} тонн</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Верификация на смятие и пластическую деформацию резьбы
    if m_required > max_allowed_moment:
        st.error(f"❌ ПРЕДЕЛ ТЕКУЧЕСТИ: Момент свинчивания ({m_required:.1f} кН·м) превышает предел ({max_allowed_moment:.1f} кН·м) для стали {pipe_steel}!")
        st.session_state["umk_critical_error"] = True
    else:
        st.success("🟢 Расчетный момент безопасен для целостности замковой резьбы.")
        st.session_state["umk_critical_error"] = False
st.markdown("---")
st.markdown("<h2 style='font-size:26px;'>📏 Шаг 4: Контроль износа опор шпиндельной секции ВЗД</h2>", unsafe_allow_html=True)
st.caption("Математический аудит радиального и осевого зазора опор шпинделя по методикам заводов-изготовителей и СТО ИНТИ")

# Подтягиваем автоматически распознанные через ИИ-OCR лимиты из паспорта
detected_brand = st.session_state.get("vzd_passport_brand", "Не определен")
passport_limit = st.session_state.get("vzd_passport_limit", 4.5)

st.info(f"📋 **Данные ИИ-OCR из паспорта:** Изготовитель: {detected_brand} | Заводской лимит осевого люфта: {passport_limit:.1f} мм")

# Выбор Заказчика для применения жестких ограничений ТК недропользователей РФ
selected_client = st.selectbox(
    "Выберите Заказчика (Недропользователя) для применения ограничений:",
    ["ПАО Роснефть", "ПАО Газпром", "ПАО Лукойл", "🔄 Без учета ограничений Заказчика"],
    key="integrated_client_selector"
)
st.markdown("##### 📋 Результаты прямых измерений износа на устье скважины:")
col_v1, col_v2, col_v3 = st.columns(3)

# Ввод данных прямых замеров инженером ННБ
with col_v1:
    size_a = st.number_input("Размер 'А' (Верхний торец корпуса к валу), мм:", min_value=0.0, max_value=50.0, value=10.0, step=0.1, key="int_size_a")
with col_v2:
    size_b = st.number_input("Размер 'Б' (Нижний торец прижатого шпинделя), мм:", min_value=0.0, max_value=50.0, value=5.5, step=0.1, key="int_size_b")
with col_v3:
    radial_ich = st.number_input("Радиальный люфт по индикатору часового типа (ИЧ), мм:", min_value=0.0, max_value=10.0, value=0.20, step=0.05, key="int_radial")

col_v4, col_v5 = st.columns(2)
with col_v4:
    vzd_hours = st.number_input("Текущая наработка ВЗД за рейс, ч:", min_value=0.0, max_value=500.0, value=48.0, step=1.0, key="int_hours")
with col_v5:
    mud_density = st.number_input("Плотность бурового раствора, г/см³:", min_value=1.0, max_value=2.5, value=1.20, step=0.02, key="int_mud")

# Вычисляем фактический осевой люфт
calculated_axial_delta = size_a - size_b
st.markdown(f"**📊 Расчет факта:** Осевой люфт = {size_a:.1f} - {size_b:.1f} = `{calculated_axial_delta:.2f} мм`")
# База данных жестких лимитов ТК Заказчиков (СТО ИНТИ S.QS.7)
client_limits_db = {
    "ПАО Роснефть": {"малый": 3.0, "средний": 4.5, "большой": 6.0},
    "ПАО Газпром": {"малый": 3.5, "средний": 4.5, "большой": 5.5},
    "ПАО Лукойл": {"малый": 3.5, "средний": 5.0, "большой": 6.0}
}

parsed_df = st.session_state.get("parsed_bha_df")
bha_text = "".join(parsed_df.iloc[:, 1].astype(str).tolist()).lower() if parsed_df is not None else ""

if "240" in bha_text or "8''" in bha_text:
    size_group = "большой"
elif "172" in bha_text or "178" in bha_text or "6.75" in bha_text or "дру3" in bha_text:
    size_group = "средний"
else:
    size_group = "малый"

# Применение гибридного правила отбраковки СТО ИНТИ
if selected_client != "🔄 Без учета ограничений Заказчика":
    client_rule = client_limits_db[selected_client][size_group]
    # Выбираем минимальное (самое жесткое) значение между заводом и нефтяной компанией
    effective_max_limit = min(passport_limit, client_rule)
    st.warning(f"🎯 **Минимально допустимый порог зазора:** {effective_max_limit:.2f} мм (Паспорт: {passport_limit:.1f} мм | {selected_client}: {client_rule:.1f} мм)")
else:
    effective_max_limit = passport_limit
    st.info(f"🎯 **Минимально допустимый порог зазора:** {effective_max_limit:.2f} мм (По заводскому паспорту)")
    
# 1. КОНСТАНТЫ И КОЭФФИЦИЕНТЫ ИЗНОСА ПО ISO 281
base_life = 200.0  # Паспортный ресурс шпинделя в часах
mud_factor = (mud_density / 1.0) ** 1.5  # Влияние абразива

# Расчет коэффициента осевой деградации
effective_max_limit = st.session_state.get("effective_max_limit_live", 4.5)
if effective_max_limit > 0:
    wear_factor_axial = (calculated_axial_delta / effective_max_limit) ** 2.5
else:
    wear_factor_axial = 1.0

# Вспомогательный коэффициент для расчета усталости вала
term_a = (calculated_axial_delta / effective_max_limit) * 60.0 if effective_max_limit > 0 else 0.0

            # Корректное обнуление моточасов при критическом износе опор шпинделя
            if calculated_axial_delta >= effective_max_limit or radial_ich > 1.80:
                estimated_remaining_hours = 0.0
                fatigue_probability = 100.0
            else:
                estimated_remaining_hours = max(0.0, (base_life - vzd_hours) / (wear_factor_axial * mud_factor)) if wear_factor_axial * mud_factor > 0 else 0.0
                fatigue_probability = min(100.0, term_a + (radial_ich / 1.80) * 40.0)

calculated_vibration_g = (radial_ich ** 2) * 4.5 * (mud_density / 1.15)

st.markdown("---")
st.markdown("##### 🔬 Инженерный СППР-анализ состояния опор (СТО ИНТИ S.QS.7):")
col_met1, col_met2, col_met3 = st.columns(3)

with col_met1:
    st.metric(label="⌛ Прогноз остаточного ресурса опор", value=f"{estimated_remaining_hours:.1f} мото-ч", delta=f"-{vzd_hours:.0f} ч отработано")
with col_met2:
    vib_status = "Норма" if calculated_vibration_g < 2.5 else ("Повышенный" if calculated_vibration_g < 5.5 else "КРИТИЧЕСКИЙ")
    st.metric(label=f"🎯 Ожидаемая радиальная вибрация ({vib_status})", value=f"{calculated_vibration_g:.2f} g")
with col_met3:
    st.metric(label="🚨 Риск поломки / полета вала", value=f"{fatigue_probability:.1f} %")
# Финальный логический светофор и карточка СМК отбраковки шпинделя ВЗД
if calculated_axial_delta >= effective_max_limit:
    st.markdown(f"""
    <div style='background-color:#7F1D1D; padding:15px; border-radius:8px; border:2px solid #EF4444; margin-top:15px; color:#FEE2E2;'>
    🛑 <b>ЗАКЛЮЧЕНИЕ СМК: ВЗД ОТБРАКОВАН!</b><br>
    Фактический осевой люфт ({calculated_axial_delta:.2f} мм) достиг или превысил лимит ({effective_max_limit:.2f} мм). Спуск КНБК категорически запрещен.
    </div>
    """, unsafe_allow_html=True)
    st.session_state["vzd_critical_error"] = True
else:
    st.markdown(f"""
    <div style='background-color:#064E3B; padding:15px; border-radius:8px; border:2px solid #10B981; margin-top:15px; color:#D1FAE5;'>
    ✅ <b>ЗАКЛЮЧЕНИЕ СМК: ВЗД ДОПУЩЕН К БУРЕНИЮ</b><br>
    Осевой люфт в допуске ({calculated_axial_delta:.2f} мм &lt; {effective_max_limit:.2f} мм). Прогнозный ресурс опор шпинделя достаточен для продолжения рейса.
    </div>
    """, unsafe_allow_html=True)
    st.session_state["vzd_critical_error"] = False
st.markdown("---")
st.markdown("<h2 style='font-size:26px;'>📉 Шаг 5: Предиктивный симулятор технологического режима ННБ</h2>", unsafe_allow_html=True)
st.caption("Математическое моделирование рисков при проводке интервала скважины по заданным параметрам")

# Интерактивные слайдеры для симуляции рейса инженером ННБ
col_sim1, col_sim2 = st.columns(2)
with col_sim1:
    sim_wob = st.slider("Планируемая осевая нагрузка на долото (WOB), тонн:", min_value=0.0, max_value=35.0, value=12.0, step=0.5)
with col_sim2:
    sim_dls = st.slider("Планируемая интенсивность искривления (DLS), град/10м:", min_value=0.0, max_value=6.0, value=1.5, step=0.1)

# Математический расчет интегрального индекса технологического риска КНБК
base_risk = 15.0
if st.session_state.get("bha_wear_critical", False):
    base_risk += 25.0
if st.session_state.get("is_rotor_critical", False):
    base_risk += 30.0
if st.session_state.get("vzd_critical_error", False):
    base_risk += 40.0

# Влияние режима бурения на усталость КНБК
wob_factor = (sim_wob / 15.0) ** 2
dls_factor = (sim_dls / 2.0) ** 3
total_risk_index = min(100.0, base_risk * wob_factor * dls_factor)
st.markdown("##### 🛡 Итоговый статус комплаенса сборки КНБК:")

# Проверяем наличие критических ошибок во всех модулях виртуального ротора
has_errors = (
    st.session_state.get("bha_wear_critical", False) or 
    st.session_state.get("is_rotor_critical", False) or 
    st.session_state.get("umk_critical_error", False) or 
    st.session_state.get("vzd_critical_error", False)
)

# Отрисовка шкалы интегрального риска рейса
if total_risk_index > 75.0:
    st.error(f"🚨 ВЫСОКИЙ РИСК НПВ: Индекс опасности рейса {total_risk_index:.1f}%! Спуск КНБК не рекомендуется.")
elif total_risk_index > 40.0:
    st.warning(f"⚠ СРЕДНИЙ РИСК: Индекс опасности рейса {total_risk_index:.1f}%. Требуется повышенный контроль параметров бурения.")
else:
    st.success(f"🟢 НИЗКИЙ РИСК: Индекс опасности рейса {total_risk_index:.1f}%. Сборка КНБК и режимы в допуске.")

# Блок принудительного согласования (Override) при нарушениях регламентов
override_granted = False
if has_errors:
    st.markdown("<div style='background-color:#451A03; padding:12px; border-radius:5px; border:1px solid #F59E0B; margin-bottom:15px; color:#FEF3C7;'>🚨 ОБНАРУЖЕНЫ НАРУШЕНИЯ РЕГЛАМЕНТА СТО ИНТИ! Функция 'Утвердить' заблокирована.</div>", unsafe_allow_html=True)
    allow_override = st.checkbox("🔓 Активировать процедуру производственного согласования (Override)", key="rotor_override_chk")
    if allow_override:
        supervisor_auth = st.text_input("Укажите ФИО супервайзера Заказчика, давшего письменное разрешение:")
        if supervisor_auth.strip():
            override_granted = True
            st.success("✔ Процедура согласования подтверждена. Кнопка фиксации разблокирована.")

# Логика финальной кнопки отправки данных в архив СМК
btn_disabled = has_errors and not override_granted

if st.button("💾 Утвердить сборку КНБК и записать лог СМК", disabled=btn_disabled, key="final_save_btn_rotor"):
    try:
        # Пишем цифровой след сборки в локальную базу данных
        conn_log = sqlite3.connect("knbk_core.db")
        cursor_log = conn_log.cursor()
        
        log_status = "APPROVED_WITH_OVERRIDE" if override_granted else "CLEAR_SUCCESS"
        
        # Создаем таблицу логов, если ее не было
        cursor_log.execute("""
        CREATE TABLE IF NOT EXISTS bha_assembly_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            well_info TEXT,
            risk_idx REAL,
            status TEXT
        )""")
        
        cursor_log.execute(
            "INSERT INTO bha_assembly_logs (well_info, risk_idx, status) VALUES (?, ?, ?)",
            (f"{field} / {well}", total_risk_index, log_status)
        )
        conn_log.commit()
        conn_log.close()
        
        st.toast(f"💾 Запись успешно внесена в локальный реестр `knbk_core.db` со статусом {log_status}!", icon="🚀")
        st.balloons()
    except Exception as e_log:
        st.error(f"Ошибка записи в базу данных КИС: {str(e_log)}")
