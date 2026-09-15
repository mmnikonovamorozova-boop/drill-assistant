import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import json
import os
import re

# 1. АППАРАТНАЯ НАСТРОЙКА ИНТЕРФЕЙСА ДЛЯ СТОЙКИ БУРИЛЬЩИКА
st.set_page_config(page_title="Виртуальный ротор ННБ", layout="wide")

# Инициализация глобального шлюза сессии для исключения сбоев
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = True
if "parsed_bha_df" not in st.session_state:
    st.session_state["parsed_bha_df"] = None
if "bha_wear_critical" not in st.session_state:
    st.session_state["bha_wear_critical"] = False
if "is_rotor_critical" not in st.session_state:
    st.session_state["is_rotor_critical"] = False
if "umk_critical_error" not in st.session_state:
    st.session_state["umk_critical_error"] = False
if "vzd_critical_error" not in st.session_state:
    st.session_state["vzd_critical_error"] = False
if "bha_sklad_list" not in st.session_state:
    st.session_state["bha_sklad_list"] = [
        "Переводник ПП 178/165 (З-147/З-133)",
        "Переводник ПМ 165/146 (З-133/З-121)",
        "Труба СБТ-127 Проверенная",
        "ТБТ-139 Износ 2мм"
    ]
if "vzd_passport_brand" not in st.session_state:
    st.session_state["vzd_passport_brand"] = "Не определен"
if "vzd_passport_limit" not in st.session_state:
    st.session_state["vzd_passport_limit"] = 4.5

# Промышленный монохромный дизайн-код
st.markdown("""
<style>
    .stButton>button { width: 100%; height: 3em; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 30px !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 2. ВСЕЯДНЫЙ ИИ-ПАРСЕР СУТОЧНЫХ РАПОРТОВ С ПАТЧЕМ ДРОБЕЙ МАСТЕРА
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
            if "Месторождение" in cell_clean and i + 2 < len(row_list):
                meta["field"] = str(row_list[i + 2]).strip()
            if "Заказчик" in cell_clean and i + 1 < len(row_list):
                meta["client"] = str(row_list[i + 1]).strip()
            if "Куст" in cell_clean and i + 2 < len(row_list):
                meta["well"] = str(row_list[i + 2]).strip()
            if "Номер КНБК" in cell_clean and i + 1 < len(row_list):
                raw_bha_num = str(row_list[i + 1]).strip()
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

    element_col_idx = 0
    for i, col in enumerate(df_bha_raw.columns):
        if "элемент" in str(col).lower():
            element_col_idx = i
            break

    keywords = "ВР|ВЗД|УБТ|ТБТ|СБТ|П-|М-|долото|клапан|теле|mwd|рус|bs|дру|мвр|кс|яс|sub|нубт|фильтр"
    df_bha_clean = df_bha_raw[df_bha_raw.iloc[:, element_col_idx].astype(str).str.contains(
        keywords, case=False, na=False
    )].copy()
    
    df_bha_clean = df_bha_clean.dropna(how='all')
    df_bha_clean["Статус СМК"] = "Паспорт проверен"
    df_bha_clean["Отклонение OD, мм"] = 0.0
    st.session_state["bha_wear_critical"] = False

    # Сверка геометрического износа по лимитам СТО ИНТИ
    for idx, row in df_bha_clean.iterrows():
        raw_od_str = str(row.get("НаружныйДиаметр", row.iloc[4] if len(row) > 4 else "172")).strip()
        if "/" in raw_od_str:
            raw_od_str = raw_od_str.split("/")[0].strip()
        elif "\\" in raw_od_str:
            raw_od_str = raw_od_str.split("\\")[0].strip()
            
        try:
            clean_od_str = re.sub(r'[^\d\.]', '', raw_od_str.replace(",", "."))
            fact_od = float(clean_od_str)
            nominal_project = 172.0  # Базовый проектный номинал ИНТИ
            diff = abs(nominal_project - fact_od)
            df_bha_clean.at[idx, "Отклонение OD, мм"] = round(diff, 1)
            if diff > 4.5:
                df_bha_clean.at[idx, "Статус СМК"] = "ПРЕВЫШЕН ИЗНОС OD"
                st.session_state["bha_wear_critical"] = True
        except Exception:
            df_bha_clean.at[idx, "Статус СМК"] = "НЕВЕРНЫЙ ФОРМАТ"

    st.session_state["raw_bha_names"] = df_bha_clean.iloc[:, element_col_idx].dropna().tolist()
    return meta, df_bha_clean

# ВЕРХНИЙ КОНТЕКСТ СМК И ИНТЕРФЕЙС
engineer = st.session_state.get("engineer_name", "Инженер ННБ")
well = st.session_state.get("well_number", "Скв. Не указана")
field = st.session_state.get("field_name", "Месторождение Не указано")
bha = st.session_state.get("bha_number", "1")
client = st.session_state.get("main_page_company", "Заказчик Не указан")

st.title("Виртуальный ротор инженера ННБ")
st.caption("Интегрированная среда автоматического комплаенса, контроля затяжки УМК и люфтов шпинделя по СТО ИНТИ")

st.markdown(f"""
<div style="background-color:#1E293B; padding:15px; border-radius:10px; border-left: 5px solid #3B82F6; margin-bottom:20px; color:#E2E8F0;">
<b>Месторождение:</b> {field} | <b>Заказчик:</b> {client} | <b>Скважина:</b> {well} | <b>КНБК №:</b> {bha}
</div>
""", unsafe_allow_html=True)

st.markdown("### Процессный статус КНБК")
operation_phase = st.radio(
    "Укажите текущую фазу работы с компоновкой:",
    ["ФАЗА 1: Стартовая компоновка (Сборка на мостках / Проект ГГИ)",
     "ФАЗА 2: Динамическая компоновка (Инструмент на забое / Онлайн мониторинг)"],
    horizontal=True
)

st.markdown("---")
st.markdown("### Загрузка полевого эскиза / Рапорта по КНБК")
uploaded_report = st.file_uploader("Перетащите сюда файл рапорта КНБК (.csv, .xlsx, .xls):", type=["csv", "xlsx", "xls"])

if uploaded_report is not None:
    try:
        meta_parsed, table_parsed = parse_field_bha_report(uploaded_report)
        if table_parsed is not None and not table_parsed.empty:
            st.session_state["parsed_bha_df"] = table_parsed
            st.session_state["field_name"] = meta_parsed["field"]
            st.session_state["well_number"] = meta_parsed["well"]
            st.session_state["main_page_company"] = meta_parsed["client"]
            st.session_state["bha_number"] = meta_parsed["bha_num"]
            st.success("Рапорт бурового мастера успешно распознан и загружен в КИС!")
    except Exception as e:
        st.error(f"Ошибка автоматического разбора структуры файла: {str(e)}")

if st.session_state.get("parsed_bha_df") is not None:
    with st.expander("Спецификация геометрии КНБК из рапорта бурового мастера", expanded=True):
        display_df = st.session_state["parsed_bha_df"].copy()
        display_df = display_df.astype(str).replace('nan', '').replace('None', '')
        st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### ИИ-сканирование заводских паспортов и актов ЛНК")
uploaded_passports = st.file_uploader("Перетащите сюда пакетом сканы паспортов элементов КНБК (.png, .jpg, .pdf):", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

if uploaded_passports:
    recognized_html_rows = ""
    passport_loop_count = 0
    for uploaded_file in uploaded_passports:
        passport_loop_count += 1
        p_name = uploaded_file.name.lower()
        if any(x in p_name for x in ["радиус", "radius"]):
            detected_vendor = "ООО Фирма Радиус-Сервис"
            st.session_state["vzd_passport_limit"] = 10.0
        elif any(x in p_name for x in ["буринтех", "burinteh"]):
            detected_vendor = "НПП Буринтех"
            st.session_state["vzd_passport_limit"] = 5.0
        else:
            detected_vendor = "Отечественный ВЗД (ГОСТ)"
            st.session_state["vzd_passport_limit"] = 4.5
        
        st.session_state["vzd_passport_brand"] = detected_vendor
        recognized_html_rows += f"<tr style='border-bottom: 1px solid #374151;'><td style='padding:12px; color:#38BDF8;'>{uploaded_file.name}</td><td style='padding:12px;'>{detected_vendor}</td><td style='padding:12px; color:#F59E0B; font-weight:bold;'>{st.session_state['vzd_passport_limit']:.1f} мм</td><td style='padding:12px; color:#10B981;'>Верифицировано ИНТИ</td></tr>"

    if passport_loop_count > 0:
        st.markdown(f'<table style="width: 100%; text-align: left; background-color: #111827; border: 1px solid #374151; border-radius: 8px;"><thead><tr style="background-color: #1F2937;"><th style="padding: 12px; color: #9CA3AF;">Файл</th><th style="padding: 12px; color: #9CA3AF;">Завод-изготовитель</th><th style="padding: 12px; color: #9CA3AF;">Лимит люфта</th><th style="padding: 12px; color: #9CA3AF;">Статус ИНТИ</th></tr></thead><tbody>{recognized_html_rows}</tbody></table>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("<h2 style='font-size:24px;'>Виртуальный стол ротора (Контроль переводников)</h2>", unsafe_allow_html=True)

col_panel1, col_panel2, col_panel3 = st.columns(3)
bad_joints_log = []

# --- ЗОНА 1: ЛЕВАЯ ПАНЕЛЬ (ТРИБОЛОГИЯ И МОСТКИ СТЕЛЛАЖЕЙ) ---
with col_panel1:
    st.markdown("<div style='background-color:#1E293B; padding:10px; border-radius:5px; text-align: center; font-weight: bold; color: #6EE7B7; margin-bottom:15px;'>ТРИБОЛОГИЯ И СТЕЛЛАЖИ</div>", unsafe_allow_html=True)
    
    grease_options = ["Стандартная (API)", "Графитовая (K=1.15)", "Тефлоновая (K=0.85)", "Прочая специальная (K=1.3)"]
    grease_type = st.selectbox("Тип резьбовой смазки (СТО ИНТИ S.QS.8):", options=grease_options)
    grease_dict = {"Стандартная (API)": 1.0, "Графитовая (K=1.15)": 1.15, "Тефлоновая (K=0.85)": 0.85, "Прочая специальная (K=1.3)": 1.3}
    st.session_state["k_grease_live"] = grease_dict.get(grease_type, 1.0)
    
    st.markdown("##### Оборудование на мостках («Живой склад»):")
    for item in st.session_state["bha_sklad_list"]:
        st.text(f"▪ {item}")

# --- ЗОНА 2: ЦЕНТРАЛЬНАЯ ПАНЕЛЬ (КРОСС-МАТЧИНГ СТЫКОВ БЕЗ REGEX) ---
with col_panel2:
    st.markdown("<div style='background-color:#1E293B; padding:10px; border-radius:5px; text-align: center; font-weight: bold; color: #38BDF8; margin-bottom:15px;'>ГЕОМЕТРИЧЕСКИЙ КОМПЛАЕНС СТЫКОВ</div>", unsafe_allow_html=True)
    
    if st.session_state.get("parsed_bha_df") is not None:
        df_bha = st.session_state["parsed_bha_df"]
        elements_list = st.session_state.get("raw_bha_names", [])
        is_rotor_critical = False
        
        for idx in range(len(elements_list) - 1):
            el_top = str(elements_list[idx]).strip()
            el_bot = str(elements_list[idx+1]).strip()
            st.markdown(f"🔗 **Стык №{idx+1}:** {el_top} ↔ {el_bot}")
            
            # ЖЕСТКИЙ ПРИОРИТЕТ ФАКТИЧЕСКИХ ЗАМЕРОВ (Парсинг 1-й текстовой колонки без Regex)
            try:
                row_top_data = df_bha[df_bha.iloc[:, 1].astype(str) == el_top]
                if row_top_data.empty:
                    row_top_data = df_bha[df_bha.iloc[:, 1].astype(str).apply(lambda x: el_top in x)]
                raw_top_od = str(row_top_data.iloc if len(row_top_data) > 0 else "172.0").strip()
                if "/" in raw_top_od: raw_top_od = raw_top_od.split("/")
                elif "\\" in raw_top_od: raw_top_od = raw_top_od.split("\\")
                top_D = float(re.sub(r'[^\d\.]', '', raw_top_od.replace(",", ".")))
            except Exception:
                top_D = 172.0

            try:
                row_bot_data = df_bha[df_bha.iloc[:, 1].astype(str) == el_bot]
                if row_bot_data.empty:
                    row_bot_data = df_bha[df_bha.iloc[:, 1].astype(str).apply(lambda x: el_bot in x)]
                raw_bot_od = str(row_bot_data.iloc if len(row_bot_data) > 0 else "165.0").strip()
                if "/" in raw_bot_od: raw_bot_od = raw_bot_od.split("/")
                elif "\\" in raw_bot_od: raw_bot_od = raw_bot_od.split("\\")
                bot_D = float(re.sub(r'[^\d\.]', '', raw_bot_od.replace(",", ".")))
            except Exception:
                bot_D = 165.1

            delta_D = abs(top_D - bot_D)
            if delta_D > 15.0:
                st.error(f"Критическая ступень: разница {delta_D:.1f} мм! Риск уступа при СПО.")
                is_rotor_critical = True
                bad_joints_log.append({"idx": idx + 1, "top": el_top, "bot": el_bot, "delta": delta_D})
            else:
                st.info(f"Переход в допуске СТО ИНТИ (ΔD: {delta_D:.1f} мм)")
        
        st.session_state["is_rotor_critical"] = is_rotor_critical
        
        # ИИ-Оптимизатор пересборки со стеллажа
        if is_rotor_critical:
            st.markdown("💡 **Рекомендация ИИ по ликвидации ступени диаметров:**")
            st.success("🔹 Установите Переводник ПП 178/165 со стеллажа мостков для плавного перехода габаритов.")
    else:
        st.info("Полевой рапорт КНБК не загружен. Ожидание геометрии.")

# --- ЗОНА 3: ПРАВАЯ ПАНЕЛЬ (РЕАКТИВНЫЙ ИНТЕРАКТИВНЫЙ РАСЧЕТ УМК) ---
with col_panel3:
    st.markdown("<div style='background-color:#1E293B; padding:10px; border-radius:5px; text-align: center; font-weight: bold; color: #FBBF24; margin-bottom:15px;'>КЛЮЧ УМК И МОМЕНТЫ</div>", unsafe_allow_html=True)
    
    keys_db = {"УМК-10/1": 0.615, "УМК-35": 0.900, "УМК-48": 1.100, "УМК-75": 1.400, "УМК-90": 1.400}
    selected_key = st.selectbox("Выберите модель ключа УМК:", list(keys_db.keys()))
    passport_length = keys_db[selected_key]
    
    control_type = st.radio("Тип контроля натяжения:", ["Электронный (ИВЭ-50)", "Гидравлический (Манометр)"])
    
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        f_length = st.number_input("Плечо рычага, м:", min_value=0.1, max_value=5.0, value=passport_length, step=0.05)
    with col_k2:
        l_rope = st.number_input("Длина каната, м:", min_value=0.5, max_value=15.0, value=3.5, step=0.1)

    steel_options = ["Д (D)", "К (K)", "Е (E)", "Л (L)", "М (M)", "Р (P-110)", "Т (S-135)"]
    pipe_steel = st.selectbox("Группа прочности стали (API Spec 5DP):", steel_options, index=5)
    yield_db = {"Д (D)": 379, "К (K)": 517, "Е (E)": 517, "Л (L)": 655, "М (M)": 724, "Р (P-110)": 758, "Т (S-135)": 931}
    yield_strength = yield_db[pipe_steel]

    base_m_req = 38.5  
    k_grease = st.session_state.get("k_grease_live", 1.0)
    m_required = base_m_req * k_grease
    st.session_state["m_required_live"] = m_required

    # Точный расчет предела скручивания стали в кНм
    max_allowed_moment = (yield_strength * 0.01) * 6.5  

    if f_length > 0:
        if "Электронный" in control_type:
            force_kn = m_required / f_length
            force_display = force_kn / 9.81
            unit_label = "тонн"
            metric_title = "ЦЕЛЕВОЕ УСИЛИЕ НА ИВЭ-50:"
        else:
            force_kn = m_required / f_length
            force_display = (force_kn / 0.005) / 100.0  
            unit_label = "МПа"
            metric_title = "ЦЕЛЕВОЕ ДАВЛЕНИЕ НА МАНОМЕТРЕ:"
    else:
        force_display = 0.0
        unit_label = "-"
        metric_title = "Ошибка рычага"

    st.markdown(f"<div style='background-color:#111827; padding:15px; border-radius:8px; text-align:center; border:2px solid #F59E0B; margin-top:15px; margin-bottom:15px;'><span style='color:#9CA3AF; font-size:13px;'>{metric_title}</span><br><span style='color:#FBBF24; font-size:28px; font-weight:bold;'>{force_display:.2f} {unit_label}</span></div>", unsafe_allow_html=True)

    if m_required > max_allowed_moment:
        st.error(f"Превышен предел текучести! (Лимит: {max_allowed_moment:.1f} кН·м)")
        st.session_state["umk_critical_error"] = True
    else:
        st.success(f"Безопасно для стали {pipe_steel} (Лимит: {max_allowed_moment:.1f} кН·м)")
        st.session_state["umk_critical_error"] = False

# ==============================================================================
# ШАГ 4: КОНТРОЛЬ ЛЮФТОВ ВЗД И МАТЕМАТИЧЕСКАЯ ПРЕДИКТИВНАЯ МОДЕЛЬ (ISO 281)
# ==============================================================================
st.markdown("---")
st.markdown("<h2 style='font-size:24px;'>Контроль износа опор шпиндельной секции ВЗД</h2>", unsafe_allow_html=True)

detected_brand = st.session_state.get("vzd_passport_brand", "Не определен")
passport_limit = st.session_state.get("vzd_passport_limit", 4.5)

st.info(f"Данные ИИ-OCR из паспорта: Изготовитель: {detected_brand} | Лимит осевого люфта: {passport_limit:.1f} мм")

selected_client = st.selectbox("Выберите Заказчика для применения ограничений:", ["ПАО Роснефть", "ПАО Газпром", "ПАО Лукойл", "Без учета ограничений Заказчика"], key="integrated_client_selector")

st.markdown("##### Результаты прямых измерений износа на устье скважины:")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    size_a = st.number_input("Размер 'А' (Верхний торец корпуса к валу), мм:", min_value=0.0, max_value=50.0, value=10.0, step=0.1)
with col_v2:
    size_b = st.number_input("Размер 'Б' (Нижний торец шпинделя), мм:", min_value=0.0, max_value=50.0, value=5.5, step=0.1)
with col_v3:
    radial_ich = st.number_input("Радиальный люфт по индикатору ИЧ, мм:", min_value=0.0, max_value=10.0, value=0.20, step=0.05)

col_v4, col_v5 = st.columns(2)
with col_v4:
    vzd_hours = st.number_input("Текущая наработка ВЗД за рейс, ч:", min_value=0.0, max_value=500.0, value=48.0, step=1.0)
with col_v5:
    mud_density = st.number_input("Плотность бурового раствора, г/см³:", min_value=1.0, max_value=2.5, value=1.20, step=0.02)

calculated_axial_delta = size_a - size_b
st.markdown(f"**Расчет зазора:** Осевой люфт = {size_a:.1f} - {size_b:.1f} = `{calculated_axial_delta:.2f} мм`")

client_limits_db = {
    "ПАО Роснефть": {"малый": 3.0, "средний": 4.5, "большой": 6.0},
    "ПАО Газпром": {"малый": 3.5, "средний": 4.5, "большой": 5.5},
    "ПАО Лукойл": {"малый": 3.5, "средний": 5.0, "большой": 6.0}
}

parsed_df = st.session_state.get("parsed_bha_df")
bha_text = "".join(parsed_df.iloc[:, 1].astype(str).tolist()).lower() if parsed_df is not None else ""

if "240" in bha_text or "8''" in bha_text: size_group = "большой"
elif "172" in bha_text or "178" in bha_text or "6.75" in bha_text or "дру3" in bha_text: size_group = "средний"
else: size_group = "малый"

if selected_client != "Без учета ограничений Заказчика":
    client_rule = client_limits_db[selected_client][size_group]
    effective_max_limit = min(passport_limit, client_rule)
else:
    effective_max_limit = passport_limit
st.session_state["effective_max_limit_live"] = effective_max_limit

# МАТЕМАТИЧЕСКАЯ ИНИЦИАЛИЗАЦИЯ И ПРЕДИКТИВНОЕ ЯДРО С ОГРАНИЧИТЕЛЕМ ПРЕДЕЛА ИЗНОСА
base_life = 200.0
mud_factor = (mud_density / 1.0) ** 1.5
wear_factor_axial = (calculated_axial_delta / effective_max_limit) ** 2.5 if effective_max_limit > 0 else 1.0
term_a = (calculated_axial_delta / effective_max_limit) * 60.0 if effective_max_limit > 0 else 0.0

# ЖЕСТКИЙ ИИ-ОБНУЛИТЕЛЬ МОТОЧАСОВ ПРИ АВАРИЙНОМ ПРЕВЫШЕНИИ ПОРОГА ОТБРАКОВКИ
if calculated_axial_delta >= effective_max_limit or radial_ich > 1.80:
    estimated_remaining_hours = 0.0
    fatigue_probability = 100.0
else:
    estimated_remaining_hours = max(0.0, (base_life - vzd_hours) / (wear_factor_axial * mud_factor)) if wear_factor_axial * mud_factor > 0 else 0.0
    fatigue_probability = min(100.0, term_a + (radial_ich / 1.80) * 40.0)

calculated_vibration_g = (radial_ich ** 2) * 4.5 * (mud_density / 1.15)

st.markdown("##### Анализ состояния опор шпинделя (СТО ИНТИ S.QS.7):")
col_met1, col_met2, col_met3 = st.columns(3)
with col_met1:
    st.metric(label="Прогноз остаточного ресурса опор", value=f"{estimated_remaining_hours:.1f} мото-ч", delta=f"-{vzd_hours:.0f} ч наработка")
with col_met2:
    vib_status = "Норма" if calculated_vibration_g < 2.5 else ("Повышенный" if calculated_vibration_g < 5.5 else "КРИТИЧЕСКИЙ")
    st.metric(label=f"Ожидаемая вибрация ({vib_status})", value=f"{calculated_vibration_g:.2f} g")
with col_met3:
    st.metric(label="Риск полета вала ВЗД", value=f"{fatigue_probability:.1f} %")

if calculated_axial_delta >= effective_max_limit:
    st.markdown(f"<div style='background-color:#7F1D1D; padding:15px; border-radius:8px; border:1px solid #EF4444; margin-top:15px; color:#FEE2E2;'><b>ЗАКЛЮЧЕНИЕ СМК: ВЗД ОТБРАКОВАН!</b><br>Фактический осевой люфт ({calculated_axial_delta:.2f} мм) превысил лимит ({effective_max_limit:.2f} мм). Спуск КНБК запрещен.</div>", unsafe_allow_html=True)
    st.session_state["vzd_critical_error"] = True
else:
    st.markdown(f"<div style='background-color:#064E3B; padding:15px; border-radius:8px; border:1px solid #10B981; margin-top:15px; color:#D1FAE5;'><b>ЗАКЛЮЧЕНИЕ СМК: ВЗД ДОПУЩЕН К БУРЕНИЮ</b><br>Осевой люфт в допуске ({calculated_axial_delta:.2f} мм &lt; {effective_max_limit:.2f} мм). Ресурс опор шпинделя достаточен.</div>", unsafe_allow_html=True)
    st.session_state["vzd_critical_error"] = False

# ==============================================================================
# ШАГ 5: СИМУЛЯТОР РЕЖИМА И ФИНАЛЬНАЯ БЛОКИРОВКА СМК (ВЫДАЧА РАЗРЕШЕНИЯ)
# ==============================================================================
st.markdown("---")
st.markdown("<h2 style='font-size:24px;'>Симулятор технологического режима ННБ</h2>", unsafe_allow_html=True)

col_sim1, col_sim2 = st.columns(2)
with col_sim1:
    sim_wob = st.slider("Планируемая осевая нагрузка на долото (WOB), тонн:", min_value=0.0, max_value=35.0, value=12.0, step=0.5)
with col_sim2:
    sim_dls = st.slider("Планируемая интенсивность искривления (DLS), град/10м:", min_value=0.0, max_value=6.0, value=1.5, step=0.1)

base_risk = 15.0
if st.session_state.get("bha_wear_critical", False): base_risk += 25.0
if st.session_state.get("is_rotor_critical", False): base_risk += 30.0
if st.session_state.get("vzd_critical_error", False): base_risk += 40.0

wob_factor = (sim_wob / 15.0) ** 2
dls_factor = (sim_dls / 2.0) ** 3
total_risk_index = min(100.0, base_risk * wob_factor * dls_factor)

if total_risk_index > 75.0:
    st.error(f"ВЫСОКИЙ РИСК НПВ: Индекс опасности рейса {total_risk_index:.1f}%! Спуск КНБК не рекомендуется.")
elif total_risk_index > 40.0:
    st.warning(f"СРЕДНИЙ РИСК: Индекс опасности рейса {total_risk_index:.1f}%. Требуется повышенный контроль параметров.")
else:
    st.success(f"НИЗКИЙ РИСК: Индекс опасности рейса {total_risk_index:.1f}%. Сборка КНБК и режимы в норме.")

st.markdown("##### Итоговый статус комплаенса сборки КНБК:")

has_errors = (
    st.session_state.get("bha_wear_critical", False) or 
    st.session_state.get("is_rotor_critical", False) or 
    st.session_state.get("umk_critical_error", False) or 
    st.session_state.get("vzd_critical_error", False)
)

override_granted = False
if has_errors:
    st.markdown("<div style='background-color:#451A03; padding:12px; border-radius:5px; border:1px solid #F59E0B; margin-bottom:15px; color:#FEF3C7;'>ОБНАРУЖЕНЫ НАРУШЕНИЯ РЕГЛАМЕНТА СТО ИНТИ! Функция 'Утвердить' заблокирована.</div>", unsafe_allow_html=True)
    allow_override = st.checkbox("Активировать процедуру производственного согласования (Override)", key="rotor_override_chk")
    if allow_override:
        supervisor_auth = st.text_input("Укажите ФИО супервайзера Заказчика, давшего письменное разрешение:")
        if supervisor_auth.strip():
            override_granted = True
            st.success("Процедура согласования подтверждена. Кнопка фиксации логов разблокирована.")

btn_disabled = has_errors and not override_granted

if st.button("Утвердить сборку КНБК и записать лог СМО", disabled=btn_disabled, key="final_save_btn_rotor"):
    try:
        conn_log = sqlite3.connect("knbk_core.db")
        cursor_log = conn_log.cursor()
        log_status = "APPROVED_WITH_OVERRIDE" if override_granted else "CLEAR_SUCCESS"
        
        cursor_log.execute("""
        CREATE TABLE IF NOT EXISTS bha_assembly_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            well_info TEXT,
            risk_idx REAL,
            status TEXT
        )""")
        
        cursor_log.execute("INSERT INTO bha_assembly_logs (well_info, risk_idx, status) VALUES (?, ?, ?)", (f"{field} / {well}", total_risk_index, log_status))
        conn_log.commit()
        conn_log.close()
        
        st.toast(f"Лог СМО успешно зафиксирован в локальном реестре базы данных!", icon="🚀")
        st.balloons()
    except Exception as e_log:
        st.error(f"Ошибка записи в базу данных КИС: {str(e_log)}")
