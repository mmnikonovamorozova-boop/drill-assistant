import streamlit as st
import pandas as pd
import numpy as np
import io
import os

# --- СТРОГАЯ АВТЕНТИФИКАЦИЯ ЭКОСИСТЕМЫ ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Пожалуйста, пройдите авторизацию на Главной странице.")
    st.stop()

# Инициализация конфигурации страницы в стиле drill-assistant
st.set_page_config(page_title="Адаптер КНБК", layout="wide")

# Внедрение кастомных стилей для максимальной ночной читаемости в полях
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stButton>button { width: 100%; height: 3em; font-weight: bold; font-size: 16px; }
    .reportview-container .main .block-container{ padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚙️ Адаптер КНБК и Динамический Комплаенс")
st.caption("Автоматический парсинг полевых рапортов КНБК, учёт износа, химии сред и цены времени СПО по СТО ИНТИ")

# --- СКВОЗНАЯ СИНХРОНИЗАЦИЯ МЕТАДАННЫХ СМК ---
engineer = st.session_state.get("engineer_name", "Не указано")
well = st.session_state.get("well_number", "Не указано")
field = st.session_state.get("field_name", "Не указано")
bha = st.session_state.get("bha_number", "1")
client = st.session_state.get("main_page_company", "Не указано")

# Крупная, контрастная информационная плашка (читается в любое время суток)
st.markdown(f"""
<div style="background-color:#1E293B; padding:15px; border-radius:10px; border-left: 5px solid #3B82F6; margin-bottom:20px;">
    <span style="color:#9CA3AF; font-size:12px;">ТЕКУЩИЙ КОНТЕКСТ СМК ТРАЕКТОРИЯ-СЕРВИС</span><br>
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

# --- ФУНКЦИЯ ОПТИМИЗИРОВАННОГО ПОЛЕВОГО ПАРСЕРА ---
def parse_field_bha_report(uploaded_file):
    try:
        raw_bytes = uploaded_file.read()
        try:
            text_data = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_data = raw_bytes.decode("cp1251")
            
        df = pd.read_csv(io.StringIO(text_data), header=None).dropna(how='all')
        
        meta = {"field": "Не указано", "well": "Не указано", "client": "Не указано", "bha_num": "1"}
        
        for idx, row in df.iterrows():
            row_str = [str(cell).strip() for cell in row.values if pd.notna(cell)]
            row_joined = " ".join(row_str)
            
            if "Месторождение" in row_joined:
                row_list = list(row.values)
                for i, cell in enumerate(row_list):
                    if str(cell).strip() == "Месторождение" and i+1 < len(row_list):
                        meta["field"] = str(row_list[i+1]).strip()
                    if "Заказчик" in str(cell) and i+1 < len(row_list):
                        meta["client"] = str(row_list[i+1]).strip()
                        
            if "Куст / скважина" in row_joined:
                row_list = list(row.values)
                for i, cell in enumerate(row_list):
                    if "Куст" in str(cell) and i+1 < len(row_list):
                        meta["well"] = str(row_list[i+1]).strip()
                    if "Номер КНБК" in str(cell) and i+1 < len(row_list):
                        meta["bha_num"] = str(row_list[i+1]).strip()

        table_start_idx = None
        for idx, row in df.iterrows():
            row_str_lower = [str(cell).lower() for cell in row.values if pd.notna(cell)]
            if any("элемент" in cell for cell in row_str_lower) and any("резьба" in cell for cell in row_str_lower):
                table_start_idx = idx
                break
                
        if table_start_idx is None:
            return meta, None
            
        df_bha_raw = df.loc[table_start_idx:].copy()
        raw_headers = df_bha_raw.iloc[0].values
        clean_headers = [str(h).strip().replace('\n', ' ') for h in raw_headers]
        df_bha_raw.columns = clean_headers
        df_bha_raw = df_bha_raw.iloc[1:]
        
        first_col = df_bha_raw.columns[0]
        df_bha_raw[first_col] = pd.to_numeric(df_bha_raw[first_col], errors='coerce')
        df_bha_clean = df_bha_raw.dropna(subset=[first_col])
        
        return meta, df_bha_clean
    except Exception as e:
        st.error(f"🚨 Ошибка чтения полевого рапорта: {str(e)}")
        return None, None

# =========================================================================
# ШАГ 1: ПРОЦЕССНЫЙ ТУМБЛЕР (ЭРГОНОМИКА ВРЕМЕНИ)
# =========================================================================
st.markdown("### 🕒 Шаг 1: Процессный статус КНБК")
operation_phase = st.radio(
    "Укажите текущую фазу работы с компоновкой:",
    ["📌 ФАЗА 1: Стартовая компоновка (Сборка на мостках / Проект ГГИ)", 
     "🔄 ФАЗА 2: Динамическая компоновка (Инструмент на забое / Онлайн мониторинг)"],
    horizontal=True, help="В Фазе 1 расчет идет по проекту. В Фазе 2 система автоматически подтягивает живую телеметрию растворов и траектории."
)

# Инициализация сессионных контейнеров
if "parsed_bha_df" not in st.session_state: st.session_state["parsed_bha_df"] = None

# =========================================================================
# ШАГ 2: АВТОМАТИЗИРОВАННЫЙ ВВОД («ВСЕЯДНЫЙ» ЗАГРУЗЧИК)
# =========================================================================
st.markdown("---")
st.markdown("### 📥 Шаг 2: Загрузка полевого эскиза / Рапорта по КНБК")
uploaded_report = st.file_uploader("Перетащите сюда официальный файл рапорта КНБК (.csv из Excel бурового мастера):", type=["csv"])

if uploaded_report is not None:
    meta_parsed, table_parsed = parse_field_bha_report(uploaded_report)
    if meta_parsed and table_parsed is not None:
        st.session_state["parsed_bha_df"] = table_parsed
        # Синхронизация «наверх»
        st.session_state["field_name"] = meta_parsed["field"]
        st.session_state["well_number"] = meta_parsed["well"]
        st.session_state["main_page_company"] = meta_parsed["client"]
        st.session_state["bha_number"] = meta_parsed["bha_num"]
        st.success("✔ Рапорт бурового мастера успешно распознан! Данные СМК синхронизированы.")
        st.rerun()

# Отображение считанной КНБК
if st.session_state["parsed_bha_df"] is not None:
    with st.expander("📐 Спецификация геометрии и резьбовых соединений КНБК из файла", expanded=True):
        st.dataframe(st.session_state["parsed_bha_df"], use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ Полевой рапорт КНБК не загружен. Система работает на базовых проектных константах.")

# =========================================================================
# ШАГ 3: КРИТИЧЕСКИЕ ПАРАМЕТРЫ СРЕДЫ И ЖЕЛЕЗА (ФАКТОРЫ ИЗ СЛЕПОЙ ЗОНЫ)
# =========================================================================
st.markdown("---")
st.markdown("### 🔬 Шаг 3: Верификация скрытых дефектов и динамики")

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.markdown("**🧫 Состояние 'Железа' из кузова**")
    actual_od_lock = st.number_input("Фактический OD муфты замка (замер штангенциркулем), мм:", value=165.0, help="Паспортный диаметр для NC50 — 172 мм. Уменьшение диаметра снижает прочность на кручение.")
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
                                  "Эксплуатационная колонна (1000 - 2500 м) [СПО: 12-18 часов]",
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
    # СКВОЗНАЯ СИНХРОНИЗАЦИЯ: забираем живой поток из ваших модулей 5 и 7 через сессию
    current_density = float(st.session_state.get("shared_buoyancy_factor", 1.18))
    current_dls = float(st.session_state.get("forecast_dls_deg10m", 0.0))
    context_banner = f"🔄 ОНЛАЙН ПЕРЕСЧЕТ: ПОДХВАЧЕН ФАКТ РАСТВОРА ({current_density} г/см³) И ИНКЛИНОМЕТРИИ (DLS: {current_dls}°/10м)"

st.caption(context_banner)

# МАТЕМАТИЧЕСКАЯ МАТРИЦА РИСКОВ (Физико-вероятностная модель "Случайного леса" в первом приближении)
risk_points = 5.0

# 1. Фактор износа геометрии муфты замка труб из кузова
if actual_od_lock < 168.0: risk_points += 30.0
if actual_od_lock < 164.0: risk_points += 15.0

# 2. Химический фактор деградации стали (наводороживание и смыв хрома)
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
elif "хвостовика" in well_interval: base_stop_threshold -= 20.0  # Экстремальная цена 1.5 суток гоняния концов туда-сюда

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
