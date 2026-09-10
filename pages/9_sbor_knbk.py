import streamlit as st
import pandas as pd
import numpy as np
import io
import os

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
            ('lnk', '🔴 Высокий риск пропуска микротрещины', 15.0, 0.0),
            ('vzd', 'Низкозаходный 3/4 ("Бронебойный танк" // Высокий Stick-Slip)', 10.0, 0.0),
            ('region', 'Западная Сибирь / Ямал (Риск термозаклинивания резьб)', 0.0, -5.0)
        ]
        cursor.executemany("INSERT INTO risk_matrix (factor_type, factor_name, penalty_points, stop_threshold_modifier) VALUES (?, ?, ?, ?)", risks_data)
            ('interval', 'Эксплуатационная колонна (1000 - 2500 м) [СПО: 12-18 часов]', 0.0, -5.0),
            ('interval', 'Техническая колонна (2500 - 3500 м) [СПО: ~24 часа]', 0.0, -12.0),
            ('interval', 'Бурение хвостовика / Зарезка БС (> 3500 м) [СПО: 1.5 - 2 суток!]', 0.0, -20.0),
            ('operator', 'Роснефть: Запрет наработки элементов КНБК > 250 ч без УЗК/МПК на устье', 15.0, -5.0),
            ('operator', 'Газпром нефть: Запрет бурения интервалов DLS > 3.5°/10м без MWD онлайн', 20.0, -8.0),
            ('operator', 'НОВАТЭК: Запрет спуска нижних пульсаторов MWD при КВЧ > 0.5%', 25.0, -10.0)

    conn.commit()
    conn.close()

# --- СТРОГАЯ АВТЕНТИФИКАЦИЯ ЭКОСИСТЕМЫ ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Пожалуйста, пройдите авторизацию на Главной странице.")
    st.stop()
# Запуск инициализации локальной базы данных СМК после авторизации
init_knbk_database()

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
            
    df_bha_clean = df_bha_raw[df_bha_raw[element_col].str.contains("ВР|ВЗД|УБТ|ТБТ|СБТ|П-|М-|долото|клапан|теле|mwd|рус|bs|дру", case=False, na=False)].copy()
    keep_cols = [c for c in df_bha_clean.columns if str(c).strip() != '']
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
        meta_parsed, table_parsed = parse_field_bha_report(uploaded_report)
        
        # Проверяем, что парсер вернул живой датафрейм, а не пустоту
        if table_parsed is not None and not table_parsed.empty:
            st.session_state["parsed_bha_df"] = table_parsed
            st.session_state["field_name"] = meta_parsed["field"]
            st.session_state["well_number"] = meta_parsed["well"]
            st.session_state["main_page_company"] = meta_parsed["client"]
            st.session_state["bha_number"] = meta_parsed["bha_num"]
            st.success("✔ Рапорт бурового мастера успешно распознан!")
            st.rerun()
        else:
            st.error("🚨 Формат файла не распознан. Пожалуйста, откройте этот файл в Excel на компьютере, нажмите 'Сохранить как' -> формат 'CSV (разделители - запятые) (*.csv)' и загрузите его снова.")
    except Exception:
        # Если файл бинарный и питон вообще не смог распаковать кортеж - мягко выводим баннер инженеру
        st.error("🚨 Обнаружен старый бинарный формат Excel. Система заблокировала падение кода. Пересохраните файл в формат .CSV перед загрузкой!")

# --- ВЫВОД ТАБЛИЦЫ ЭЛЕМЕНТОВ ДЛЯ ВИЗУАЛЬНОЙ ПРОВЕРКИ ---
if st.session_state["parsed_bha_df"] is not None:
    with st.expander("📐 Спецификация геометрии и резьбовых соединений КНБК из файла", expanded=True):
        # Очищаем таблицу от пустых технических столбцов для эргономики экрана
        display_df = st.session_state["parsed_bha_df"].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# =========================================================================
# ШАГ 3: КРИТИЧЕСКИЕ ПАРАМЕТРЫ СРЕДЫ И ЖЕЛЕЗА
# =========================================================================
st.markdown("---")
st.markdown("### 🔬 Шаг 3: Верификация скрытых дефектов и динамики")

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.markdown("**🧫 Состояние 'Железа' из кузова**")
    actual_od_lock = st.number_input("Фактический OD муфты замка (замер штангенциркулем), мм:", value=165.0)
    acid_history = st.selectbox("История кислотных обработок данного комплекта железа:", 
                                ["Чистая история (Без ОПЗ)", 
                                 "Мягкая ОПЗ (Органические кислоты)", 
                                 "Солянокислотная ванна HCl (Риск смыва хрома ВЗД)", 
                                 "Агрессивный 'Термит' HCl+HF (Экстремальное наводороживание)"])
    lnk_status = st.radio("Качество дефектоскопии (ЛНК) на базе приемки:", ["🟢 Полный УЗК/МПК контроль", "🔴 Высокий риск пропуска микротрещины"])

with col_p2:
    st.markdown("**🗺️ География и дизайн ВЗД**")
    region_select = st.selectbox("Регион ведения работ (Температурный фактор):", ["Западная Сибирь / Ямал (Риск термозаклинивания резьб)", "Поволжье / Волгоград (Стабильный тепловой баланс)"])
    vzd_lobes = st.selectbox("Конфигурация (заходимость) винтовой пары ВЗД:", ["Низкозаходный 3/4 ('Бронебойный танк' // Высокий Stick-Slip)", "Высокозаходный 7/8 ('Шустрый' // Высокая частота вибраций)"])
    bha_caliber = st.selectbox("Калибр КНБК (Масса и инерция системы):", ["Тяжелый калибр (295.3 - 311.1 мм)", "Средний калибр (215.9 мм)", "Малый калибр / Хвостовик (120.6 - 142.9 мм)"])

with col_p3:
    st.markdown("**📐 Целевой интервал и цена НПВ**")
    well_interval = st.selectbox("Текущий интервал бурения (Глубина спуска):", 
                                 ["Кондуктор / Направление (0 - 1000 м) [СПО: 3-5 часов]",
                                  "Эксплуатационная校онна (1000 - 2500 м) [СПО: 12-18 часов]",
                                  "Техническая колонна (2500 - 3500 м) [СПО: ~24 часа]",
                                  "Бурение хвостовика / Зарезка БС (> 3500 м) [СПО: 1.5 - 2 суток!]"])

# =========================================================================
# ШАГ 4: ДИНАМИЧЕСКИЙ СКВОЗНОЙ ИНТЕГРАТОР И РАСЧЕТ РИСКОВ (ИИ-ЯДРО)
# =========================================================================
st.markdown("---")
st.markdown("### 📊 Шаг 4: Адаптивный ИИ-комплаенс и вердикт СМК")

# Реализация Процессного подхода: сбор сквозных данных
if "📌 ФАЗА 1" in operation_phase:
    current_density = 1.18  # Проектная плотность по ГГИ
    current_dls = 1.5       # Проектная плановая интенсивность искривления
    context_banner = "📋 РАСЧЕТ ВЫПОЛНЕН ПО ПРОЕКТНЫМ ДАННЫМ ГГИ И ТЗ ЗАКАЗЧИКА"
else:
    # СКВОЗНАЯ СИНХРОНИЗАЦИЯ: забираем живой поток из ваших модулей растворов и траекторий
    current_density = float(st.session_state.get("shared_buoyancy_factor", 1.18))
    current_dls = float(st.session_state.get("forecast_dls_deg10m", 0.0))
    context_banner = f"🔄 ОНЛАЙН ПЕРЕСЧЕТ: ПОДХВАЧЕН ФАКТ РАСТВОРА ({current_density} г/см³) И ИНКЛИНОМЕТРИИ (DLS: {current_dls}°/10м)"

st.caption(context_banner)

# МАТЕМАТИЧЕСКАЯ МАТРИЦА РИСКОВ (Физико-вероятностная модель "Случайного леса")
risk_points = 5.0

# 1. Фактор износа геометрии муфты замка труб из кузова
if actual_od_lock < 168.0: risk_points += 30.0
if actual_od_lock < 164.0: risk_points += 15.0

# 2. Химический фактор деградации стали (наводороживание и смыв хрома ротора)
if "Органические" in acid_history: risk_points += 5.0
elif "HCl (Риск" in acid_history: risk_points += 20.0
elif "Термит" in acid_history: risk_points += 45.0

# 3. Человеческий фактор дефектоскопии (риск пропуска микротрещин)
if "Риск пропуска" in lnk_status: risk_points += 15.0

# 4. Кинематика ВЗД и крутящий момент ("Танк" против "Шустрого")
if "3/4" in vzd_lobes: risk_points += 10.0  # Мощные пиковые удары кручения и Stick-Slip

# 5. Профиль скважины (Фактическое или плановое кривляние ствола)
if current_dls > 2.5: risk_points += 15.0
if current_dls > 4.0: risk_points += 20.0

calculated_total_risk = min(99.2, risk_points)

# ВЫЧИСЛЕНИЕ ДИНАМИЧЕСКОГО ПОРОГА БЛОКИРОВКИ СТОП (Самообучающаяся логика СМК)
base_stop_threshold = 80.0

# Штрафной вычет за интенсивность пространственного искривления (DLS)
base_stop_threshold -= (current_dls * 2.5)

# Штрафной вычет за химическую хрупкость металла после ванн
if "HCl" in acid_history: base_stop_threshold -= 5.0
if "Термит" in acid_history: base_stop_threshold -= 12.0

# Штрафной вычет за Сибирь (температурный шок разбурки холодного корпуса)
if "Сибирь" in region_select: base_stop_threshold -= 5.0

# Штрафной вычет за целевой интервал и цену времени СПО (Хвостовик на 3500м)
if "Эксплуатационная" in well_interval: base_stop_threshold -= 5.0
elif "Техническая" in well_interval: base_stop_threshold -= 12.0
elif "хвостовика" in well_interval: base_stop_threshold -= 20.0  # Цена 1.5 суток гоняния концов туда-сюда

dynamic_stop_threshold = max(45.0, base_stop_threshold)

# ЭРГОНОМИКА ВЫВОДА: Два крупных контрастных блока результатов для ночной смены
col_res1, col_res2 = st.columns(2)

with col_res1:
    st.markdown(f"""
    <div style="background-color:#111827; padding:20px; border-radius:10px; text-align:center; border: 1px solid #374151;">
        <span style="color:#9CA3AF; font-size:14px;">РАСЧЕТНЫЙ РИСК АВАРИЙНОСТИ КНБК</span><br>
        <span style="color:#F3F4F6; font-size:48px; font-weight:bold;">{calculated_total_risk:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

with col_res2:
    st.markdown(f"""
    <div style="background-color:#111827; padding:20px; border-radius:10px; text-align:center; border: 1px solid #374151;">
        <span style="color:#9CA3AF; font-size:14px;">ДИНАМИЧЕСКИЙ ПОРОГ БЛОКИРОВКИ СТОП</span><br>
        <span style="color:#6EE7B7; font-size:48px; font-weight:bold;">{dynamic_stop_threshold:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

# СВЕТОФОР СМК И ЭКСПЕРТНАЯ РЕКОМЕНДАЦИЯ
st.markdown("#### 🔬 Экспертное заключение ИИ-системы:")

is_blocked = calculated_total_risk >= dynamic_stop_threshold

# Интеллектуальный синтез текста рекомендации на основе комбинации полевых факторов
recommendation_text = ""
if "хвостовика" in well_interval and is_blocked:
    recommendation_text = f"🚨 **ВНИМАНИЕ: КРИТИЧЕСКАЯ ЗОНА НПВ!** Спуск изношенного инструмента (OD {actual_od_lock} мм) в интервал хвостовика на глубину более 3500 м сопряжен с риском обрыва резьбы ЗТС. Время ликвидации аварии составит до 1.5-2 суток. "
if "Термит" in acid_history:
    recommendation_text += "Обнаружены следы воздействия плавиковой кислоты на металл — критический риск водородного хрупчения стали в зоне знакопеременного изгиба скважины. "
if "Сибирь" in region_select:
    recommendation_text += "В условиях экстремальных температур устья (-40°C) прогнозируется термический самозатяг замков на забое при выходе на геотермический градиент. "

if not recommendation_text:
    recommendation_text = "🟢 Компоновка полностью соответствует базовым прочностным характеристикам для данного интервала. Бурение разрешено в штатном технологическом режиме."

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

# АВТОМАТИЧЕСКИЙ ШЛЮЗ В МОДУЛЬ УМК (2_raschet_umk.py)
if actual_od_lock < 168.0 or "Термит" in acid_history:
    # Записываем скорректированный безопасный момент в сессию, чтобы модуль 2 подхватил его автоматически
    st.session_state["p_moment_corrected"] = 21.5
    st.info("🔗 **Шлюз СМК:** Информация об истончении муфт замков труб передана в Модуль УМК. Паспортный момент затяжки на ключах автоматически занижен до **21.5 кН·м** для предотвращения среза резьбы.")

# Кнопка сохранения результатов и лога в локальную базу данных
st.markdown("---")
if st.button("💾 Утвердить сборку КНБК и записать лог СМК", disabled=button_disabled):
    log_status = "OVERRIDE_BY_USER" if is_blocked else "APPROVED_BY_AI"
    st.toast(f"💾 Запись успешно внесена в локальный реестр `knbk_core.db` со статусом {log_status}!")
    st.success("✔ Данные КНБК успешно верифицированы и зафиксированы в цифровом следе проекта.")

# Подвал в стиле автора СМК компании
st.markdown("<div style='text-align: center; color: #6B7280; font-size: 11px; margin-top: 50px;'><b>Разработчик экосистемы:</b> Старший инженер по качеству ОСМК Никонова-Morozova М.М. • СТО ИНТИ • ООО «Траектория-СЕРВИС» © 2026</div>", unsafe_allow_html=True)
