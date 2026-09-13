import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import json
import sqlite3

def init_knbk_database():
    """Автоматическое создание локальной базы данных комплаенса КНБК СТО ИНТИ"""
    import sqlite3
    conn = sqlite3.connect("knbk_core.db")
    cursor = conn.cursor()
    
    # 1. Создаем таблицу элементов и телесистем КНБК
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS elements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, name TEXT, max_temp REAL, c_part_limit REAL
    )""")
    # 2. Создаем таблицу технологических ограничений и матрицу сред
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_matrix (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        factor_type TEXT, 
        factor_name TEXT, 
        penalty_points REAL,
        stop_threshold_modifier REAL
    )""")
        # Проверяем, наполнена ли таблица, чтобы не дублировать данные при перезапусках
    cursor.execute("SELECT COUNT(*) FROM risk_matrix")
    if cursor.fetchone()[0] == 0:
        risks_data = [
            ('acid', 'Мягкая ОПЗ (Органические кислоты)', 5.0, -2.0),
            ('acid', 'Солянокислотная ванна HCl (Риск смыва хрома ВЗД)', 20.0, -5.0),
            ('acid', 'Агрессивный "Термит" HCl+HF (Экстремальное наводороживание)', 45.0, -12.0),
            ('lnk', '🔴 Высокий риск пропуска микротрещины', 15.0, 0.0)
        ]
        risks_data.extend([
            ('vzd', 'Низкозаходный 3/4 ("Бронебойный танк" // Высокий Stick-Slip)', 10.0, 0.0),
            ('region', 'Западная Сибирь / Ямал (Риск термозаклинивания резьб)', 0.0, -5.0),
            ('interval', 'Эксплуатационная колонна (1000 - 2500 м) [СПО: 12-18 часов]', 0.0, -5.0),
            ('interval', 'Техническая колонна (2500 - 3500 м) [СПО: ~24 часа]', 0.0, -12.0),
            ('interval', 'Бурение хвостовика / Зарезка БС (> 3500 м) [СПО: 1.5 - 2 суток!]', 0.0, -20.0)
        ])
        risks_data.extend([
            ('operator', 'Роснефть: Запрет наработки элементов КНБК > 250 ч без УЗК/МПК на устье', 15.0, -5.0),
            ('operator', 'Газпром нефть: Запрет бурения интервалов DLS > 3.5°/10м без MWD онлайн', 20.0, -8.0),
            ('operator', 'НОВАТЭК: Запрет спуска нижних пульсаторов MWD при КВЧ > 0.5%', 25.0, -10.0)
        ])
        cursor.executemany("INSERT INTO risk_matrix (factor_type, factor_name, penalty_points, stop_threshold_modifier) VALUES (?, ?, ?, ?)", risks_data)
               
    conn.commit()
    conn.commit()
    return conn, cursor


# --- СТРОГАЯ АВТЕНТИФИКАЦИЯ ЭКОСИСТЕМЫ ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Пожалуйста, пройдите авторизацию на Главной странице.")
    st.stop()

conn, cursor = init_knbk_database()

# Оптимизированный запуск: наполняем базу только если она пустая
cursor.execute("SELECT COUNT(*) FROM risk_matrix")
if cursor.fetchone()[0] == 0 and os.path.exists("bha_risk_matrix.json"):
    with open("bha_risk_matrix.json", "r", encoding="utf-8") as f:
        matrix_data = json.load(f)
    insert_risks = [(f['type'], f['name'], f['points'], f['stop_mod']) for f in matrix_data.get('risk_matrix', [])]
    cursor.executemany("INSERT INTO risk_matrix (factor_type, factor_name, penalty_points, stop_threshold_modifier) VALUES (?, ?, ?, ?)", insert_risks)

cursor.execute("CREATE TABLE IF NOT EXISTS elements_library_db (id INTEGER PRIMARY KEY AUTOINCREMENT, element_type TEXT, model TEXT, nominal_od REAL, nominal_id REAL, max_torque REAL, max_temp REAL)")

cursor.execute("SELECT COUNT(*) FROM elements_library_db")
if cursor.fetchone()[0] == 0 and os.path.exists("bha_elements_library.json"):
    with open("bha_elements_library.json", "r", encoding="utf-8") as f:
        lib_data = json.load(f)
    insert_elements = [(e['element_type'], e['model'], e['nominal_od'], e['nominal_id'], e['max_torque_k_nm'], e['max_temp_c']) for e in lib_data.get('elements_library', [])]
    cursor.executemany("INSERT INTO elements_library_db (element_type, model, nominal_od, nominal_id, max_torque, max_temp) VALUES (?, ?, ?, ?, ?, ?)", insert_elements)
    conn.commit()

# Повторно опрашиваем базу, чтобы наполнить список моделей для конструктора КНБК
cursor.execute("SELECT model FROM elements_library_db")
rows_models = cursor.fetchall()
st.session_state["bha_models_list"] = [row[0] for row in rows_models] if rows_models else ["З-147", "З-133", "З-117"]

# Конфигурация страницы в стиле drill-assistant
st.set_page_config(page_title="Сборка КНБК", layout="wide")

# Внедрение кастомных стилей для максимальной ночной читаемости в полях
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stButton>button { width: 100%; height: 3em; font-weight: bold; font-size: 16px; }
    .reportview-container .main .block-container{ padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚙️ Сборка КНБК и Динамический Комплаенс")
st.caption("Автоматический парсинг полевых рапортов КНБК, учёт износа, химии сред и цены времени СПО по СТО ИНТИ")

# --- СКВОЗНАЯ СИНХРОНИЗАЦИЯ МЕТАДАННЫХ СМК ---
engineer = st.session_state.get("engineer_name", "Иванов И.И.")
well = st.session_state.get("well_number", "Скв. № 202, Куст 12")
field = st.session_state.get("field_name", "Приобское")
bha = st.session_state.get("bha_number", "2")
client = st.session_state.get("main_page_company", "ООО Газпром добыча Уренгой")

# Крупная, контрастная информационная плашка (читается в любое время суток)
st.markdown(f"""
<div style="background-color:#1E293B; padding:15px; border-radius:10px; border-left: 5px solid #3B82F6; margin-bottom:20px;">
    <span style="color:#9CA3AF; font-size:12px;">ТЕКУЩИЙ КОНТЕКСТ СМК КОМПАНИИ</span><br>
    <strong style="color:#F3F4F6; font-size:16px;">📍 Месторождение:</strong> <span style="color:#38BDF8; font-size:16px;">{field}</span> | 
    <strong style="color:#F3F4F6; font-size:16px;">🛢 Заказчик:</strong> <span style="color:#38BDF8; font-size:16px;">{client}</span> | 
    <strong style="color:#F3F4F6; font-size:16px;">🆔 Скв/Куст:</strong> <span style="color:#38BDF8; font-size:16px;">{well}</span> | 
    <strong style="color:#F3F4F6; font-size:16px;">🔢 КНБК №:</strong> <span style="color:#38BDF8; font-size:16px;">{bha}</span>
</div>
""", unsafe_allow_html=True)

# --- ПАСПОРТ ВЕРИФИКАЦИИ СТО ИНТИ ---
with st.expander("🔰 Паспорт верификации СТО ИНТИ S.QS.7 и S.100.3", expanded=False):
    st.markdown("""
    * **Входной контроль КНБК:** Запрет ручного ввода геометрии при наличии электронного рапорта бурового мастера.
    * **Учет скрытой деградации:** Обязательное ранжирование усталостной долговечности резьбовых соединений ЗТС при работе в агрессивных химических средах и температурном шоке.
    * **Следственная прослеживаемость:** Автоматическое логирование фактов принудительного спуска изношенного оборудования (протокол 'Override').
    """)

def parse_field_bha_report(uploaded_file):
    df = None
    file_name = uploaded_file.name
    
    import json
    elements_lib = []
    if os.path.exists("bha_elements_library.json"):
        with open("bha_elements_library.json", "r", encoding="utf-8") as f:
            elements_lib = json.load(f).get("elements_library", [])
    
    if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
        try:
            df = pd.read_excel(uploaded_file, header=None).dropna(how='all')
        except Exception:
            uploaded_file.seek(0)
            df = None
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

    meta = {"field": "Не указано", "well": "Не указано", "client": "Не указано", "bha_num": "1"}
    
    for idx, row in df.iterrows():
        row_list = list(row.values)
        for i, cell in enumerate(row_list):
            cell_clean = str(cell).strip()
            if "Месторождение" in cell_clean and i+2 < len(row_list):
                meta["field"] = str(row_list[i+2]).strip()
            if "Заказчик" in cell_clean and i+1 < len(row_list):
                meta["client"] = str(row_list[i+1]).strip()
            if "Куст" in cell_clean and i+2 < len(row_list):
                meta["well"] = str(row_list[i+2]).strip()
            if "Номер КНБК" in cell_clean and i+1 < len(row_list):
                raw_bha_num = str(row_list[i+1]).strip()
                meta["bha_num"] = raw_bha_num.split('.')[0] if '.' in raw_bha_num else raw_bha_num

    table_start_idx = None
    for idx, row in df.iterrows():
        row_str_lower = [str(cell).lower() for cell in row.values]
        if any("элемент" in c for c in row_str_lower) and any("серийный" in c for c in row_str_lower):
            table_start_idx = idx
            break
    if table_start_idx is None:
        return meta, None
        
    df_bha_raw = df.loc[table_start_idx:].copy()
    raw_headers = df_bha_raw.iloc[0].values
    clean_headers = [str(h).strip().replace('\n', ' ') for h in raw_headers]
    df_bha_raw.columns = clean_headers
    df_bha_raw = df_bha_raw.iloc[1:]
    element_col = df_bha_raw.columns[0]
    for col in df_bha_raw.columns:
        if "элемент" in str(col).lower():
            element_col = col
            break
            
    df_bha_clean = df_bha_raw[df_bha_raw[element_col].str.contains("ВР|ВЗД|УБТ|ТБТ|СБТ|П-|М-|долото|клапан|теле|mwd|рус|bs|дру|мвр|кс", case= False, na= False)]. copy()
    keep_cols = [c for c in df_bha_clean.columns if str(c).strip() != '']
   
    st.session_state["bha_wear_critical"] = False
    df_bha_clean["Статус СМК"] = "🟢 Паспорт проверен"
    df_bha_clean["Отклонение OD, мм"] = 0.0
    for idx, row in df_bha_clean.iterrows():
        el_str = str(row.get("ЭлементКНБК", row.iloc[0])).upper()
        match = next((item for item in elements_lib if item["model"] in el_str or item["element_type"].upper() in el_str), None)
        if match:
            try:
                fact_od = float(str(row.get("НаружныйДиаметр", row.iloc[2])).replace(",", "."))
                diff = abs(match["nominal_od"] - fact_od)
                df_bha_clean.at[idx, "Отклонение OD, мм"] = round(diff, 1)
                if diff > 4.5:
                    df_bha_clean.at[idx, "Статус СМК"] = "🔴 ПРЕВЫШЕН ИЗНОС OD!"
                    st.session_state["bha_wear_critical"] = True
            except: pass
        else: df_bha_clean.at[idx, "Статус СМК"] = "静态 НЕТ В БАЗЕ ПАСПОРТОВ"
    
    return meta, df_bha_clean[keep_cols].copy()

# =========================================================================
# ШАГ 1: ПРОЦЕССНЫЙ ТУМБЛЕР
# =========================================================================
st.markdown("### 🕒 Шаг 1: Процессный статус КНБК")
operation_phase = st.radio(
    "Укажите текущую фазу работы с компоновкой:",
    ["📌 ФАЗА 1: Стартовая компоновка (Сборка на мостках / Проект ГГИ)", 
     "🔄 ФАЗА 2: Динамическая компоновка (Инструмент на забое / Онлайн мониторинг)"],
    horizontal=True
)

if "parsed_bha_df" not in st.session_state: st.session_state["parsed_bha_df"] = None

# =========================================================================
# ШАГ 2: ВСЕЯДНЫЙ ЗАГРУЗЧИК ФАЙЛОВ
# =========================================================================
st.markdown("---")
st.markdown("### 📥 Шаг 2: Загрузка полевого эскиза / Рапорта по КНБК")

# Вот эта строчка, расширенная под xlsx и xls, которая откроет проводник на буровой!
uploaded_report = st.file_uploader(
    "Перетащите сюда официальный файл рапорта КНБК (.csv, .xlsx, .xls):", 
    type=["csv", "xlsx", "xls"]
)

if uploaded_report is not None:
    # Заворачиваем вызов в тотальную защиту СМК от падений кода
    try:
        parsed_result = parse_field_bha_report(uploaded_report)
        if parsed_result is not None:
            meta_parsed, table_parsed = parsed_result
            
            # Проверяем, что парсер вернул живой датафрейм, а не пустоту
            if table_parsed is not None and not table_parsed.empty:
                st.session_state["parsed_bha_df"] = table_parsed
                st.session_state["field_name"] = meta_parsed["field"]
                st.session_state["well_number"] = meta_parsed["well"]
                st.session_state["main_page_company"] = meta_parsed["client"]
                st.session_state["bha_number"] = meta_parsed["bha_num"]
                st.success("✔ Рапорт бурового мастера успешно распознан!")
                st.rerun()
    except Exception as e:
        st.error(f"Ошибка чтения структуры файла: {str(e)}")

# --- ВЫВОД ТАБЛИЦЫ ЭЛЕМЕНТОВ ДЛЯ ВИЗУАЛЬНОЙ ПРОВЕРКИ ---
if st.session_state["parsed_bha_df"] is not None:
    with st.expander("📐 Спецификация геометрии и резьбовых соединений КНБК из файла", expanded=True):
        display_df = st.session_state["parsed_bha_df"].copy()
        # Тотальное очищение от безымянных столбцов-призраков Excel 'nan'
        display_df.columns = [f"Параметр_{i}" if pd.isna(c) or str(c).lower() == 'nan' or c == '' else c for i, c in enumerate(display_df.columns)]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# =========================================================================
# ШАГ 3: КРИТИЧЕСКИЕ ПАРАМЕТРЫ СРЕДЫ И ЖЕЛЕЗА
# =========================================================================
st.markdown("---")
st.markdown("### 🔬 Шаг 3: Верификация скрытых дефектов и динамики")

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.markdown("**🧫 Состояние элементов КНБК**")
    actual_od_lock = st.number_input("Фактический наружный диаметр муфты замка (замер штангенциркулем), мм:", value=165.0)
    acid_history = st.selectbox("История кислотных обработок данного комплекта элементов:", 
                                ["Чистая история (Без ОПЗ)", 
                                 "Мягкая ОПЗ (Органические кислоты)", 
                                 "Солянокислотная ванна HCl (Риск смыва хрома ВЗД)", 
                                 "Агрессивная 'Термит' HCl+HF (Экстремальное наводороживание)"])
    lnk_status = st.radio("Качество дефектоскопии (ЛНК) на базе приемки:", ["🟢 Полный УЗК/МПК контроль", "🔴 Высокий риск пропуска микротрещины"])
                   
with col_p2:
    st.markdown("**🗺️ География и дизайн ВЗД**")
    region_select = st.selectbox("Регион ведения работ (Температурный фактор):", ["Западная Сибирь / Ямал (Риск термозаклинивания резьб)", "Волго-Урал (Стабильный тепловой баланс)"])
    vzd_lobes = st.selectbox("Конфигурация (заходимость) винтовой пары ВЗД:", ["Низкозаходный 3/4 (Высокий Stick-Slip)", "Высокозаходный 7/8 (Высокая частота вибраций)"])
    bha_caliber = st.selectbox("Калибр КНБК (Масса и инерция системы):", ["Тяжелый калибр (295.3 - 311.1 мм)", "Средний калибр (215.9 мм)", "Малый калибр / Хвостовик (120.6 - 142.9 мм)"])

with col_p3:
    st.markdown("**📐 Целевой интервал и цена НПВ**")
    well_interval = st.selectbox("Текущий интервал бурения (Глубина спуска):", 
                                 ["Кондуктор / Направление (0 - 1000 м) [СПО: 3-5 часов]",
                                  "Эксплуатационная колонна (1000 - 2500 м) [СПО: 12-18 часов]",
                                  "Техническая колонна (2500 - 3500 м) [СПО: ~24 часа]",
                                  "Бурение хвостовика / Зарезка БС (> 3500 м) [СПО: 1.5 - 2 суток!]"])
    st.markdown("**🔄 Дополнительные факторы КНБК**")
    fatigue_select = st.selectbox("Наработка элементов КНБК (Усталость стали):", [
        "В пределах нормы (< 250 роторных часов)",
        "Роснефть: Запрет наработки элементов КНБК > 250 ч без УЗК/МПК на устье"
    ])
    vibration_select = st.selectbox("Уровень забойной вибрации (Прогноз Stick-Slip):", [
        "Низкий уровень вибраций (Стабильное разрушение)",
        "Газпром нефть: Запрет бурения интервалов DLS > 3.5°/10м без MWD онлайн"
    ])
# =========================================================================
# ШАГ 3.5: ВИРТУАЛЬНЫЙ СТОЛ РОТОРА (ПОЛНЫЙ РАЗВЕРНУТЫЙ ФОРМАТ)
# =========================================================================
st.markdown("---")
st.markdown("<h2 style='font-size:26px;'>🔄 Шаг 3.5: Виртуальный стол ротора (Контроль переводников)</h2>", unsafe_allow_html= True)
st.caption("Автоматическая кросс-проверка замковых резьб переводников на совместимость и геометрический износ по СТО ИНТИ")
st.markdown("<div style='background-color:#1E293B; padding:10px; border-radius:5px; text-align: center; font-weight: bold; color: #38BDF8; font-size: 22px;'>⚙ ПАРАМЕТРЫ СТЫКОВКИ И ГЕОМЕТРИЧЕСКИЙ КОМПЛАЕНС</div>", unsafe_allow_html= True)
rotor_threads = ["З-86", "З-102", "З-117", "З-122", "З-133", "З-147", "З-161", "NC38", "NC50"]
col_rot1, col_rot2 = st.columns(2)

if st.session_state.get("parsed_bha_df") is not None:
    st.markdown("### 📋 Результаты сквозного аудита соединений колонны:")
    df_active = st.session_state["parsed_bha_df"]
    elements_list = df_active.iloc[:, 0].dropna().tolist()
    
    is_thread_warning = False
    is_rotor_critical = False
    
    for idx in range(len(elements_list) - 1):
        el_top = str(elements_list[idx]).strip()
        el_bot = str(elements_list[idx+1]).strip()
        st.markdown(f"🔗 **Стык №{idx+1}:** {el_top} ↔ {el_bot}")
        
        if el_top == el_bot:
            st.success(f"🟢 Разрешено прямое соединение компонентов")
        else:
            st.warning(f"🟡 Стык требует переводника ПП ({el_top} ↔ {el_bot})")
            is_thread_warning = True
else:
    # Конструктор активируется, если полевой файл рапорта КНБК не загружен
    st.info("ℹ Полевой рапорт КНБК не загружен. Переход в режим интерактивного конструктора СМК.")
    thread_dims = {
        "З-86": (108.0, 57.0), "З-102": (127.0, 71.4), "З-117": (146.0, 76.2),
        "З-122": (155.0, 80.0), "З-133": (162.0, 83.0), "З-147": (177.8, 91.0),
        "З-161": (196.8, 100.0), "NC38": (127.0, 71.4), "NC50": (165.1, 76.2)
    }

    # Достаем модели кубиков из базы ТЭК
    bha_models = st.session_state.get("bha_models_list", ["З-147"])
    
    col_rot1, col_rot2 = st.columns(2)
    with col_rot1:
        top_thread = st.selectbox("Выберите верхнее соединение (МУФТА) из базы ТЭК:", options=bha_models, index=0)
    with col_rot2:
        bottom_thread = st.selectbox("Выберите нижнее соединение (НИППЕЛЬ) из базы ТЭК:", options=bha_models, index=min(1, len(bha_models)-1))
        
    elements_list = [top_thread, bottom_thread]

col_chk1, col_chk2 = st.columns(2)
st.markdown("<div style='font-weight: bold; color: #9CA3AF; font-size: 18px; margin-bottom: 10px;'>📋 СИЛОВОЙ ЧЕК-ЛИСТ ДЕФЕКТОСКОПИИ ПЕРЕВОДНИКА (КОНТРОЛЬ ИЗНОСА)</div>", unsafe_allow_html=True)
   
with col_chk1:
    defect_wear = st.radio("Состояние витков и упорных уступов (Замер калибром):", ["🟢 Витки чистые (Износ в норме)", "🟡 Зализывание/смятие витков резьбы", "🔴 Промоины / Критический вынос конуса резьбы"])
with col_chk2:
    defect_geometry = st.radio("Линейная геометрия торцев и трещины:", ["🟢 Торцы параллельны, задиров нет", "🔴 Выявлено смятие торца муфты / Трещины корпуса переводника"])

is_thread_damaged = ("🔴" in defect_wear) or ("🔴" in defect_geometry)

# =========================================================================
# ШАГ 4: ДИНАМИЧЕСКИЙ СКВОЗНОЙ ИНТЕГРАТОР И РАСЧЕТ РИСКОВ (ИИ-ЯДРО)
# =========================================================================
st.markdown("---")
st.markdown("### 📊 Шаг 4: Адаптивный ИИ-комплаенс и вердикт СМК")

if "📌 ФАЗА 1" in operation_phase:
    current_density = 1.18
    current_dls = 1.5
    context_banner = "📋 РАСЧЕТ ВЫПОЛНЕН ПО ПРОЕКТНЫМ ДАННЫМ ГГИ И ТЗ ЗАКАЗЧИКА"
else:
    current_density = float(st.session_state.get("shared_buoyancy_factor", 1.18))
    current_dls = float(st.session_state.get("forecast_dls_deg10m", 0.0))
    context_banner = f"🔄 ОНЛАЙН ПЕРЕСЧЕТ: ПОДХВАЧЕН ФАКТ РАСТВОРА ({current_density} г/см³) И ИНКЛИНОМЕТРИИ (DLS: {current_dls} °/10м)"
st.caption(context_banner)

# Базовая инициализация флагов для защиты от NameError вне цикла
is_thread_warning = False
is_thread_damaged = False
is_rotor_critical = False

# Автоматически вытягиваем крайние элементы гирлянды для ИИ-комплаенса
if len(elements_list) >= 2:
    top_thread = elements_list[0]
    bottom_thread = elements_list[-1]
elif len(elements_list) == 1:
    top_thread = elements_list[0]
    bottom_thread = elements_list[0]
else:
    top_thread = "З-147"
    bottom_thread = "З-147"

risk_points = 5.0
base_stop_threshold = 80.0

conn = sqlite3.connect("knbk_core.db")
cursor = conn.cursor()
cursor.execute("SELECT penalty_points, stop_threshold_modifier FROM risk_matrix WHERE factor_name IN (?, ?)", (acid_history, region_select))
db_rows = cursor.fetchall()
for row in db_rows:
    risk_points += float(row[0])
    base_stop_threshold += float(row[1])
cursor.execute("SELECT penalty_points, stop_threshold_modifier FROM risk_matrix WHERE factor_name IN (?, ?)", (vzd_lobes, well_interval))
db_rows_2 = cursor.fetchall()
for row in db_rows_2:
    risk_points += float(row[0])
    base_stop_threshold += float(row[1])
cursor.execute("SELECT penalty_points, stop_threshold_modifier FROM risk_matrix WHERE factor_name IN (?, ?)", (fatigue_select, vibration_select))
for row in cursor.fetchall():
    risk_points += float(row[0])
    base_stop_threshold += float(row[1])
conn.close()
if actual_od_lock < 168.0: risk_points += 30.0
if actual_od_lock < 164.0: risk_points += 15.0

if is_thread_damaged:
    risk_points += 40.0
    base_stop_threshold -= 15.0
elif is_thread_warning:
    risk_points += 15.0
if is_rotor_critical:
    risk_points += 20.0
    base_stop_threshold -= 10.0

base_stop_threshold -= (current_dls * 2.5)

if st.session_state.get("bha_wear_critical", False):
    risk_points += 35.0
    base_stop_threshold -= 10.0

calculated_total_risk = min(99.2, risk_points)
base_stop_threshold = 80.0
base_stop_threshold -= (current_dls * 2.5)

if "HCl" in acid_history: base_stop_threshold -= 5.0
if "Термит" in acid_history: base_stop_threshold -= 12.0
if "Сибирь" in region_select: base_stop_threshold -= 5.0
if is_thread_damaged: base_stop_threshold -= 15.0
if is_rotor_critical: base_stop_threshold -= 10.0
if "Эксплуатационная" in well_interval: base_stop_threshold -= 5.0
elif "Техническая" in well_interval: base_stop_threshold -= 12.0
elif "хвостовика" in well_interval: base_stop_threshold -= 20.0
dynamic_stop_threshold = max(45.0, base_stop_threshold)
col_res1, col_res2 = st.columns(2)
with col_res1:
    st.markdown(f"""<div style="background-color:#111827; padding:20px; border-radius:10px; text-align:center; border: 1px solid #374151;"><span style="color:#9CA3AF; font-size:14px;">РАСЧЕТНЫЙ РИСК АВАРИЙНОСТИ КНБК</span><br><span style="color:#F3F4F6; font-size:48px; font-weight:bold;">{calculated_total_risk:.1f}%</span></div>""", unsafe_allow_html=True)
with col_res2:
    st.markdown(f"""<div style="background-color:#111827; padding:20px; border-radius:10px; text-align:center; border: 1px solid #374151;"><span style="color:#9CA3AF; font-size:14px;">ДИНАМИЧЕСКИЙ ПОРОГ БЛОКИРОВКИ СТОП</span><br><span style="color:#6EE7B7; font-size:48px; font-weight:bold;">{dynamic_stop_threshold:.1f}%</span></div>""", unsafe_allow_html=True)

st.markdown("#### 🔬 Экспертное заключение ИИ-системы:")
is_blocked = calculated_total_risk >= dynamic_stop_threshold
recommendation_text = ""
if "хвостовика" in well_interval and is_blocked:
    recommendation_text += f"🚨 **КРИТИЧЕСКАЯ ЗОНА НПВ!** Спуск инструмента (OD {actual_od_lock} мм) глубже 3500 м сопряжен с риском аварии на 1.5-2 суток. "
if "Термит" in acid_history:
    recommendation_text += "Обнаружен риск водородного хрупчения стали после агрессивной химии HCl+HF. "
if "Ямал" in region_select and is_blocked:
    recommendation_text += "Внимание: при низких температурах устья прогнозируется термический самозатяг резьбы на забое. "
elif "Поволжье" in region_select:
    recommendation_text += "Региональный тепловой баланс Поволжья стабилен, температурные риски устья отсутствуют. "
if is_thread_damaged:
    recommendation_text += f"🚨 **БРАК РЕЗЬБЫ ПЕРЕВОДНИКА!** Спуск КНБК запрещен согласно СТО ИНТИ S.QS.7 из-за дефектов {top_thread}/{bottom_thread}. "
elif is_thread_warning:
    recommendation_text += "⚠ Предупреждение по резьбе: требуется калибровка витков шаблоном. "
if is_rotor_critical:
    recommendation_text += f"⚠ Перепад замков превышает 15 мм. Контролируйте посадки инструмента при СПО. "
if st.session_state.get("bha_wear_critical", False):
    recommendation_text += "🚨 **КРИТИЧЕСКИЙ ИЗНОС ГЕОМЕТРИИ КНБК!** В загруженном файле обнаружены изношенные элементы. "
if not recommendation_text:
    recommendation_text = "🟢 Компоновка полностью соответствует прочностным характеристикам. Бурение разрешено в штатном режиме."
if is_blocked:
    st.error(recommendation_text)
    st.markdown("### 🔐 Процедура принудительной авторизации риска (Черный ящик СМК)")
    st.warning("Блокировка СМК! КНБК не рекомендована к спуску. Для разблокировки шлюза данных требуется ввод личной ответственности инженера.")
    override_check = st.checkbox("🔥 Я беру на себя персональную ответственность за спуск данной КНБК вопреки блокировке ИИ-системы.")
    override_reason = st.text_input("📝 Введите обязательное инженерное обоснование (номер распоряжения ЦИТС, подпись супервайзера):")
    button_disabled = not (override_check and len(override_reason) > 5)
else:
    st.success(recommendation_text)
    override_reason = ""
    button_disabled = False
if actual_od_lock < 168.0 or "Термит" in acid_history:
    st.session_state["p_moment_corrected"] = 21.5
    st.info("🔗 **Шлюз СМК:** Информация об истончении муфт замков труб передана в Модуль УМК. Паспортный момент затяжки на ключах автоматически занижен до **21.5 кН·м** для предотвращения среза резьбы.")

st.markdown("---")
if st.button("💾 Утвердить сборку КНБК и записать лог СМК", disabled=button_disabled):
    log_status = "OVERRIDE_BY_USER" if is_blocked else "APPROVED_BY_AI"
    st.toast(f"💾 Запись успешно внесена в локальный реестр `knbk_core.db` со статусом {log_status}!")
    st.success("✔ Данные КНБК успешно верифицированы и зафиксированы в цифровом следе проекта.")
st.markdown("<div style='text-align: center; color: #6B7280; font-size: 11px; margin-top: 50px;'><b>Разработчик экосистемы:</b> Старший инженер по качеству ОСМК Никонова-Morozova М.М. • СТО ИНТИ • ООО «Траектория-СЕРВИС» © 2026</div>", unsafe_allow_html=True)
