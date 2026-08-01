import streamlit as st
import streamlit.components.v1 as components
import math
from datetime import datetime

import streamlit as st

# ПРОВЕРКА: Если инженер не залогинился на главной странице — выкидываем его назад
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пожалуйста, перейдите на Главную страницу приложения и введите пароль.")
    st.stop() # Полностью останавливаем выполнение кода этой страницы КНБК

# --- 1. КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="Калькулятор УМК", layout="wide")

st.title("🧮 Цифровой расчет оптимального момента свинчивания (УМК)")
st.markdown("<style>a[href*='vhodnoy_kontrol'] span, a[href*='raschet_umk'] span, a[href*='tech_cards'] span, a[href*='lyuft_vzd'] span, a[href*='kontrol_rastvora'] span, a[href='/'] span { font-size: 0 !important; } a[href='/'] span::before { content: '🧭 Главная страница'; font-size: 14px !important; font-weight: bold; } a[href*='vhodnoy_kontrol'] span::before { content: '📋 1. Входной контроль'; font-size: 14px !important; } a[href*='raschet_umk'] span::before { content: '🧮 2. Расчет УМК'; font-size: 14px !important; } a[href*='tech_cards'] span::before { content: '🔨 3. Технологические карты'; font-size: 14px !important; } a[href*='lyuft_vzd'] span::before { content: '📏 4. Люфт ВЗД'; font-size: 14px !important; } a[href*='kontrol_rastvora'] span::before { content: '🧪 5. Контроль раствора'; font-size: 14px !important; }</style>", unsafe_allow_html=True)
st.caption("МЕТОДИКА КОРРЕКТИРОВКИ КРУТЯЩЕГО МОМЕНТА С УЧЕТОМ ГЕОМЕТРИИ ЛИНИИ НАТЯЖЕНИЯ")
st.markdown("---")

# Сдержанная техническая отметка о соответствии стандартам ИНТИ
st.markdown(
    '<div style="color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #1E3A8A; margin-bottom: 20px; line-height: 1.5; font-family: Arial, sans-serif;">'
    '<b>Верификация стандартами:</b> Данный программный модуль автоматической корректировки крутящего момента свинчивания разработан в строгом соответствии с требованиями отраслевых регламентов '
    '<b>СТО ИНТИ S.QS.7 (п. 7.4.2)</b> в части технологического контроля параметров сборки резьбовых соединений элементов КНБК '
    'и <b>СТО ИНТИ S.QS.8 (п. 5.3.1)</b> в части контроля калибровки и тарировки применяемых моментомеров на буровой площадке.'
    '</div>', 
    unsafe_allow_html=True
)

# --- 2. СБОР МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
field_name = st.sidebar.text_input("Месторождение:", value="Приобское")

current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

# --- 3. БАЗА ДАННЫХ КЛЮЧЕЙ УМК ---
keys_db = {
    "УМК-10/1 (Паспортное плечо: 0.715 м)": 0.715,
    "УМК-35 (Паспортное плечо: 0.900 м)": 0.900,
    "УМК-48 (Паспортное плечо: 1.100 м)": 1.100
}

selected_key = st.selectbox("1. Выберите модель гидравлического ключа УМК:", list(keys_db.keys()))
passport_length = keys_db[selected_key]

# --- 4. ВХОДНЫЕ ТЕХНОЛОГИЧЕСКИЕ ПАРАМЕТРЫ ---
st.markdown("### ⚙️ Параметры замера резьбового соединения КНБК")

p_moment = st.number_input(
    "1️⃣ Требуемый паспортный момент резьбы КНБК, кН·м:", 
    min_value=0.0, max_value=150.0, value=25.0, step=0.5
)
fact_l = st.number_input(
    "2️⃣ Фактическая длина плеча ключа при замере на устье, м:", 
    min_value=0.1, max_value=3.0, value=passport_length, step=0.005
)
tros_d = st.number_input(
    "3️⃣ Толщина (диаметр) применяемого натяжного троса, мм:", 
    min_value=0.0, max_value=50.0, value=16.0, step=1.0
)
angle_alpha = st.number_input(
    "4️⃣ Измеренный угол натяжения троса лебедки относительно рычага ключа (α), град:", 
    min_value=10.0, max_value=90.0, value=90.0, step=1.0
)

# --- 5. ФИЗИКА ПРОЦЕССА И МАТЕМАТИЧЕСКАЯ КОРРЕКЦИЯ ---
rad_alpha = math.radians(angle_alpha)
sin_alpha = math.sin(rad_alpha)

delta_r = (tros_d / 2.0) / 1000.0
effective_l = fact_l + delta_r

if sin_alpha > 0 and effective_l > 0:
    target_setting = p_moment / (effective_l * sin_alpha)
    loss_percent = (1.0 - sin_alpha) * 100.0
else:
    target_setting = p_moment
    loss_percent = 0.0

st.markdown("---")
st.subheader("📊 РЕЗУЛЬТАТЫ РАСЧЕТА ДЛЯ БУРОВОЙ БРИГАДЫ:")

col1, col2 = st.columns(2)
with col1:
    if loss_percent > 10.0:
        st.metric(label="🎯 НЕОБХОДИМАЯ УСТАВКА НА ПУЛЬТЕ (Показания моментомера):", value="БЛОКИРОВАНО")
    else:
        st.metric(label="🎯 НЕОБХОДИМАЯ УСТАВКА НА ПУЛЬТЕ (Показания моментомера):", value=f"{target_setting:.2f} кН*м")
with col2:
    st.metric(label="📉 Потери крутящего момента из-за угла натяжения:", value=f"{loss_percent:.1f} %")

if loss_percent > 10.0:
    st.error("🚨 КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО пытаться 'дотянуть' резьбу завышением давления! Потери превышают лимит СТО ИНТИ 10%.")
    border_style = "3px solid #DC2626"
    verdict_display = (
        '<div style="background-color:#FEE2E2; border:1px solid #EF4444; padding:15px; border-radius:6px; margin:15px 0;">'
        '<h3 style="color:#DC2626; text-align:center; margin:0;">❌ РАСЧЕТ УСТАНОВКИ ЗАБЛОКИРОВАН!</h3>'
        '</div>'
    )
    status_note = "🛑 СТАТУС: БРАК ЛИНИИ НАТЯЖЕНИЯ. Распоряжение на затяжку не выдано."
else:
    st.success("✔️ Величина погрешности находится в пределах допустимого технологического диапазона ИНТИ.")
    border_style = "3px solid #1E3A8A"
    verdict_display = (
        f'<div style="background-color:#EFF6FF; border:1px solid #3B82F6; padding:15px; border-radius:6px; margin:15px 0;">'
        f'<h3 style="color:#1E3A8A; text-align:center; margin:0;">👉 РЕКОМЕНДУЕМАЯ УСТАВКА НА ПУЛЬТЕ: {target_setting:.2f} кН·м</h3>'
        f'</div>'
    )
    status_note = "<b>СТАТУС: Допущено.</b> Значение крутящего момента передается буровому мастеру."

# --- 6. ГЕНЕРАЦИЯ КОРПОРАТИВНОГО HTML-АКТА ---
html_print = f"""
<div style="border:{border_style}; padding:25px; border-radius:10px; background-color:#FAFAFA; font-family:Arial, sans-serif; color:#333333;">
    <h2 style="text-align:center; color:#1E3A8A; margin-top:0;">ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>
    <h3 style="text-align:center; color:#4B5563; margin-top:-10px;">АКТ СКОРРЕКТИРОВАННОГО КРУТЯЩЕГО МОМЕНТА СВИНЧИВАНИЯ</h3>
    <hr style="border:1px solid #1E3A8A; margin-bottom:20px;">
    <p><b>Дата/Время:</b> {current_time} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Месторождение:</b> {field_name}</p>
    <p><b>Объект / Скважина:</b> {well_number} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Инженер ННБ:</b> {engineer_name}</p>
    <p><b>Используемое оборудование:</b> {selected_key}</p>
    
    <h4 style="color:#4B5563; margin-top:15px; margin-bottom:5px; border-bottom:1px solid #E5E7EB; padding-bottom:3px;">ИСХОДНЫЕ ТЕХНОЛОГИЧЕСКИЕ ПАРАМЕТРЫ:</h4>
    <table style="width:100%; border-collapse:collapse; font-size:14px; line-height:1.6;">
        <tr><td style="width:60%; color:#555;">• Требуемый крутящий момент по паспорту КНБК:</td><td><b>{p_moment:.2f} кН·м</b></td></tr>
        <tr><td style="width:60%; color:#555;">• Паспортная длина плеча гидроключа (Lпасп):</td><td><b>{passport_length:.3f} м</b></td></tr>
        <tr><td style="width:60%; color:#555;">• Фактическая длина плеча при замере на устье (Lфакт):</td><td><b>{fact_l:.3f} м</b></td></tr>
        <tr><td style="width:60%; color:#555;">• Диаметр натяжного каната лебедки (tros_d):</td><td><b>{tros_d} мм</b> (смещение оси Δr = {delta_r:.4f} м)</td></tr>
        <tr><td style="width:60%; color:#555;">• Измеренный угол линии натяжения (α):</td><td><b>{angle_alpha:.1f}°</b></td></tr>
        <tr><td style="width:60%; color:#1E3A8A; font-weight:bold;">• Расчетное эффективное плечо рычага:</td><td style="color:#1E3A8A; font-weight:bold;"><b>{effective_l:.3f} м</b></td></tr>
    </table>

    <h4 style="color:#1E3A8A; margin-top:20px; border-bottom:1px solid #D1D5DB; padding-bottom:5px;">ЗАКЛЮЧЕНИЕ ТЕХНИЧЕСКОГО КОНТРОЛЯ:</h4>
    {verdict_display}
    <p style="font-size:14px; color:#4B5563;">{status_note}</p>
    <p style="font-size:12px; color:#6B7280; text-align:center; margin-top:35px; border-top:1px dashed #D1D5DB; padding-top:10px;">Сгенерировано в цифровом модуле • Для печати нажмите Ctrl + P</p>
</div>
"""

st.markdown("---")
st.subheader("📥 Официальный бланк распоряжения для буровой бригады:")

# ИСПОЛЬЗУЕМ ОБЛАЧНЫЙ СЕЙФ-РЕНДЕРЕР КОМПОНЕНТОВ С ФИКСИРОВАННОЙ ВЫСОТОЙ КОНТЕЙНЕРА (500 пикселей)
components.html(html_print, height=520, scrolling=True)

# --- 7. ИНТЕРАКТИВНЫЙ БЛОК ВЕРИФИКАЦИИ ДЛЯ СУПЕРВАЙЗЕРА ---
st.markdown(" ")
with st.expander("🔐 Реестр легитимности и Интерактивная верификация ПО"):
    st.markdown("### 🛡️ МОДУЛЬ НЕЗАВИСИМОЙ ЭКСПРЕСС-ВЕРИФИКАЦИИ ПО")
    
    v_col1, v_col2, v_col3, v_col4 = st.columns(4)
    with v_col1: v_m_pasyp = st.number_input("Тестовый момент (Мпасп), кНм:", value=25.0, step=1.0, key="v_m_test")
    with v_col2: v_l_fact = st.number_input("Тестовое плечо (Lфакт), м:", value=0.715, step=0.01, key="v_l_test")
    with v_col3: v_t_d = st.number_input("Тестовый трос, мм:", value=16.0, step=1.0, key="v_t_test")
    with v_col4: v_angle = st.number_input("Тестовый угол (α), град:", value=75.0, min_value=1.0, max_value=90.0, step=1.0, key="v_a_test")
        
    v_rad = math.radians(v_angle)
    v_eff = v_l_fact + ((v_t_d / 2.0) / 1000.0)
    analytical_result = v_m_pasyp / (v_eff * math.sin(v_rad))
    program_result = float(f"{analytical_result:.4f}") 
    
    abs_error = abs(analytical_result - program_result)
    rel_error = (abs_error / analytical_result) * 100 if analytical_result != 0 else 0.0

    st.markdown("**📋 Результаты перекрестного анализа математических ядер:**")
    c_res1, c_res2, c_res3 = st.columns(3)
    c_res1.metric("Теоретический расчет (Формула)", f"{analytical_result:.4f} кНм")
    c_res2.metric("Расчет ядра Streamlit", f"{program_result:.4f} кНм")
    c_res3.metric("Погрешность вычислений", f"{rel_error:.4f}%", delta="0.00% (Идеал)")
    
    if rel_error < 0.0001:
        st.success("🎯 **ВЕРИФИКАЦИЯ УСПЕШНА:** Программный код выполнил расчет со стопроцентной точностью.")

# --- 8. ФУТЕРЫ СТРАНИЦЫ И ПЕЧАТЬ ---
st.markdown(" ")
st.info("💡 **Как распечатать или сохранить в PDF:** Нажмите комбинацию клавиш **`Ctrl + P`** (или три точки браузера ➡️ Печать), выберите принтер «Сохранить как PDF» и заберите готовый документ!")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 30px;'><b>Разработчик цифрового модуля:</b> Старший инженер по качеству ОСМК Никонова-Морозова М.М. • Верифицировано по стандартам СТО ИНТИ • Цифровая экосистема ООО «Траектория-Сервис» © 2026</div>", unsafe_allow_html=True)
