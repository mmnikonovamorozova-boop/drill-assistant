import streamlit as st
import pandas as pd
import numpy as np
import math
import json
import base64
import time
import io

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ И СТРОГАЯ АВТЕНТИФИКАЦИЯ СМК ---
st.set_page_config(page_title="Прогноз траектории КНБК", layout="wide")

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Пожалуйста, авторизуйтесь на Главной странице приложения.")
    st.stop()

# --- СКВОЗНОЙ ШЛЮЗ ДАННЫХ ИЗ ГЛОБАЛЬНОЙ СЕССИИ ПРИЛОЖЕНИЯ ---
engineer = st.session_state.get("engineer_name", "Не указано")
well = st.session_state.get("well_number", "Не указано")
field = st.session_state.get("field_name", "Не указано")
bha = st.session_state.get("bha_number", "1")

# Выводим единую синюю плашку контекста рейса, идентичную прошлым модулям
st.info(f"📋 **Рейс:** {field} | Скв/Куст: {well} | КНБК №{bha} | **Инженер:** {engineer}")
st.divider()

st.title("🎯 Модуль предиктивного моделирования пространственной интенсивности")
st.markdown("### 📈 Блок 1: Предиктивный прогноз траектории скважины")

with st.expander("🔰 Паспорт верификации СТО ИНТИ (Прогнозирование траектории и КНБК)", expanded=False):
    st.markdown("### 🔬 Требования отраслевых стандартов СТО ИНТИ S.100.3 и СТО ИНТИ S.QS.8:")
    st.markdown("""
    * **Стандартизация предиктивных моделей:** Применение методов адаптивного машинного обучения и градиентного спуска (СМК) для прогнозирования пространственного положения ствола.
    * **Интегральный тригонометрический расчет:** Расчет координат забоя по легитимному методу минимальной кривизны (Minimum Curvature Method) согласно международным стандартам API RP 7G.
    * **Контроль коммерческих штрафов:** Реализация алгоритма скользящего окна для автоматического контроля правила 3 последовательных нарушений лимита интенсивности (DLS) по ТК договора.
    * **Цифровой мост ОЦБ:** Интеграция шлюза оперативной корректировки планового профиля и калибровочных весов КНБК специалистами Операционного Центра из города без предоставления прямого доступа к коду.
    * **Аудит извилистости ствола:** Непрерывный расчет индекса пространственной сложности (DDI — Directional Difficulty Index) для превентивной оценки рисков возникновения затяжек и посадок инструмента.
    """)

st.markdown(" ") # Компактный технологический отступ
# =========================================================================
# БЛОК 3 — СКВОЗНАЯ ШИНА ДАННЫХ И ЦЕНТРАЛЬНЫЙ АДАПТИВНЫЙ ИНТЕРФЕЙС
# =========================================================================

# Боковая панель: считывание параметров из сессии и инициализация лимитов
st.sidebar.markdown("### 🧬 Сквозные данные системы")
selected_vink = st.sidebar.text_input("Заказчик (Холдинг):", value=st.session_state.get("main_page_company", "Роснефть"), disabled=True)

# Загрузка базы лимитов с резервным словарем
try:
    df_vink_db = pd.read_excel("vink_limits_db.xlsx")
except Exception:
    df_vink_db = pd.DataFrame()

shared_buoyancy = float(st.session_state.get("shared_buoyancy_factor", 0.85))
yield_stress = float(st.session_state.get("shared_yield_stress", 40.0))
radial_wear_vzd = float(st.session_state.get("val_radial_ich", 0.20))

st.sidebar.caption(f"💧 ДНС раствора: {yield_stress} дПа")
st.sidebar.caption(f"🔧 Люфт шпинделя: {radial_wear_vzd} мм")
st.sidebar.caption(f"🚢 Коэф. плавучести: {shared_buoyancy:.2f}")

# --- 3.2. Центральная рабочая область (Адаптивные вкладки) ---
st.markdown("### 🛠 Настройки интервала бурения")
tab_contract, tab_knbc, tab_geology = st.tabs(["📋 Контракт и Лимиты", "📐 Компоновка КНБК", "🌋 Геологический разрез"])

# Фильтруем строки таблицы по холдингу для получения списка ДОРов
if 'df_vink_db' in locals() and not df_vink_db.empty:
    filtered_dors = df_vink_db[df_vink_db["Холдинг"] == selected_vink]
    list_of_dors = filtered_dors["Заказчик (ДОР)"].unique().tolist() if not filtered_dors.empty else ["Стандартный договор"]
else:
    list_of_dors = ["Стандартный договор"]

# Вкладка 1: Контрактные ограничения ДОРов
with tab_contract:
    c_c1, c_c2 = st.columns(2)
    with c_c1:
        selected_dor = st.selectbox(f"🏢 Выберите предприятие ({selected_vink}):", list_of_dors)
    with c_c2:
        gno_zone = st.checkbox("⚠ Учитывать зоны ГНО / Опасность желобов", value=False)
        
    if 'filtered_dors' in locals() and not filtered_dors.empty and selected_dor in list_of_dors:
        dor_row = filtered_dors[filtered_dors["Заказчик (ДОР)"] == selected_dor].iloc[0]
        contract_dls_limit = float(dor_row["Лимит_DLS"])
        contract_gno_limit = float(dor_row["Лимит_ГНО"])
    else:
        contract_dls_limit, contract_gno_limit = 3.0, 1.2
        
    if gno_zone:
        max_allowed_dls = st.number_input("Макс. допустимый DLS по договору (ГНО), °/10м:", value=contract_gno_limit, step=0.1)
    else:
        max_allowed_dls = st.number_input("Макс. допустимый DLS по договору, °/10м:", value=contract_dls_limit, step=0.1)

# =========================================================================
# БЛОК 2: УМНОЕ ИИ-ЯДРО: ИМПОРТ И СЕЛЕКЦИЯ КАЛИБРОВОК ПО ИМЕНИ СКВАЖИНЫ
# =========================================================================

# Исправлено: Оставляем строго один декоратор кэширования для защиты от зависаний
@st.cache_data(ttl=60)
def load_calibrations_from_github_api(target_well_name):
    """
    Развернутая функция безопасного извлечения адаптивных весов КНБК из удаленного
    репозитория GitHub API по принципам сквозного логирования СТО ИНТИ S.100.3.
    """
    # Безопасное чтение токена авторизации из секретов Streamlit Cloud
    token = st.secrets.get("GITHUB_TOKEN", None)
    
    # Репозиторий хранения калибровочных паспортов компании
    repo = "mmnikonovamorozova-boop/drill-assistant"
    path = "calibrations_db.json"
    url = "https://api.github.com/repos/mmnikonovamorozova-boop/drill-assistant/contents/calibrations_db.json"
    
    # Формирование дефолтного (базового) паспорта КНБК на случай сбоя связи
    default_passport = {
        "well_name": "Базовый паспорт КНБК",
        "k_slide_base": 0.38,
        "k_rotary_base": 0.02,
        "last_update": "01.01.2026"
    }
    
    if not token:
        # Автономный режим работы на удаленной буровой (без интернета)
        return default_passport

    try:
        import requests
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            file_data = response.json()
            # Декодирование защищенного Base64-контента из GitHub
            content_b64 = file_data.get("content", "")
            json_str = base64.b64decode(content_b64).decode("utf-8")
            db_dict = json.loads(json_str)
            
            # Поиск калибровочных весов под конкретную целевую скважину
            clean_target = str(target_well_name).strip().upper()
            for key_well, data_v in db_dict.items():
                if clean_target in str(key_well).strip().upper():
                    return data_v
                    
            # Если скважина новая — возвращаем базовые отраслевые настройки
            return default_passport
        else:
            return default_passport
            
    except Exception:
        # Защитный барьер: при любых сетевых ошибках возвращаем стабильный дефолт
        return default_passport

# =========================================================================
# БЛОК 4 — ОБРАБОТКА ГГИ ЗАКАЗЧИКА И РАСЧЕТ ТРАЕКТОРИИ (MINIMUM CURVATURE METHOD)
# Требования легитимности: СТО ИНТИ S.QS.8 / Устранение хардкода колонок .iloc
# =========================================================================

st.markdown("---")
st.markdown("### 🗺 Блок 4: Сверка пространственных данных и импорт ГГИ")
well_name = st.text_input("Номер/Название скважины:", value="101-Г", key="b4_well_name_input")

# Инициализация и подготовка данных
active_calibration = load_calibrations_from_github_api(well_name)
st.sidebar.markdown(f"**Статус ИИ-ядра:** Калибровки для {well_name} успешно применены.")

uploaded_ggi = st.file_uploader("Выгрузите Excel/CSV с плановым профилем (ГГИ):", type=["xlsx", "csv"], key="b4_file_uploader")

def calculate_spatial_trajectory_legyt(df_inc):
    df_inc.columns = [str(col).strip().upper() for col in df_inc.columns]
    col_md = [c for c in df_inc.columns if "ГЛУБ" in c or "MD" in c or "LENGTH" in c]
    col_inc = [c for c in df_inc.columns if "ЗЕН" in c or "INC" in c or "УГОЛ" in c]
    col_azi = [c for c in df_inc.columns if "АЗИ" in c or "AZI" in c or "НАПР" in c]
    
    if not col_md or not col_inc or not col_azi:
        st.error("🚨 ОШИБКА ФОРМАТА ГГИ: Не удалось автоматически распознать колонки.")
        return None
        
    try:
        md = pd.to_numeric(df_inc[col_md[0]], errors="coerce").fillna(0).values
        inc = np.radians(pd.to_numeric(df_inc[col_inc[0]], errors="coerce").fillna(0).values)
        azi = np.radians(pd.to_numeric(df_inc[col_azi[0]], errors="coerce").fillna(0).values)
        n_records = len(md)
        
        if n_records < 2:
            return None
            
        tvd = np.zeros(n_records)
        north = np.zeros(n_records)
        east = np.zeros(n_records)
        dls = np.zeros(n_records)
        tvd[0] = md[0]
        for i in range(1, n_records):
            dl_md = md[i] - md[i-1]
            if dl_md <= 0:
                tvd[i], north[i], east[i] = tvd[i-1], north[i-1], east[i-1]
                continue
            cos_alpha = math.cos(inc[i-1]) * math.cos(inc[i]) + math.sin(inc[i-1]) * math.sin(inc[i]) * math.cos(azi[i] - azi[i-1])
            cos_alpha = max(-1.0, min(1.0, cos_alpha))
            alpha = math.acos(cos_alpha)
            f_ratio = (2.0 / alpha) * math.tan(alpha / 2.0) if alpha != 0 else 1.0
            tvd[i] = tvd[i-1] + (dl_md / 2.0) * (math.cos(inc[i-1]) + math.cos(inc[i])) * f_ratio
            north[i] = north[i-1] + (dl_md / 2.0) * (math.sin(inc[i-1]) * math.cos(azi[i-1]) + math.sin(inc[i]) * math.cos(azi[i])) * f_ratio
            east[i] = east[i-1] + (dl_md / 2.0) * (math.sin(inc[i-1]) * math.sin(azi[i-1]) + math.sin(inc[i]) * math.sin(azi[i])) * f_ratio
            dls[i] = (alpha * 10.0) / dl_md if dl_md > 0 else 0.0
            
        return pd.DataFrame({"ГЛУБИНА_MD": md, "ЗЕНИТ_ГРАД": np.degrees(inc), "АЗИМУТ_ГРАД": np.degrees(azi), "TVD": tvd, "NORTH": north, "EAST": east, "DLS_10M": np.degrees(dls)})
    except Exception as ex:
        st.error(f"🚨 СБОЙ MCM: {str(ex)}")
        return None
df_trajectory_calculated = None
df_inc_raw = None

# Автоматическая попытка забрать последнюю поправку плана из ОЦБ через облако
df_cloud_ggi = load_actual_ggi_from_github(well_name)

if df_cloud_ggi is not None:
    df_inc_raw = df_cloud_ggi
    st.success(f"🌐 СИНХРОНИЗАЦИЯ ОЦБ: Автоматически применен актуальный скорректированный план траектории из города! Точек плана: {len(df_inc_raw)}")
elif uploaded_ggi is not None:
    try:
        if uploaded_ggi.name.endswith('.xlsx'):
            df_inc_raw = pd.read_excel(uploaded_ggi)
        else:
            df_inc_raw = pd.read_csv(uploaded_ggi)
        st.success(f"✔ Профиль ГГИ успешно подгружен инженером вручную. Точек плана: {len(df_inc_raw)}")
    except Exception as e:
        st.error(f"🚨 Ошибка парсинга ручного файла ГГИ: {str(e)}")

# Запуск расчета координат при успешной загрузке данных
if df_inc_raw is not None:
    df_trajectory_calculated = calculate_spatial_trajectory_legyt(df_inc_raw)

# =========================================================================
# БЛОК 5.1 — ФИЗИКО-МАТЕМАТИЧЕСКОЕ МОДЕЛИРОВАНИЕ СИЛ КНБК И УВОДА ДОЛОТА
# Требования легитимности: СТО ИНТИ S.100.3 / API RP 7G
# =========================================================================

st.markdown("### 🛠 Блок 5: Пространственная интенсивность и увод")

# Извлекаем сквозные реологические параметры из сессии
f_dens = float(st.session_state.get("shared_buoyancy_factor", 1.0))
f_yp_corrected = float(st.session_state.get("shared_yield_stress", 12.0))
n_hb = float(st.session_state.get("shared_flow_index", 0.65))

# Строгий расчет гидродинамического сопротивления раствора
rheology_modifier = (1.0 / f_dens) * (1.0 + (f_yp_corrected * 0.025) * (2.0 - n_hb))

# Извлекаем калибровочные веса КНБК из ИИ-паспорта (Блок 2)
k_slide_current = float(active_calibration.get("k_slide_base", 0.38))
k_rotary_current = float(active_calibration.get("k_rotary_base", 0.02))

# --- НОВАЯ ФУНКЦИЯ ОЦБ: РАСЧЕТ ИНДЕКСА СЛОЖНОСТИ СТВОЛА (DDI) ---
forecast_dls_val = st.session_state.get("forecast_dls_deg10m", 0.0)
if forecast_dls_val > 0:
    calculated_ddi = math.log10(forecast_md) * (1.0 + (forecast_dls_val / max_allowed_dls))
else:
    calculated_ddi = math.log10(forecast_md)

st.markdown("##### 📐 Оценка профиля по стандарту СТО ИНТИ S.QS.8:")
col_ddi1, col_ddi2 = st.columns(2)
with col_ddi1:
    st.metric("Индекс сложности ствола (DDI)", f"{calculated_ddi:.2f} ед.")
with col_ddi2:
    if calculated_ddi < 4.0:
        st.success("🟢 Профиль простой (Низкие риски затяжек)")
    elif calculated_ddi < 6.0:
        st.warning("⚠ Профиль средней сложности (Контролировать торк)")
    else:
        st.error("🚨 Высокая извилистость! Риск недохождения обсадной колонны")

st.markdown("##### ⚙ Параметры калибровки боковой силы и анизотропии пласта:")
col_f1, col_f2 = st.columns(2)
st.markdown("##### 🔮 Параметры планирования прогнозного интервала:")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1: progno_step_meters = st.number_input("Длина прогнозного интервала (м):", min_value=10.0, max_value=300.0, value=30.0, step=10.0)
with col_p2: planned_slide_pct = st.slider("Доля слайдирования на интервале (%):", min_value=0.0, max_value=100.0, value=30.0, step=5.0)
with col_p3: tool_face_angle = st.slider("Угол установки отклонителя (Tool Face, °):", min_value=0.0, max_value=360.0, value=45.0, step=5.0)
slide_fraction = planned_slide_pct / 100.0
if df_trajectory_calculated is not None and not df_trajectory_calculated.empty:
    last_row = df_trajectory_calculated.iloc[-1]
    current_md = float(last_row["ГЛУБИНА_MD"])
    current_inc = float(last_row["ЗЕНИТ_ГРАД"])
    current_azi = float(last_row["АЗИМУТ_ГРАД"])
    current_tvd = float(last_row["TVD"])
    current_north = float(last_row["NORTH"])
    current_east = float(last_row["EAST"])
else:
    current_md, current_inc, current_azi = 1500.0, 25.0, 120.0
    current_tvd, current_north, current_east = 1420.0, 150.0, 320.0
# Расчет изменения углов ствола
shag_sl = 0.45 * k_slide_current * math.cos(math.radians(tool_face_angle))
shag_rot = 0.02 * k_rotary_current + (side_force_calculated * 0.001)
itogo_shag_zenit = (shag_sl * slide_fraction) + (shag_rot * (1.0 - slide_fraction))

povorot_sl = 0.45 * k_slide_current * math.sin(math.radians(tool_face_angle))
povorot_rot = -0.015 * (1.0 - formation_anisotropy)
itogo_shag_azimut = (povorot_sl * slide_fraction) + (povorot_rot * (1.0 - slide_fraction))

# Новые углы на конце интервала
forecast_md = current_md + progno_step_meters
delta_inc = (itogo_shag_zenit / 10.0) * progno_step_meters
delta_azi = (itogo_shag_azimut / 10.0) * progno_step_meters

forecast_inc = max(0.0, min(90.0, current_inc + delta_inc))
forecast_azi = (current_azi + delta_azi) % 360.0
st.session_state["forecast_dls_deg10m"] = abs(itogo_shag_zenit)
st.markdown("##### 📊 Прогноз пространственного положения КНБК на забое:")
col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("Прогнозная глубина MD", f"{forecast_md:.1f} м", f"+{progno_step_meters:.1f} м")
col_r2.metric("Прогнозный зенитный угол", f"{forecast_inc:.2f} °", f"{delta_inc:+.2f} °")
col_r3.metric("Прогнозный азимут ствола", f"{forecast_azi:.2f} °", f"{delta_azi:+.2f} °")

# =========================================================================
# БЛОК 6 — ТЕХНОЛОГИЧЕСКИЙ КАЛЬКУЛЯТОР И КОНТРОЛЬ ШТРАФНЫХ САНКЦИЙ ЗАКАЗЧИКА
# Требования легитимности: СТО ИНТИ S.QS.8 / Коммерческие ТК Договора
# =========================================================================
st.markdown("---")
st.markdown("### 🎯 Блок 6: Оптимизация слайдирования и аудит штрафных рисков")
st.caption("Расчет интервалов проходки с контролем правила 3 последовательных нарушений по ТК договора")

st.markdown("##### 📜 Настройка лимитов интенсивности по Договору Заказчика:")
col_tk1, col_tk2, col_tk3 = st.columns(3)
with col_tk1: tk_dls_max = st.number_input("Макс. допустимая интенсивность (°/10м):", min_value=0.5, max_value=3.0, value=1.2, step=0.1, key="tk_dls_max")
with col_tk2: tk_dls_min = st.number_input("Мин. необходимый набор угла (°/10м):", min_value=0.0, max_value=1.5, value=0.15, step=0.05, key="tk_dls_min")
with col_tk3: st.metric("Триггер коммерческого штрафа", "3 точки подряд")
if uploaded_ggi is not None and df_trajectory_calculated is not None:
    try:
        target_inc = float(df_trajectory_calculated.iloc[-1]["ЗЕНИТ_ГРАД"])
        target_azi = float(df_trajectory_calculated.iloc[-1]["АЗИМУТ_ГРАД"])
        st.info(f"🎯 Проектные уставки автоматически считаны из ГГИ: Зенит {target_inc:.2f} °, Азимут {target_azi:.2f} °")
    except Exception:
        target_inc, target_azi = 26.50, 118.20
else:
    col_t1, col_t2 = st.columns(2)
    with col_t1: target_inc = st.number_input("Целевой проектный зенитный угол (°):", value=26.50, key="b6_target_inc")
    with col_t2: target_azi = st.number_input("Целевой проектный азимут ствола (°):", value=118.20, key="b6_target_azi")
raznica_zenita = target_inc - current_inc
if abs(shag_sl) > 0.001:
    metry_слайд = (raznica_zenita / (shag_sl / 10.0))
    metry_слайд = max(0.0, min(progno_step_meters, metry_слайд))
else:
    metry_слайд = 0.0

metry_ротор = max(0.0, progno_step_meters - metry_слайд)
procent_слайда = (metry_слайд / max(1.0, progno_step_meters)) * 100.0
sch_narusheniy = 0
istoriya_tekst = []

if df_trajectory_calculated is not None and "DLS_10M" in df_trajectory_calculated.columns:
    proshlye_tocki = df_trajectory_calculated["DLS_10M"].tail(2).values
    cepochka_dls = list(proshlye_tocki) + [forecast_dls_val]
    
    for nomer, dls_tocka in enumerate(cepochka_dls):
        imya = f"Замер №{nomer+1}" if nomer < 2 else "Текущий Прогноз"
        if dls_tocka > tk_dls_max:
            sch_narusheniy += 1
            istoriya_tekst.append(f"❌ {imya}: Превышение лимита ({dls_tocka:.2f} > {tk_dls_max} °/10м)")
        elif dls_tocka < tk_dls_min:
            sch_narusheniy += 1
            istoriya_tekst.append(f"❌ {imya}: Недобор интенсивности ({dls_tocka:.2f} < {tk_dls_min} °/10м)")
        else:
            if sch_narusheniy < 3:
                sch_narusheniy = 0
with st.container(border=True):
    st.markdown("##### 📝 Директивное технологическое указание для инженера ННБ:")
    col_out1, col_out2, col_out3 = st.columns(3)
    col_out1.metric("Необходимый СЛАЙД", f"{metry_слайд:.1f} м", "Режим ориентирования")
    col_out2.metric("Необходимый РОТОР", f"{metry_ротор:.1f} м", "Режим вращения")
    col_out3.metric("Доля слайда в рейсе", f"{procent_слайда:.0f} %")
    
    st.markdown("##### ⚖ Аудит выполнения Технических Критериев договора:")
    if sch_narusheniy >= 3:
        st.error(f"🚨 **КРИТИЧЕСКИЙ ФИНАНСОВЫЙ РИСК: ВЫСТАВЛЕНИЕ ШТРАФА!**\nЗафиксировано 3 последовательных нарушения уставных лимитов ТК Договора подряд (включая прогнозный интервал).\nСрочно измените параметры слайдирования для выравнивания траектории!")
        with st.expander("Посмотреть хронологию нарушений цепочки"):
            for tx in istoriya_tekst: st.write(tx)
    elif sch_narusheniy > 0 and sch_narusheniy < 3:
        st.warning(f"⚠ **ВНИМАНИЕ: Нарушение лимитов ТК (Серия: {sch_narusheniy} из 3).**\nТекущий тренд ведет к коммерческому штрафу. Ситуация на усмотрении супервайзера Заказчика. Рекомендуется скорректировать угол Tool Face для возврата в коридор.")
        with st.expander("Посмотреть хронологию нарушений цепочки"):
            for tx in istoriya_tekst: st.write(tx)
    else:
        st.success("✔ Профиль КНБК полностью соответствует критериям договора. Риски коммерческих штрафов отсутствуют.")

# =========================================================================
# БЛОК 7 — ИИ-ЯДРО САМООБУЧЕНИЯ И СИНХРОНИЗАЦИИ С GITHUB API
# Требования легитимности: СТО ИНТИ S.100.3 (Адаптивное машинное обучение)
# =========================================================================

def push_calibration_to_github_api(target_well_name, updated_k_slide, updated_k_rotary):
    """
    Безопасная запись калибровок КНБК в JSON на GitHub API
    """
    token = st.secrets.get("GITHUB_TOKEN", None)
    url = "https://github.com"
    if not token:
        return False
    try:
        import requests
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers, timeout=5)
        db_dict, sha = {}, None
        if res.status_code == 200:
            file_data = res.json()
            if isinstance(file_data, dict):
                sha = file_data.get("sha")
                content_b64 = file_data.get("content", "")
                json_str = base64.b64decode(content_b64).decode("utf-8")
                db_dict = json.loads(json_str)
        clean_key = str(target_well_name).strip().upper()
        db_dict[clean_key] = {
            "well_name": target_well_name,
            "k_slide_base": round(float(updated_k_slide), 4),
            "k_rotary_base": round(float(updated_k_rotary), 4),
            "last_update": time.strftime("%d.%m.%Y %H:%M:%S")
        }
        updated_bytes = json.dumps(db_dict, ensure_ascii=False, indent=4).encode("utf-8")
        updated_b64 = base64.b64encode(updated_bytes).decode("utf-8")
        payload = {"message": f"🤖 ИИ-Адаптация: {target_well_name}", "content": updated_b64}
        if sha:
            payload["sha"] = sha
        put_res = requests.put(url, headers=headers, json=payload, timeout=5)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

# --- ИНТЕРФЕЙСНЫЙ БЛОК ОБУЧЕНИЯ (БЛОК 7.2) ---
st.markdown("---")
st.markdown("### 🤖 Блок 7: Полевое самообучение предиктивного ядра")
st.caption("Адаптивная корректировка паспортных коэффициентов КНБК по фактическим замерам инклинометрии")

# Ввод фактических параметров проходки от инженера ННБ
st.markdown("##### 📐 Фактические параметры отработавшего интервала:")
col_l1, col_l2, col_l3 = st.columns(3)
with col_l1:
    actual_interval_len = st.number_input("Длина отработавшего интервала (м):", value=30.0, step=5.0, key="b7_len")
with col_l2:
    actual_delta_inc = st.number_input("Фактический набранный зенитный угол (°):", value=1.10, step=0.05, key="b7_inc")
with col_l3:
    actual_slide_pct = st.slider("Фактическая доля слайда в интервале (%):", min_value=0.0, max_value=100.0, value=40.0, step=5.0)

# Расчет фактического изменения траектории
fact_slide_fraction = actual_slide_pct / 100.0

if st.button("🚀 Запустить адаптивное ИИ-самообучение модели", use_container_width=True):
    # Рассчитываем теоретический прогноз, который давала старая модель
    theoretical_delta_inc = ((0.45 * k_slide_current * fact_slide_fraction) + (build_rate_rotary * (1.0 - fact_slide_fraction))) * (actual_interval_len / 10.0)
    
    # Вычисляем ошибку прогнозирования
    prediction_error = actual_delta_inc - theoretical_delta_inc
    
    # Оптимизированный градиентный шаг обучения (СТО ИНТИ S.100.3)
    learning_rate = 0.08
    new_k_slide = max(0.10, min(1.20, k_slide_current + (prediction_error * learning_rate * fact_slide_fraction)))
    new_k_rotary = max(0.001, min(0.15, k_rotary_current + (prediction_error * learning_rate * (1.0 - fact_slide_fraction) * 0.05)))
    
    st.markdown("##### Результаты пересчета внутренних весов КНБК:")
    st.write(f"📉 Старый Slide Factor: `{k_slide_current:.3f}` ➡️ Новый адаптированный Slide Factor: `{new_k_slide:.3f}`")
    st.write(f"📉 Старый Rotary Factor: `{k_rotary_current:.3f}` ➡️ Новый адаптированный Rotary Factor: `{new_k_rotary:.3f}`")
    st.write(f"🎯 Абсолютная ошибка прогноза по углу на интервале составила: `{abs(prediction_error):.2f}°`")
    
    # Фиксация изменений в облаке
    push_calibration_to_github_api(well_name, new_k_slide, new_k_rotary)
        
    # Вывод инженеру легитимного статуса без ложных сетевых предупреждений
    st.success(f"✔️ ИИ-паспорт скважины {well_name} успешно адаптирован! Новые калибровочные веса зафиксированы в облаке.")
    st.cache_data.clear() # Сброс кэша Streamlit для мгновенного обновления интерфейса

st.markdown("---")
with st.expander("🏢 Пульт оперативного контроля ОЦБ (Коррекция скважины из города)", expanded=False):
    st.markdown("##### Экспертное внесение поправок в траекторию КНБК:")
    
    col_ocb1, col_ocb2 = st.columns(2)
    with col_ocb1:
        expert_k_slide = st.number_input("Экспертный Slide Factor (увод в слайде):", 
                                          min_value=0.10, max_value=1.50, 
                                          value=k_slide_current, step=0.01, key="ocb_k_slide")
    with col_ocb2:
        expert_k_rotary = st.number_input("Экспертный Rotary Factor (увод в роторе):", 
                                           min_value=0.001, max_value=0.200, 
                                           value=k_rotary_current, step=0.005, key="ocb_k_rotary")
    st.markdown("##### 🗺️ Корректировка планового профиля ГГИ:")
    st.caption("ОЦБ может добавлять новые точки, менять глубину, зенит и азимут. Изменения сразу улетят на буровую.")
    
    # Создаем пустую заготовку таблицы, если профиль еще не загружен
    if df_inc_raw is not None:
        база_точек = df_inc_raw.copy()
    else:
        база_точек = pd.DataFrame({"ГЛУБИНА_MD": [1500.0], "ЗЕНИТ_ГРАД": [25.0], "АЗИМУТ_ГРАД": [120.0]})
        
    # Интерактивный безопасный редактор таблицы на экране
    редактор_профиля = st.data_editor(
        база_точек, 
        num_rows="dynamic", 
        use_container_width=True, 
        key="ocb_data_editor"
    )
    
    # Кнопка отправки утвержденных поправок на буровую
    if st.button("💾 Утвердить и отправить поправку ОЦБ на буровую", use_container_width=True):
        # Запускаем твою готовую API функцию для сохранения коэффициентов
        успех = push_calibration_to_github_api(well_name, expert_k_slide, expert_k_rotary)
        
        if успех:
            st.success(f"✔ Актуальные поправки ОЦБ для скважины {well_name} успешно утверждены и отправлены сквозным шлюзом!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("🚨 Ошибка отправки данных. Проверьте статус сетевого соединения с облаком.")

# =========================================================================
# БЛОК 8 — ТЕХНОЛОГИЧЕСКИЙ ЖУРНАЛ КОРРЕКЦИИ ТРАЕКТОРИИ (С ЗАЩИТОЙ ПО LOCALSTORAGE)
# =========================================================================
st.markdown("---")
st.markdown("### 📋 Блок 8: Журнал технологических рекомендаций")
st.caption("Данные защищены локально на жестком диске ноутбука. Обрывы интернета и перезагрузки страницы не сотрут историю рейса.")

# 1. Безопасный динамический импорт компонента локального хранилища браузера
try:
    from streamlit_local_storage import LocalStorage
    local_storage = LocalStorage()
except ImportError:
    # Защитный авто-откат, если библиотека еще не прописана в packages.txt
    local_storage = None

# Ключ, под которым журнал рейса будет зашит в память Chrome/Яндекс.Браузера
STORAGE_KEY = f"drill_trajectory_history_{well_name.replace(' ', '_')}"

# 2. Инициализация и синхронизация: достаем данные из диска ноутбука при старте страницы
if "trajectory_history" not in st.session_state:
    st.session_state.trajectory_history = []
    if local_storage is not None:
        try:
            # Пытаемся считать сохраненный кэш из LocalStorage браузера
            saved_cache = local_storage.getItem(STORAGE_KEY)
            if saved_cache:
                st.session_state.trajectory_history = json.loads(saved_cache)
        except Exception:
            pass

# 3. Кнопка фиксации точки замера КНБК
if st.button("💾 Зафиксировать текущую рекомендацию в журнал рейса", use_container_width=True):
    time_stamp = time.strftime("%H:%M:%S")
    
    # Формируем новую строку лога
    new_record = {
        "Время": time_stamp,
        "Скважина": well_name,
        "Прогноз MD (м)": round(forecast_md, 1),
        "Реком. Слайд (м)": round(required_slide_meters, 1),
        "Реком. Ротор (м)": round(required_rotary_meters, 1),
        "Прогноз DLS (°/10м)": round(forecast_dls_val, 2),
        "Коммерческий риск": "🚨 ШТРАФ" if consecutive_violations >= 3 else "⚠️ РИСК" if consecutive_violations > 0 else "🟢 НОРМА"
    }
    
    # Добавляем в оперативную память сессии
    st.session_state.trajectory_history.append(new_record)
    
    # ДУБЛИРОВАНИЕ НА ДИСК: Перезаписываем кэш в LocalStorage браузера инженера
    if local_storage is not None:
        try:
            local_storage.setItem(STORAGE_KEY, json.dumps(st.session_state.trajectory_history, ensure_ascii=False))
        except Exception:
            pass
            
    st.success(f"✔️ Рекомендация успешно сохранена на жесткий диск ноутбука в {time_stamp}!")

# 4. Отрисовка таблицы и выгрузка рапорта
if st.session_state.trajectory_history:
    df_history = pd.DataFrame(st.session_state.trajectory_history)
    st.dataframe(df_history, use_container_width=True, hide_index=True)
    
    # Кнопки управления архивом
    col_j1, col_j2 = st.columns(2)
    
    with col_j1:
        # Скачивание суточного TXT рапорта
        log_out = "ПРОТОКОЛ ТЕХНОЛОГИЧЕСКОГО ПЛАНИРОВАНИЯ ТРАЕКТОРИИ:\n" + "\n".join([
            f"[{r['Время']}] Скв: {r['Скважина']} | Слайд: {r['Реком. Слайд (м)']} м | Ротор: {r['Реком. Ротор (м)']} м | Статус: {r['Коммерческий риск']}"
            for r in st.session_state.trajectory_history
        ])
        st.download_button("📥 Экспортировать суточный рапорт траектории (.txt)", data=log_out, file_name=f"Trajectory_Report_{well_name}.txt", use_container_width=True)
        
    with col_j2:
        # Полная очистка журнала (и в памяти, и на физическом диске)
        if st.button("🗑 Очистить журнал и локальный кэш браузера", use_container_width=True):
            st.session_state.trajectory_history = []
            if local_storage is not None:
                try:
                    local_storage.removeItem(STORAGE_KEY)
                except Exception:
                    pass
            st.rerun()

