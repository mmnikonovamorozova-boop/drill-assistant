import streamlit as st
from datetime import datetime

# --- 2. КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="Контроль раствора", layout="wide")
st.title("🧪 Контроль параметров раствора и износа КНБК")
st.caption("МОНИТОРИНГ АБРАЗИВНОЙ АГРЕССИВНОСТИ И ГИДРАВЛИКИ ННБ")
st.markdown("---")

# Техническая отметка о соответствии стандартам ИНТИ
st.markdown(
    "<div style='color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #1E3A8A; margin-bottom: 20px; font-family: Arial, sans-serif;'>"
    "<b>Верификация:</b> Модуль разработан по <b>СТО ИНТИ S.QS.7</b> (мониторинг) и <b>СТО ИНТИ S.100.3</b> (безаварийность).</div>",
    unsafe_allow_html=True
)
st.markdown("---")

# --- 3. СБОР МЕТАДАННЫХ (SIDEBAR И НАЛЕДОВАНИЕ) ---
st.sidebar.header("📋 Метаданные рапорта")

# Пытаемся забрать данные из сессии, если их нет — ставим дефолт
well_number = st.sidebar.text_input(
    "Номер скважины / Куст:", 
    value=st.session_state.get("well_number", "Скв. № 101, Куст 5")
)
engineer_name = st.sidebar.text_input(
    "ФИО Инженера по ННБ:", 
    value=st.session_state.get("engineer_name", "Иванов И.И.")
)
field_name = st.sidebar.text_input(
    "Месторождение:", 
    value=st.session_state.get("field_name", "Приобское")
)
vzd_passport_number = st.sidebar.text_input(
    "Серийный номер ВЗД по паспорту:", 
    value=st.session_state.get("vzd_passport_number", "№ 6677")
)
selected_client = st.session_state.get("selected_client", "ПАО Роснефть")
current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

# --- 4. ВВОД ФАКТИЧЕСКИХ ПАРАМЕТРОВ РАСТВОРА ---
st.subheader("📥 Ввод фактических параметров (данные ГТИ / Растворщика)")

col_r1, col_r2, col_r3, col_r4 = st.columns(4)

with col_r1:
    fact_sand = st.number_input(
        "Содержание песка (%), ИЧ:", 
        min_value=0.0, max_value=5.0, value=0.05, step=0.01,
        help="Критический параметр абразивного износа по ИНТИ"
    )
with col_r2:
    fact_solids = st.number_input(
        "Твердая фаза (% об.):", 
        min_value=0.0, max_value=30.0, value=4.5, step=0.1
    )
with col_r3:
    fact_density = st.number_input(
        "Плотность раствора (г/см³):", 
        min_value=0.8, max_value=2.5, value=1.18, step=0.01
    )
with col_r4:
    hours_worked = st.number_input(
        "Время циркуляции на интервале (ч):", 
        min_value=1, max_value=120, value=12, step=1
    )

st.markdown("---")

# --- 5. МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ИЗНОСА СТАТОРА ВЗД ---
st.subheader("📊 Аналитика абразивной деградации оборудования")

# Базовые константы и лимиты согласно СТО ИНТИ S.QS.7/8
limit_sand_normal = 0.10  # Норма ИНТИ (до 0.1%)
limit_sand_critical = 0.50  # Критический предел (0.5%)
base_wear_rate_per_hour = 0.33  # Базовый износ эластомера в % за 1 час (ресурс ~300 ч)

# Расчет коэффициента агрессивности среды (степенная зависимость износа от абразива)
if fact_sand > limit_sand_normal:
    # Степень агрессивности среды m = 1.5 для кварцевого песка
    wear_coefficient = (fact_sand / limit_sand_normal) ** 1.5
else:
    wear_coefficient = 1.0

# Расчет накопленного ущерба за интервал времени циркуляции
calculated_wear_interval = base_wear_rate_per_hour * wear_coefficient * hours_worked

# Вывод результатов и светофор рисков для инженера ННБ
col_m1, col_m2 = st.columns(2)

with col_m1:
    st.metric(
        label="Коэффициент ускорения износа", 
        value=f"x{wear_coefficient:.2f}",
        delta=f"+{(wear_coefficient - 1.0) * 100:.1f}%" if wear_coefficient > 1.0 else "Норма"
    )

with col_m2:
    st.metric(
        label="Потеря ресурса за интервал", 
        value=f"{calculated_wear_interval:.2f} %",
        delta=f"Экстремальный темп!" if fact_sand > limit_sand_critical else None,
        delta_color="inverse"
    )

# Визуальные триггеры опасности на основе регламентов
if fact_sand > limit_sand_critical:
    res_sol_text = f"🚨 КРИТИЧЕСКИЙ АБРАЗИВНЫЙ ИЗНОС! Содержание песка ({fact_sand}%) превышает лимит {limit_sand_critical}%. Износ ускорен в {wear_coefficient:.1f} раз! Срочно требуйте очистки или остановите бурение."
    st.error(res_sol_text)
elif fact_sand > limit_sand_normal:
    res_sol_text = f"⚠️ ПОВЫШЕННАЯ АБРАЗИВНАЯ АГРЕССИВНОСТЬ среды. Песок ({fact_sand}%) выше нормы ИНТИ ({limit_sand_normal}%). Ресурс статора ВЗД вырабатывается быстрее."
    st.warning(res_sol_text)
else:
    res_sol_text = "✔ ПАРАМЕТРЫ АБРАЗИВА В НОРМЕ. Скорость деградации эластомера соответствует проектным значениям."
    st.success(res_sol_text)

st.markdown("---")

# --- 6. ЭКСПРЕСС-РАСЧЕТ ГИДРОДИНАМИКИ И ЭЦП ---
st.subheader("🌊 Гидродинамический экспресс-расчет (ЭЦП и Очистка)")

col_h1, col_h2, col_h3 = st.columns(3)

with col_h1:
    flow_rate = st.number_input(
        "Расход буровых насосов (л/с):", 
        min_value=0, max_value=100, value=28, step=1
    )
with col_h2:
    rop_fact = st.number_input(
        "Текущая мех. скорость бурения (м/ч):", 
        min_value=0, max_value=200, value=25, step=5
    )
with col_h3:
    yield_point = st.number_input(
        "ДНС раствора (паскали / lb/100ft²):", 
        min_value=0.0, max_value=50.0, value=12.0, step=0.5
    )

# Упрощенная полевая модель расчета гидравлических потерь в затрубе (ΔP_затруб)
# Базируется на геометрии стандартного ствола 215.9 мм и бурильных труб 127 мм
annular_loss = (0.00015 * (flow_rate ** 1.8) * fact_density) + (0.05 * yield_point)

# Расчет Эквивалентной Циркуляционной Плотности (ЭЦП / ECD)
# Принимаем среднюю условную глубину по вертикали (TVD) за 2500 метров для экспресс-оценки
calculated_ecd = fact_density + (annular_loss / (0.00981 * 2500))

# Логическая оценка рисков очистки ствола при слайдировании
critical_rop_limit = flow_rate * 0.9  # Эмпирическое правило: мех. скорость не должна превышать расход * 0.9

col_res1, col_res2 = st.columns(2)

with col_res1:
    st.metric(
        label="Расчетная ЭЦП (ECD)", 
        value=f"{calculated_ecd:.3f} г/см³",
        delta=f"+{calculated_ecd - fact_density:.3f} (Динамика)",
        delta_color="inverse"
    )

with col_res2:
    if rop_fact > critical_rop_limit:
        clean_status = "⚠️ Риск зашламления КНБК!"
        st.metric(label="Статус очистки затруба", value="Недостаточный", delta=clean_status, delta_color="inverse")
    else:
        clean_status = "✔ Вынос шлама эффективен"
        st.metric(label="Статус очистки затруба", value="В допуске", delta=clean_status)

# Вывод технологических предупреждений по гидравлике
if calculated_ecd > (fact_density + 0.08):
    st.error(f"🛑 ВНИМАНИЕ: Высокое гидродинамическое сопротивление! Риск поглощения раствора. Ограничьте мех. скорость до {critical_rop_limit:.0f} м/ч.")
elif rop_fact > critical_rop_limit:
    st.warning("⚠️ ВНИМАНИЕ: Высокая скорость проходки при текущем расходе. Риск образования шламовой подушки и прихвата КНБК при слайдировании.")
else:
    st.success("✔ Гидравлический режим стабилен. Риски поглощения пластов и прихвата инструмента минимальны.")

st.markdown("---")

# --- 7. ФОРМИРОВАНИЕ ОФИЦИАЛЬНОГО HTML-АКТА ---
st.subheader("📥 Официальный бланк аудита для суточного рапорта:")

# Переводим статус износа в цвет для бланка акта
if fact_sand > limit_sand_critical:
    act_status_color = "#DC2626"  # Красный
    status_summary = "НЕ СООТВЕТСТВУЕТ (КРИТИЧЕСКИЙ АБРАЗИВ)"
elif fact_sand > limit_sand_normal:
    act_status_color = "#D97706"  # Желтый
    status_summary = "ДОПУЩЕНО С ОГРАНИЧЕНИЕМ РЕСУРСА ВЗД"
else:
    act_status_color = "#16A34A"  # Зеленый
    status_summary = "СООТВЕТСТВУЕТ НОРМАМ ИНТИ"

# Сборка корпоративного HTML-шаблона акта (упрощенный пример)
html_solutions = f"""
<div style='border:3px solid #1E3A8A; padding:25px; font-family:Arial;'>
    <h2 style='text-align:center; color:#1E3A8A;'>ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>
    <h3>АКТ ТЕХНОЛОГИЧЕСКОГО АУДИТА ПРОМЫВОЧНОЙ ЖИДКОСТИ</h3>
    <p><b>Дата:</b> {current_time} | <b>Скважина:</b> {well_number} | <b>Инженер:</b> {engineer_name}</p>
    <p><b>Параметры:</b> Песок={fact_sand:.2f}% | Плотность={fact_density:.2f} г/см³</p>
    <h4 style='color:#1E3A8A;'>ЗАКЛЮЧЕНИЕ:</h4>
    <p style='color:{act_status_color};'><b>СТАТУС: {status_summary}</b></p>
    <p><b>Износ ВЗД:</b> {calculated_wear_interval:.2f}% за {hours_worked} ч.</p>
    <p>___________________ / {engineer_name} /</p>
</div>
"""

# Вывод акта в Streamlit
st.markdown(html_solutions, unsafe_allow_html=True)

# --- 8. ИНСТРУКЦИЯ И ФУТЕР ---
st.info("💡 **Сохранение:** Кнопка «Поделиться» ➡ Печать/PDF.")
st.markdown("---")
# Брендированный футер
st.markdown(
    "<div style='text-align:center; color:#9CA3AF; font-size:11px;'>"
    "<b>Разработчик:</b> ООО «Траектория-Сервис» © 2026"
    "</div>", 
    unsafe_allow_html=True
)
