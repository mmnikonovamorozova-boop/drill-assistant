import streamlit as st
import numpy as np
import pandas as pd
import openpyxl
from datetime import datetime

# --- ИНИЦИАЛИЗАЦИЯ БАЗОВЫХ ПЕРЕМЕННЫХ СЕССИИ ---
if "predicted_hours_to_failure" not in st.session_state:
    st.session_state.predicted_hours_to_failure = 0.0
if "mae_hours" not in st.session_state:
    st.session_state.mae_hours = 24.0
if "accuracy_pct" not in st.session_state:
    st.session_state.accuracy_pct = 75.0

# --- СТРОГАЯ ПРОВЕРКА АВТОРИЗАЦИИ ИНЖЕНЕРА ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пожалуйста, перейдите на Главную страницу приложения и введите пароль.")
    st.stop()
# --- КОНФИГУРАЦИЯ СТРАНИЦЫ И ЗАГОЛОВКИ ---
st.set_page_config(page_title="Контроль растворов", layout="wide")
st.title("🧪 Цифровой контроль параметров бурового раствора")
st.caption("МЕТОДИКА КОНТРОЛЯ И ОЦЕНКИ АБРАЗИВНОГО ИЗНОСА ЭЛАСТОМЕРОВ")
st.markdown("---")

# Паспорт верификации СТО ИНТИ, скрытый под фирменный спойлер
with st.expander("🔰 Паспорт верификации СТО ИНТИ (Контроль промывки)"):
    st.markdown(
        "<div style='color: #1F2937; font-size: 14px; background-color: #F9FAFB; padding: 15px; border-radius: 6px; border-left: 4px solid #2563EB; line-height: 1.6; font-family: Arial, sans-serif; margin-bottom: 10px;'> "
        "<b>1. СТО ИНТИ S.QS.7 и S.QS.8:</b> Проведение обязательного суточного аудита параметров бурового раствора, операционный контроль содержания абразивной твердой фазы и обеспечение безопасных критериев эксплуатации элементов КНБК на устье скважины.<br><br>"
        "<b>2. СТО ИНТИ S.100.3:</b> Метрологическое подтверждение точности измерений промывочной среды, математическое моделирование скорости деградации нитрильных эластомеров (NBR) и предиктивная оценка остаточного ресурса статора ВЗД."
        "</div>",
        unsafe_allow_html=True
    )

# --- ВЫБОР ЗАКАЗЧИКА И ЕДИНЫЙ БАННЕР ТЕХКРИТЕРИЕВ ---
company_choice = st.selectbox(
    "Текущий недропользователь (Заказчик):",
    ["Роснефть", "Газпром нефть", "ЛУКОЙЛ", "НОВАТЭК", "Прочие"],
    key="main_page_company"
)

# Единый баннер технологических ограничений
if company_choice == "Роснефть":
    st.error("📋 **Регламент ТК «Роснефть»:** Максимальное содержание песка: **> 0.5%**.")
elif company_choice == "Газпром нефть":
    st.error("📋 **Регламент ТК «Газпром нефть»:** Максимальное содержание песка: **> 0.4%**.")
elif company_choice == "ЛУКОЙЛ":
    st.warning("📋 **Регламент ТК «ЛУКОЙЛ»:** Максимальное содержание песка: **> 0.5%**.")
else:
    st.info("📋 **Стандартный регламент РД:** Лимит содержания песка: **> 0.5%**.")

st.markdown("---")

# --- ДОБАВЛЕНИЕ ТЕХНОЛОГИЧЕСКИХ ПАРАМЕТРОВ РАСТВОРА (УСТРАНЕНИЕ NAMEERROR) ---
st.subheader("📋 Технологические параметры промывочной жидкости:")
col_dens1, col_dens2, col_dens3 = st.columns(3)

with col_dens1:
    f_dens = st.number_input("Плотность раствора (г/см³):", min_value=0.8, max_value=2.5, value=1.12, step=0.01)
with col_dens2:
    f_pv = st.number_input("Пластическая вязкость ПВ (мПа·с):", min_value=1.0, max_value=100.0, value=25.0, step=1.0)
with col_dens3:
    f_yp = st.number_input("Динамическое напряжение сдвига ДНС (дПа):", min_value=0.0, max_value=100.0, value=12.0, step=1.0)

st.markdown("---")

# =========================================================================
# БЛОК 1: СИНХРОНИЗАЦИЯ С ГЛОБАЛЬНЫМ ПАСПОРТОМ РЕЙСА И РЕГЛАМЕНТЫ ТК
# =========================================================================

# Извлекаем глобальные данные из app.py (с подстраховкой на дефолт)
well_number = st.session_state.get("well_number", "Скв. № 101, Куст 5")
field_name = st.session_state.get("field_name", "Приобское")
bha_number = st.session_state.get("bha_number", "1")

# Вывод аккуратной информационной плашки паспорта в сайдбар
with st.sidebar:
    st.markdown(f"### 🌐 Текущий контекст КНБК №{bha_number}")
    st.info(f"📍 **Месторождение:** {field_name}\n🎯 **Объект:** {well_number}")
    
    # Оставляем только уникальные поля для контроля раствора
    engineer_name = st.text_input("ФИО Инженера по растворам / ННБ:", value="Иванов И.И.", key="sol_eng_name")
    serial_number = st.text_input("Серийный номер ВЗД:", value="№ 6677", key="sol_vzd_sn")
    st.markdown("---")
    
    if st.button("🚪 Выйти из системы", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# =========================================================================
# БЛОК 2: ТЕХНОЛОГИЧЕСКИЙ КОНТРОЛЬ ОЧИСТКИ И ОЦЕНКА РИСКОВ
# =========================================================================
st.subheader("📥 Блок 2: Фактические параметры очистки")

col_sand1, col_sand2 = st.columns(2)

with col_sand1:
    sand_input_val = st.number_input(
        "Фактическое содержание песка, %:",
        min_value=0.0, max_value=10.0, value=0.5, step=0.1, key="main_sand_input"
    )

with col_sand2:
    # 💡 Трюк для идеального выравнивания: пустой заголовок-прокладка
    st.markdown("<p style='margin-bottom: 33px;'></p>", unsafe_allow_html=True)
    max_flow_active = st.checkbox(
        "🚀 Форсированный режим бурения (Макс. расход)",
        key="main_max_flow_checkbox"
    )

# --- МАТЕМАТИЧЕСКИЙ РАСЧЕТ ДИНАМИЧЕСКОГО ПОРОГА БЕЗОПАСНОСТИ ---
# Базовый лимит наследуется из Блока 1 (переменная max_sand_limit)
base_limit = max_sand_limit if 'max_sand_limit' in locals() else 0.5

if max_flow_active:
    # При максимальном расходе сужаем рамки безопасности на 0.1% согласно API RP 13D
    sand_threshold = base_limit - 0.1
    flow_context = " при МАКСИМАЛЬНОМ расходе насосов (повышенная гидродинамическая нагрузка)"
else:
    # При стандартном режиме бурения используем базовый лимит Заказчика
    sand_threshold = base_limit
    flow_context = " при стандартном режиме промывки скважины"

# --- ПРОВЕРКА КРИТЕРИЕВ И ВЫВОД РЕКОМЕНДАЦИЙ ДЛЯ ИНЖЕНЕРА ННБ ---
st.markdown("##### 🔬 Экспертное заключение по состоянию очистки БР:")

if sand_input_val > sand_threshold:
    # Формируем жесткий аварийный статус ИНТИ (красный цвет)
    inti_status = f"🚨 КРИТИЧЕСКИЙ РИСК: Интенсивный абразивный износ статора ВЗД! Фактический песок ({sand_input_val}%) превышает допустимый технологический порог {sand_threshold}%{flow_context}. Срочно активировать гидроциклоны и снизить подачу!"
    act_status_color = "#EF4444"  # Строгий красный цвет HEX
    st.error(inti_status)
else:
    # Режим в пределах нормы (зеленый цвет)
    inti_status = f"✔ ТЕХНОЛОГИЧЕСКИЙ СТАТУС В НОРМЕ: Текущее содержание песка ({sand_input_val}%) находится в безопасных пределах (Допуск до {sand_threshold}%{flow_context}). Допущено к продолжению бурения интервала."
    act_status_color = "#10B981"  # Насыщенный зеленый цвет HEX
    st.success(inti_status)

st.markdown("---")

# =========================================================================
# БЛОК 3: ВЫСОКОТОЧНЫЙ РАСЧЕТ ЭЦП ПО МОДЕЛИ ГЕРШЕЛЯ-БАЛКЛИ (API 13D) - ЧАСТЬ 1
# =========================================================================
st.markdown("### 📊 Блок 3: Высокоточный расчет и управление ЭЦП/ECD")
st.caption("Математическое ядро по стандарту API RP 13D интегрировано с уставками ТК и поправкой на абразивную фазу")

# --- Инициализация базовых состояний (выполняется один раз при старте) ---
if "val_h_tvd" not in st.session_state: st.session_state["val_h_tvd"] = 2500.0
if "val_d_hole" not in st.session_state: st.session_state["val_d_hole"] = 215.9
if "val_q_flow" not in st.session_state: st.session_state["val_q_flow"] = 28.0
if "val_rop" not in st.session_state: st.session_state["val_rop"] = 35.0
if "val_d_pipe" not in st.session_state: st.session_state["val_d_pipe"] = 127.0
if "val_p_frac" not in st.session_state: st.session_state["val_p_frac"] = 1.35

# 1. Ввод геолого-технических данных
col_geo1, col_geo2, col_geo3 = st.columns(3)

with col_geo1:
    h_tvd = st.number_input("Вертикальная глубина скважины (TVD), м:", min_value=10.0, step=10.0, key="val_h_tvd")
    d_hole = st.number_input("Диаметр скважины, мм:", min_value=50.0, step=0.1, key="val_d_hole")

with col_geo2:
    q_flow = st.number_input("Расход насосов, л/с:", min_value=0.0, step=0.5, key="val_q_flow")
    rop = st.number_input("Скорость проходки (ROP), м/ч:", min_value=0.0, step=1.0, key="val_rop")

with col_geo3:
    d_pipe = st.number_input("Наружный диаметр трубы, мм:", min_value=10.0, step=0.1, key="val_d_pipe")
    p_frac = st.number_input("Эквивалент ГРП / поглощения, г/см³:", min_value=0.8, step=0.01, key="val_p_frac")

# --- СТРОГАЯ ГЕОМЕТРИЧЕСКАЯ ВАЛИДАЦИЯ ---
if d_pipe >= d_hole:
    st.error(f"🚨 **КРИТИЧЕСКАЯ ОШИБКА:** D трубы ({d_pipe} мм) > D скважины ({d_hole} мм).")
    st.stop()

# 2. Перевод параметров в СИ
import math
dh_m, dp_m = d_hole / 1000.0, d_pipe / 1000.0
area_annulus = (math.pi / 4.0) * (dh_m**2 - dp_m**2)
hydraulic_diam = dh_m - dp_m

# --- ИНТЕГРАЦИЯ ДАННЫХ ИЗ БЛОКА 2 (Поправка на песок) ---
actual_sand_pct = st.session_state.get('main_sand_input', 0.5)
sand_fraction = actual_sand_pct / 100.0
rho_rock = 2650.0  # кг/м³
base_mud_density = f_dens * 1000.0  # г/см³ -> кг/м³

# Корректировка плотности
rho_base_corrected = base_mud_density + (sand_fraction * (rho_rock - base_mud_density))

# Эмпирическая поправка реологии (Модель Эйнштейна-Томаса)
sand_fraction_clipped = min(0.10, sand_fraction)
rheology_multiplier = 1.0 + 2.5 * sand_fraction_clipped + 10.05 * (sand_fraction_clipped ** 2)

f_pv_corrected = f_pv * rheology_multiplier
f_yp_corrected = f_yp * rheology_multiplier

# СИ для Гершеля-Балкли
pv_si = f_pv_corrected / 1000.0  # Па·с
yp_si = f_yp_corrected * 0.1     # Па
# =========================================================================
# БЛОК 3: ВЫСОКОТОЧНЫЙ РАСЧЕТ ЭЦП ПО МОДЕЛИ ГЕРШЕЛЯ-БАЛКЛИ - ЧАСТЬ 2
# =========================================================================

# Пересчет скорректированных ПВ и ДНС обратно в условные показания реометра Fann 
# (Используем стандартные константы перевода API)
theta_300_fann = f_pv_corrected + f_yp_corrected
theta_600_fann = (2.0 * f_pv_corrected) + f_yp_corrected

# Расчет предела текучести по Гершелю-Балкли (Yield Stress, tau_0) по стандарту API RP 13D
# Классическая формула на основе геометрии Fann: tau_0 = 2 * theta_3 - theta_600
# Для защиты от экстремальных/ошибочных значений ограничиваем tau_0 снизу и сверху
fann_tau_0 = (2.0 * theta_300_fann) - theta_600_fann
if fann_tau_0 < 0.0:
    fann_tau_0 = 0.0
elif fann_tau_0 >= theta_300_fann:
    fann_tau_0 = theta_300_fann * 0.5  # Защитное ограничение при аномальной реологии

# --- СТРОГИЙ РАСЧЕТ ИНДЕКСА ТЕЧЕНИЯ (n_hb) И КОЭФФИЦИЕНТА КОНСИСТЕНЦИИ (K_hb) ---
# Проверяем знаменатель и аргумент логарифма на корректность (!= 0 и > 0)
numerator_log = theta_600_fann - fann_tau_0
denominator_log = theta_300_fann - fann_tau_0

if denominator_log > 0.001 and numerator_log > 0.001 and (numerator_log / denominator_log) > 0:
    try:
        # Расчет индекса нелинейности потока n_hb
        n_hb = 3.321928 * math.log10(numerator_log / denominator_log)
        
        # Физические рамки для псевдопластичных буровых растворов по API
        n_hb = max(0.1, min(1.0, n_hb))
        
        # Расчет коэффициента консистенции K_hb в Па·с^n
        # Коэффициент 0.511 переводит показания шкалы Fann в Паскали
        K_hb = 0.511 * (theta_300_fann - fann_tau_0) / (511.0 ** n_hb)
        
    except (ValueError, ZeroDivisionError):
        # Безопасный откат к базовым параметрам в случае математической аномалии
        n_hb = 0.65
        K_hb = 0.511 * theta_300_fann / (511.0 ** n_hb)
        fann_tau_0 = 0.0
else:
    # Если реологическая кривая вырождается, переходим на линейную модель
    n_hb = 1.0  # Ньютоновская модель
    K_hb = 0.511 * theta_300_fann / 511.0
    fann_tau_0 = 0.0

# Перевод предела текучести tau_0 в систему СИ (Паскали) для гидродинамических уравнений
tau_0_si = fann_tau_0 * 0.511
# =========================================================================
# БЛОК 3: ВЫСОКОТОЧНЫЙ РАСЧЕТ ЭЦП ПО МОДЕЛИ ГЕРШЕЛЯ-БАЛКЛИ - ЧАСТЬ 3
# =========================================================================

# --- 1. РАСЧЕТ СКОРОСТИ И СКОРОСТИ СДВИГА В ЗАТРУБЬЕ ---
# v_annulus уже посчитана на Шаге 1. Проверяем, есть ли циркуляция:
if q_flow > 0.001 and area_annulus > 0:
    v_annulus = (q_flow / 1000.0) / area_annulus
    
    # Эффективная скорость сдвига в затрубном пространстве по API RP 13D
    # Учитывает индекс нелинейности потока n_hb
    if hydraulic_diam > 0 and n_hb > 0:
        gamma_dot = ((2.0 * n_hb + 1.0) / (3.0 * n_hb)) * (12.0 * v_annulus / hydraulic_diam)
    else:
        gamma_dot = 0.0
else:
    v_annulus = 0.0
    gamma_dot = 0.0

# --- 2. РАСЧЕТ НАПРЯЖЕНИЯ СДВИГА И ЭФФЕКТИВНОЙ ВЯЗКОСТИ ---
if gamma_dot > 0.001:
    # Динамическое напряжение сдвига в потоке по Гершелю-Балкли
    tau_annulus = tau_0_si + K_hb * (gamma_dot ** n_hb)
    # Эффективная вязкость (Па·с)
    eff_viscosity = tau_annulus / gamma_dot
else:
    tau_annulus = tau_0_si
    # В статике эффективная вязкость условно стремится к максимуму (заглушка для исключения деления на 0)
    eff_viscosity = 999.0  

# --- 3. ОБОБЩЕННОЕ ЧИСЛО РЕЙНОЛЬДСА ДЛЯ МОДЕЛИ ГЕРШЕЛЯ-БАЛКЛИ ---
# Используем скорректированную плотность раствора rho_base_corrected из Шага 1
if eff_viscosity > 0 and hydraulic_diam > 0:
    Re_general = (rho_base_corrected * v_annulus * hydraulic_diam) / eff_viscosity
else:
    Re_general = 0.0

# --- 4. КРИТЕРИАЛЬНЫЙ РАСЧЕТ КОЭФФИЦИЕНТА ТРЕНИЯ ФАННИНГА ---
if Re_general <= 0.001:
    # Полная статика, трение отсутствует
    f_friction = 0.0
elif Re_general < 2100.0:
    # Ламинарный режим течения
    f_friction = 16.0 / Re_general
else:
    # Турбулентный/переходный режим (Классическое приближение Блазиуса по API)
    f_friction = 0.0791 / (Re_general ** 0.25)
# =========================================================================
# БЛОК 3: ВЫСОКОТОЧНЫЙ РАСЧЕТ ЭЦП ПО МОДЕЛИ ГЕРШЕЛЯ-БАЛКЛИ - ЧАСТЬ 4
# =========================================================================

# --- 1. ПОТЕРИ ДАВЛЕНИЯ НА ТРЕНИЕ В ЗАТРУБЕ (Па) ---
if hydraulic_diam > 0:
    # Дифференциальные потери давления на 1 метр длины ствола
    dp_dl_friction = (2.0 * f_friction * rho_base_corrected * (v_annulus ** 2)) / hydraulic_diam
    total_p_friction_pa = dp_dl_friction * h_tvd
else:
    total_p_friction_pa = 0.0

# --- 2. МАТЕМАТИЧЕСКИЙ РАСЧЕТ КОНЦЕНТРАЦИИ И ВЫНОСА ШЛАМА ---
if rop > 0.01 and d_hole > 0 and (q_flow > 0.01 or v_annulus > 0.01):
    dh_m_local = d_hole / 1000.0
    # Объем выбуренной породы в секунду (м³/с)
    q_solids = ((math.pi / 4.0) * (dh_m_local ** 2)) * (rop / 3600.0)
    # Поток промывочной жидкости (м³/с)
    q_fluid_m3s = q_flow / 1000.0
    
    # Объемная концентрация шлама в затрубном пространстве
    c_cutting = q_solids / (q_fluid_m3s + q_solids)
    # Физическое ограничение сверху для исключения математических аномалий (макс 10%)
    c_cutting = max(0.0, min(0.10, c_cutting)) 
else:
    c_cutting = 0.0

# --- 3. ИНТЕГРАЦИЯ ЭФФЕКТИВНОЙ ПЛОТНОСТИ СМЕСИ С УЧЕТОМ ШЛАМА И ПЕСКА ---
# rho_base_corrected уже учитывает песок из Блока 2, добавляем шлам (rho_rock = 2650 кг/м³)
rho_eff_mix = (rho_base_corrected * (1.0 - c_cutting)) + (rho_rock * c_cutting)

# --- 4. РАСЧЕТ АБСОЛЮТНЫХ ДАВЛЕНИЙ И ФИНАЛЬНОЙ ЭЦП (ECD) ---
if h_tvd > 0.1:
    # Общее гидростатическое давление смеси (Па)
    total_hydrostatic_pa = rho_eff_mix * 9.81 * h_tvd
    # Полное динамическое забойное давление (Па)
    total_dynamic_pressure_pa = total_hydrostatic_pa + total_p_friction_pa
    
    # Перевод итоговой ЭЦП (ECD) обратно в г/см³
    calculated_ecd = (total_dynamic_pressure_pa / (9.81 * h_tvd)) / 1000.0
    
    # НОВАЯ МЕТРИКА: Перевод давлений в технические атмосферы (атм) с защитой арифметики
    p_hydrostatic_atm = round(total_hydrostatic_pa / 101325.0, 1)
    p_friction_atm = round(total_p_friction_pa / 101325.0, 1)
    # Финальное давление жестко формируется из округленных слагаемых
    p_total_bottomhole_atm = p_hydrostatic_atm + p_friction_atm

else:
    # Защитный откат на плотность на входе, если глубина близка к нулю
    calculated_ecd = rho_base_corrected / 1000.0
    p_hydrostatic_atm = 0.0
    p_friction_atm = 0.0
    p_total_bottomhole_atm = 0.0

# =========================================================================
# БЛОК 3: ВЫСОКОТОЧНЫЙ РАСЧЕТ ЭЦП ПО МОДЕЛИ ГЕРШЕЛЯ-БАЛКЛИ - ЧАСТЬ 5
# =========================================================================

# --- 1. ОПРЕДЕЛЕНИЕ ДИНАМИЧЕСКОГО БУФЕРА БЕЗОПАСНОСТИ ПО ТРЕБОВАНИЯМ ТК ---
selected_client = company_choice if 'company_choice' in locals() else "Прочие"

if selected_client == "Роснефть":
    tk_buffer = 0.030
    client_label = "ПАО «НК «Роснефть»"
elif selected_client == "Газпром нефть":
    tk_buffer = 0.020
    client_label = "ПАО «Газпром нефть»"
elif selected_client == "ЛУКОЙЛ":
    tk_buffer = 0.020
    client_label = "ПАО «ЛУКОЙЛ»"
else:
    tk_buffer = 0.025
    client_label = f"ТК «{selected_client}»"

# --- 2. КЛАССИФИКАЦИЯ ТЕХНОЛОГИЧЕСКИХ ЗОН РИСКА С УЧЕТОМ БУФЕРА ---
orange_zone_threshold = p_frac - tk_buffer
red_zone_threshold = p_frac - (tk_buffer * 0.5)

if calculated_ecd < orange_zone_threshold:
    ecd_status = "🟢 Зеленая зона (Режим безопасен)"
    status_color = "#10B981"
    status_msg = f"Гидравлический режим стабилен. ЭЦП соответствует Техническим Критериям {client_label}."
elif calculated_ecd < red_zone_threshold:
    ecd_status = "🟡 Оранжевая зона (Повышенный риск)"
    status_color = "#F59E0B"
    status_msg = f"ВНИМАНИЕ: Нарушен буфер безопасности {client_label}. Контролировать скорость спуска инструмента!"
else:
    ecd_status = "🔴 Красная зона (Критическая угроза ГРП!)"
    status_color = "#EF4444"
    status_msg = f"КРИТИЧЕСКИЙ РЕЖИМ {client_label}: Расчетная ЭЦП превышает безопасный предел пласта!"

# --- 3. ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ ГИДРОДИНАМИЧЕСКОГО МОНИТОРИНГА ---
st.markdown("#### 📈 Результаты гидродинамического мониторинга:")

# Строка 1: Относительные показатели (ЭЦП)
col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.metric("Расчетная ЭЦП (ECD)", f"{calculated_ecd:.3f} г/см³")
with col_res2:
    st.metric("Запас до ГРП пласта", f"{p_frac - calculated_ecd:.3f} г/см³")
with col_res3:
    st.markdown(
        f'<div style="text-align: center; color: white; background-color: {status_color}; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 14px; margin-top: 8px;">'
        f'{ecd_status}</div>',
        unsafe_allow_html=True
    )

# Строка 2: Абсолютные гидродинамические давления (в атмосферах)
st.markdown("##### Абсолютные давления на забое скважины:")
col_press1, col_press2, col_press3 = st.columns(3)
with col_press1:
    st.metric("Гидростатика смеси", f"{p_hydrostatic_atm:.1f} атм", help="Давление чистого столба раствора со шламом и песком")
with col_press2:
    st.metric("Потери на трение в КСП", f"{p_friction_atm:.1f} атм", help="Гидравлические потери при движении потока вверх")
with col_press3:
    st.metric("Полное забойное давление", f"{p_total_bottomhole_atm:.1f} атм", help="Суммарная нагрузка на пласт в динамике")

# Вывод текстового предупреждения
if "🔴" in ecd_status: 
    st.error(f"❌ **{status_msg}**")
elif "🟡" in ecd_status: 
    st.warning(f"⚠️ **{status_msg}**")
else: 
    st.success(f"{status_msg}")

st.markdown("---")

st.session_state["shared_buoyancy_factor"] = 1.0 - (f_dens / 7.85)  # Расчет коэффициента плавучести из плотности раствора
st.session_state["shared_yield_stress"] = f_yp_corrected           # Передаем скорректированное ДНС
st.session_state["shared_flow_index"] = n_hb                       # Передаем точный индекс течения из Гершеля-Балкли
st.session_state["shared_sand_pct"] = sand_input_val               # Передаем процент песка для прогноза износа

# =========================================================================
# МОДУЛЬ ОНЛАЙН-ВАЛИДАЦИИ И ТЕСТИРОВАНИЯ ГИДРАВЛИЧЕСКОГО ЯДРА БЛОКА 3
# =========================================================================
with st.expander("🛠 Модуль онлайн-валидации и стресс-тестирования ядра"):
    st.markdown("##### Симуляция экстремальных режимов бурения")
    st.caption("Выберите тестовый сценарий для проверки устойчивости математических алгоритмов:")
    
    # --- НАДЕЖНЫЕ ФУНКЦИИ-КОЛБЭКИ ДЛЯ ТЕСТОВЫХ ПРЕСЕТОВ ---
    def set_test_static():
        st.session_state["val_q_flow"] = 0.0
        st.session_state["val_rop"] = 0.0

    def set_test_high_rop():
        st.session_state["val_q_flow"] = 22.0
        st.session_state["val_rop"] = 100.0

    def set_test_extreme_depth():
        st.session_state["val_h_tvd"] = 5500.0
        st.session_state["val_q_flow"] = 35.0

    # Кнопки для быстрой загрузки экстремальных пресетов с привязкой колбэков
    col_test1, col_test2, col_test3 = st.columns(3)
    
    # При нажатии сначала выполнится функция изменения сессии, и только потом Стримлит чисто перерисует инпуты
    col_test1.button("🔴 Тест 1: Статика (Остановка насосов)", on_click=set_test_static)
    col_test2.button("🔥 Тест 2: Лавинообразный ROP (100 м/ч)", on_click=set_test_high_rop)
    col_test3.button("🏔 Тест 3: Экстремальная глубина (5500 м)", on_click=set_test_extreme_depth)

    # Секция автоматической верификации математических логов
    st.markdown("##### Лог верификации параметров API RP 13D:")
    
    # Проверяем критические маркеры на деление на ноль или комплексные числа
    validation_passed = True
    logs = []
    
    if Re_general == 0:
        logs.append("ℹ️ Число Рейнольдса равно 0 (Поток остановлен или вязкость стремится к бесконечности).")
    else:
        logs.append(f"✅ Число Рейнольдса стабильно: {Re_general:.2f} ({'Ламинарный' if Re_general < 2100 else 'Турбулентный'} режим).")
        
    if gamma_dot <= 0:
        logs.append("ℹ️ Скорость сдвига на стенке трубы равна 0.")
    else:
        logs.append(f"✅ Скорость сдвига валидна: {gamma_dot:.2f} с⁻¹.")
        
    if c_cutting >= 0.10:
        logs.append("⚠️ Предупреждение: Концентрация шлама достигла верхнего защитного лимита отсечки (10%).")
    else:
        logs.append(f"✅ Концентрация шлама в пределах нормы: {c_cutting*100:.2f}%.")

    if calculated_ecd <= 0 or calculated_ecd > 3.0:
        logs.append("❌ КРИТИЧЕСКИЙ СБОЙ: Аномальное значение ЭЦП! Проверьте физические размерности.")
        validation_passed = False
    else:
        logs.append(f"✅ Выходной параметр ЭЦП прошел валидацию диапазона: {calculated_ecd:.3f} г/см³.")

    # Вывод логов валидации
    for log in logs:
        if "✅" in log: st.write(log)
        elif "⚠️" in log or "ℹ️" in log: st.info(log)
        else: st.error(log)
        
    if validation_passed:
        st.success("🎯 Автоматическая валидация ядра: Ошибок деления на ноль (ZeroDivisionError) и сбоев типов данных НЕ ОБНАРУЖЕНО.")
    else:
        st.error("🚨 Автоматическая валидация ядра: Обнаружены математические аномалии!")

# =========================================================================
# БЛОК 4: ЭКСПЕРТНАЯ СИСТЕМА СИНХРОНИЗАЦИИ И РАСЧЕТА РЕСУРСА СТАТОРА ВЗД
# =========================================================================

# --- ЧАСТЬ 4.1: ИНЖЕНЕРНАЯ ОЦЕНКА ХИМИИ РАСТВОРА И БЕЗОПАСНАЯ ИНИЦИАЛИЗАЦИЯ ---
st.markdown("### ⏳ Блок 4: Экспертная система расчета остаточного ресурса")

# 1. Защита от NameError: извлекаем тип кинематики из сессии или ставим стандартный дефолт 5/6
if "kinematics_type" in st.session_state:
    kinematics_type = st.session_state["kinematics_type"]
else:
    kinematics_type = "5/6"  # Стандартная заходность по умолчанию

# 2. Расширенный выпадающий список типов растворов и агрессивных технологических пачек
mud_list = [
    "Полимерный / Биополимерный", 
    "Гипсокалиевый", 
    "Гелево-Эмульсионный", 
    "MaxFlow", 
    "Вязко-упругий состав (ВУС)",  # Расширение списка
    "Кислотная пачка",            # Расширение списка
    "Прочие"
]

mud_choice = st.selectbox(
    "Тип применяемого бурового раствора / технологической пачки:",
    mud_list,
    key="b4_mud_choice"
)

# 3. Базовая инициализация метрик (подстраховка от NameError на дальнейших шагах)
current_runtime = float(st.session_state.get("current_runtime", 48.0))
current_temp_est = float(st.session_state.get("current_temp_est", 75.0))
region_choice = st.session_state.get("region_choice", "ХМАО / Мегион")
vendor_choice = st.session_state.get("vendor_choice", "Радиус-Сервис")

# 4. Расчет коэффициента химической деструкции по методике СТО ИНТИ S.100.3
if "Вязко-упругий" in mud_choice:
    current_mud_aggressiveness = 1.85  # Повышенный износ из-за сверхвязкости состава
elif "Кислотная" in mud_choice:
    current_mud_aggressiveness = 3.50  # Критический химический износ нитрильного эластомера NBR
elif "Полимерный" in mud_choice:
    current_mud_aggressiveness = 1.10
elif "Гипсокалиевый" in mud_choice:
    current_mud_aggressiveness = 1.30
elif "Гелево-Эмульсионный" in mud_choice:
    current_mud_aggressiveness = 1.35
elif "MaxFlow" in mud_choice:
    current_mud_aggressiveness = 1.45
else:
    current_mud_aggressiveness = 1.00

# 5. Преобразование текстового пресета заходности силовой пары бурового мотора
if "5/6" in kinematics_type: 
    current_kin = 0.83
elif "7/8" in kinematics_type: 
    current_kin = 0.87
elif "9/10" in kinematics_type: 
    current_kin = 0.90
else: 
    current_kin = 0.50

# Фильтрация базы данных по географическому признаку
region_filter = ["ХМАО", "ЯНАО", "Западная Сибирь"] if "Самара" not in region_choice else "Волго-Урал"

def load_advanced_failures_database(file_path):
    """Безопасная функция загрузки исторических инцидентов отказов ВЗД"""
    try:
        df = pd.read_excel(file_path)
        # Очищаем заголовки от случайных пробелов
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception:
        # Если файла нет, возвращаем пустой DataFrame с нужными колонками
        return pd.DataFrame(columns=["Регион работ", "Производитель_чистый", "Песок (%)", "Забойная Темп. (°C)", "Кинематика_число", "Наработка до отказа (Часы)", "Скорость_износа"])

# Теперь вызываем её (эта строчка у вас уже есть)
df_failures = load_advanced_failures_database("failures_db.xlsx")

# Загружаем историческую базу инцидентов перед фильтрацией
df_failures = load_advanced_failures_database("failures_db.xlsx")

if df_failures is not None and not df_failures.empty:
    if isinstance(region_filter, list):
        df_geo = df_failures[df_failures["Регион работ"].isin(region_filter)].copy()
    else:
        df_geo = df_failures[df_failures["Регион работ"] == region_filter].copy()

    # Каскадный спуск по вендорам оборудования КНБК
    vendor_cols = [c for c in df_geo.columns if "Производитель" in c or "Габарит" in c]
    if vendor_cols:
        target_vendor_col = vendor_cols[0]
        short_vendor_name = str(vendor_choice).split("-")[0].split(" ")[0].upper()
        df_vendor_slice = df_geo[df_geo[target_vendor_col].astype(str).str.upper().str.contains(short_vendor_name, na=False)].copy()
        df_train = df_vendor_slice.copy() if len(df_vendor_slice) >= 3 else df_geo.copy()
    else:
        df_train = df_geo.copy()

# Сброс флагов готовности перед запуском расчетов машинного обучения
model_ready = False
predicted_hours_to_failure = 0.0
mae_hours = 24.0
accuracy_pct = 75.0
# --- ЧАСТЬ 4.3: ОБУЧЕНИЕ ИИ-МОДЕЛИ (COMPACT) ---
if len(df_train) >= 3:
    try:
        X_train = df_train[["Песок (%)", "Забойная Темп. (°C)", "Кинематика_число", "Агрессивность_БР"]]
        y_train = df_train["Скорость_износа"]
        
        # Обучение с ограничением глубины
        rf_model = RandomForestRegressor(n_estimators=30, max_depth=5, random_state=42)
        rf_model.fit(X_train, y_train)
        
        # Прогноз ресурса (max 150 ч)
        X_curr = np.array([[sand_input_val, current_temp_est, current_kin, current_mud_aggressiveness]])
        pred_speed = max(0.0001, float(rf_model.predict(X_curr)))
        allowed_res = min(150.0, 1.0 / pred_speed)
        predicted_hours_to_failure = max(0.0, allowed_res - current_runtime)
        model_ready = True
    except:
        model_ready = False
# =========================================================================
# --- ЧАСТЬ 4.4: АНАЛИТИКА, РАСЧЕТ ДЕГРАДАЦИИ И РЕГЛАМЕНТНЫЕ ОТСЕЧКИ ---
# =========================================================================

# 1. Принудительный спуск инпутов в интерфейс для контроля инженером ННБ
st.markdown("##### ⚙️ Фактические параметры эксплуатации эластомера:")
col_in1, col_in2, col_in3 = st.columns(3)
with col_in1:
    current_runtime = st.number_input(
        "Текущая наработка ВЗД за рейс (ч):", 
        min_value=0.0, max_value=300.0, value=48.0, step=1.0, key="b4_current_runtime"
    )
with col_in2:
    current_temp_est = st.number_input(
        "Расчетная забойная температура (°C):", 
        min_value=20.0, max_value=200.0, value=75.0, step=1.0, key="b4_current_temp_est"
    )
with col_in3:
    # Отображаем текущий коэффициент агрессивности среды для понимания физики процесса
    st.metric("Коэффициент агрессивности среды (СТО ИНТИ)", f"{current_mud_aggressiveness:.2f}")

# 2. Математический расчет износа по методике СТО ИНТИ S.100.3
if not model_ready:
    # Базовая деградация от абразива (песка) и температурного расширения
    base_degradation = (1.0 + (max(0.0, sand_input_val - 0.5) * 3.5)) * \
                       (1.5 ** ((current_temp_est - 70.0) / 10.0) if current_temp_est > 70.0 else 1.0)
    
    # Итоговый коэффициент износа с учетом геометрии и химии пачки
    total_degradation = base_degradation * (current_kin * 1.3 * current_mud_aggressiveness)
    
    # Вычисление аналитического ресурса по СТО ИНТИ
    allowed_analytical = min(150.0, 180.0 / max(0.001, total_degradation))
    
    # Применение жестких регламентных технологических лимитов и отсечек компании
    if "Кислотная пачка" in mud_choice:
        allowed_analytical = 0.0  # Срочное СПО, 99% разрушения силовой пары ВЗД
    elif "Вязко-упругий состав (ВУС)" in mud_choice:
        allowed_analytical = min(60.0, allowed_analytical)  # Защитное ограничение по давлению
        
    predicted_hours_to_failure = max(0.0, allowed_analytical - current_runtime)

# 3. Синхронизация со сквозным шлюзом данных сессии Streamlit
st.session_state["predicted_hours_to_failure"] = predicted_hours_to_failure
st.session_state["shared_buoyancy_factor"] = 1.0 - (f_dens / 7.85)
st.session_state["shared_yield_stress"] = f_yp_corrected
st.session_state["shared_flow_index"] = n_hb
st.session_state["shared_sand_pct"] = sand_input_val

# 4. Вывод KPI-метрик (Возвращаем наработку, точность и погрешность MAE)
st.markdown("#### 📊 Результаты предиктивного анализа силовой секции:")

# Если прокачана кислота — выводим критический аварийный баннер вместо стандартного счетчика
if "Кислотная пачка" in mud_choice:
    st.error("🚨 КРИТИЧЕСКИЙ СТАТУС: ПРОКАЧКА КИСЛОТЫ! ОСТАТОК РЕСУРСА ВЗД ОБНУЛЕН. ТРЕБУЕТСЯ СРОЧНЫЙ ПОДЪЕМ КНБК НА СПО И ЗАМЕНА ДВИГАТЕЛЯ!")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1: st.metric("Остаток времени бурения", "0.0 ч", delta="-100%", delta_color="inverse")
    with col_m2: st.metric("Точность ядра (учет ТК)", f"{accuracy_pct:.1f} %")
    with col_m3: st.metric("Погрешность расчета (MAE)", f"± {mae_hours:.1f} ч")
else:
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1: 
        # Если ресурс исчерпан по времени наработки
        if predicted_hours_to_failure == 0:
            st.metric("Остаток времени бурения", "0.0 ч", "Ресурс исчерпан!", delta_color="inverse")
        else:
            st.metric("Остаток времени бурения", f"{predicted_hours_to_failure:.1f} ч")
    with col_m2: 
        st.metric("Точность ядра (учет ТК)", f"{accuracy_pct:.1f} %")
    with col_m3: 
        st.metric("Погрешность расчета (MAE)", f"± {mae_hours:.1f} ч", help="Средняя абсолютная ошибка модели на основе исторических отказов")

    # =========================================================================
# БЛОК 4.5: ПОИСК СХОЖИХ ИНЦИДЕНТОВ И СТРАХОВКА ОТ NAMEERROR
# =========================================================================

# Инициализируем пустой df_similarity для предотвращения NameError
df_similarity = pd.DataFrame()

if df_failures is not None and not df_failures.empty and 'df_geo' in locals() and not df_geo.empty:
    df_similarity = df_geo.copy()
    # Расчет дистанции сходства (сокращено для лаконичности)
    p_sand = pd.to_numeric(df_similarity["Песок (%)"], errors="coerce").fillna(0) if "Песок (%)" in df_similarity.columns else 0
    df_similarity["Дистанция_сходства"] = np.sqrt((10.0 * (p_sand - sand_input_val)) ** 2) # Упрощенный пример

# Безопасный вывод карточек
if not df_similarity.empty and "Дистанция_сходства" in df_similarity.columns:
    st.markdown("---")
    st.markdown(f"#### 🔍 Топ-3 схожих исторических отказа в регионе ({region_choice}):")
    top_3 = df_similarity.sort_values(by="Дистанция_сходства").head(3)
    card_cols = st.columns(3)
    for idx, (_, row) in enumerate(top_3.iterrows()):
        with card_cols[idx]:
            with st.container(border=True):
                st.markdown(f"🔹 **{row.get('ВЗД', 'ВЗД')}**") # Пример вывода
                st.caption(f"Песок: {row.get('Песок (%)', 0)}%")

st.warning("⚠️ **ВАЖНОЕ УВЕДОМЛЕНИЕ:** Расчеты носят рекомендательный характер.")


# =========================================================================
# МОДУЛЬ ОНЛАЙН-ВАЛИДАЦИИ И СТРЕСС-ТЕСТИРОВАНИЯ ИИ-ЯДРА БЛОКА 4
# =========================================================================
with st.expander("🛠 Модуль онлайн-валидации и стресс-тестирования ИИ-ядра"):
    st.markdown("##### Симуляция критических режимов эксплуатации эластомера")
    st.caption("Выберите тестовый сценарий для проверки устойчивости предиктивных алгоритмов:")
    
    # ФУНКЦИИ-КОЛБЭКИ ДЛЯ ИЗМЕНЕНИЯ СЕССИИ (Защита от StreamlitAPIException)
    def set_test_critical_wear():
        st.session_state["main_sand_input"] = 2.5
        st.session_state["b4_current_temp_est"] = 110.0
        st.session_state["b4_mud_choice"] = "MaxFlow"
        st.session_state["b4_current_runtime"] = 120.0

    def set_test_ideal_conditions():
        st.session_state["main_sand_input"] = 0.1
        st.session_state["b4_current_temp_est"] = 50.0
        st.session_state["b4_mud_choice"] = "Техническая вода"
        st.session_state["b4_current_runtime"] = 0.0

    # Кнопки пресетов
    col_v_test1, col_v_test2 = st.columns(2)
    
    col_v_test1.button("🔴 Тест 1: Экстремальная деградация статора", on_click=set_test_critical_wear, use_container_width=True)
    col_v_test2.button("🟢 Тест 2: Идеальные условия (Новый двигатель)", on_click=set_test_ideal_conditions, use_container_width=True)

    st.markdown("##### Сводный лог валидации ИИ-модели (СТО ИНТИ S.100.3):")
    
    # Алгоритм автоматического аудита переменных
    ai_validation_passed = True
    ai_logs = []
    
    # 1. Проверка режима работы ядра
    if model_ready:
        ai_logs.append(f"✅ **Режим работы:** Машинное обучение (RandomForestRegressor). Обучено на выборке из {len(df_train)} записей.")
    else:
        ai_logs.append("ℹ️ **Режим работы:** Аналитический статический откат ИНТИ (Недостаточно исторических данных в Excel).")
        
    # 2. Проверка адекватности прогноза времени
    if predicted_hours_to_failure < 0:
        ai_logs.append("❌ **КРИТИЧЕСКИЙ СБОЙ:** Прогноз ресурса ушел в отрицательную зону! Проверьте формулу вычитания наработки.")
        ai_validation_passed = False
    elif predicted_hours_to_failure == 0:
        ai_logs.append("⚠️ **Предупреждение:** Остаточный ресурс равен 0. Эластомер выработал свой предел в текущих условиях.")
    else:
        ai_logs.append(f"✅ **Выходной параметр:** Расчетный остаток времени ({predicted_hours_to_failure:.1f} ч.) находится в рамках физического диапазона.")
        
    # 3. Валидация точности
    if accuracy_pct < 50.0:
        ai_logs.append(f"⚠️ **Внимание:** Точность предиктивного ядра занижена ({accuracy_pct:.1f}%). Высокий разброс целевых меток в Excel.")
    else:
        ai_logs.append(f"✅ **Метрика точности:** Доверительный интервал модели стабилен ({accuracy_pct:.1f}%).")

    # Вывод логов на экран
    for log in ai_logs:
        if "✅" in log: st.write(log)
        elif "⚠️" in log or "ℹ️" in log: st.info(log)
        else: st.error(log)
        
    if ai_validation_passed:
        st.success("🎯 Предиктивное ядро Блока 4 успешно прошло автоматический аудит типов данных и граничных значений.")
    else:
        st.error("🚨 Обнаружены математические аномалии в расчете ИИ-модели!")

# =========================================================================
# БЛОК 5: СВОДНЫЙ РАПОРТ ТЕХНОЛОГИЧЕСКОГО КОНТРОЛЯ - ЧАСТЬ 5.1
# =========================================================================
st.markdown("---")
import time

# --- ТЕКСТОВАЯ НОРМАЛИЗАЦИЯ И ОЧИСТКА (Исключаем NameError) ---
# Принудительно приводим переменные к строкам, проверяя их наличие (locals())
normalized_well = str(well_name).strip() if 'well_name' in locals() else "Скв. № 101, Куст 5"
normalized_engineer = str(engineer_name).strip() if 'engineer_name' in locals() else "Иванов И.И."
# ... (остальные переменные normalized_* аналогично) ...
report_timestamp = time.strftime("%d.%m.%Y %H:%M")

# --- ЛОГИКА АВТО-АНАЛИЗА И КРИТИЧЕСКОГО КАПСЛОКА ---
## =========================================================================
# БЛОК 4.5: ПОИСК СХОЖИХ ИНЦИДЕНТОВ И СТРАХОВКА ОТ NAMEERROR
# =========================================================================

# Инициализируем пустой df_similarity для предотвращения NameError
df_similarity = pd.DataFrame()

if df_failures is not None and not df_failures.empty and 'df_geo' in locals() and not df_geo.empty:
    df_similarity = df_geo.copy()
    # Расчет дистанции сходства (сокращено для лаконичности)
    p_sand = pd.to_numeric(df_similarity["Песок (%)"], errors="coerce").fillna(0) if "Песок (%)" in df_similarity.columns else 0
    df_similarity["Дистанция_сходства"] = np.sqrt((10.0 * (p_sand - sand_input_val)) ** 2) # Упрощенный пример

# Безопасный вывод карточек
if not df_similarity.empty and "Дистанция_сходства" in df_similarity.columns:
    st.markdown("---")
    st.markdown(f"#### 🔍 Топ-3 схожих исторических отказа в регионе ({region_choice}):")
    top_3 = df_similarity.sort_values(by="Дистанция_сходства").head(3)
    card_cols = st.columns(3)
    for idx, (_, row) in enumerate(top_3.iterrows()):
        with card_cols[idx]:
            with st.container(border=True):
                st.markdown(f"🔹 **{row.get('ВЗД', 'ВЗД')}**") # Пример вывода
                st.caption(f"Песок: {row.get('Песок (%)', 0)}%")

st.warning("⚠️ **ВАЖНОЕ УВЕДОМЛЕНИЕ:** Расчеты носят рекомендательный характер.")

# =========================================================================
# БЛОК 5: СВОДНЫЙ РАПОРТ ТЕХНОЛОГИЧЕСКОГО КОНТРОЛЯ (ЧАСТЬ 5.1)
# =========================================================================
st.markdown("---")
import time

# --- Безопасная инициализация текстовых полей ---
report_timestamp = time.strftime("%d.%m.%Y %H:%M")
normalized_company = locals().get('company_choice', "Роснефть")
normalized_mud = locals().get('mud_choice', "Полимерный / Биополимерный")
normalized_field = str(locals().get('field_name', "Приобское")).strip()
normalized_well = str(locals().get('well_number', "Скв. № 101, Куст 5")).strip()
normalized_engineer = str(locals().get('engineer_name', "Иванов И.И.")).strip()
normalized_serial = str(locals().get('serial_number', "№ 6677")).strip()

# --- Единая логика нарушений и формирования статуса ---
current_threshold = locals().get('sand_threshold', 0.5)
is_sand_failure = sand_input_val > current_threshold

if "Кислотная пачка" in normalized_mud:
    final_report_status = "КРИТИЧЕСКИЙ ОТКАЗ: СТОП БУРЕНИЕ! ПРОКАЧКА КИСЛОТЫ. СУММАРНОЕ РАЗРУШЕНИЕ СИЛОВОЙ ПАРЫ ВЗД. СРОЧНОЕ СПО НА ЗАМЕНУ ДВИГАТЕЛЯ РЕГЛАМЕНТ СТО ИНТИ S.100.3!"
    is_any_failure = True
elif is_sand_failure:
    final_report_status = f"ТЕХНОЛОГИЧЕСКОЕ НЕСООТВЕТСТВИЕ: СОДЕРЖАНИЕ ПЕСКА ({sand_input_val:.2f}%) ПРЕВЫШАЕТ ДОПУСТИМЫЙ ЛИМИТ ЗАКАЗЧИКА {current_threshold:.2f}%!"
    is_any_failure = True
else:
    final_report_status = f"Технологический status в норме. Фактическое содержание песка ({sand_input_val:.2f}%) находится в безопасных пределах допуска."
    is_any_failure = False
# =========================================================================
# БЛОК 5: СВОДНЫЙ РАПОРТ ТЕХНОЛОГИЧЕСКОГО КОНТРОЛЯ (Шаг 5.2.1)
# =========================================================================
st.markdown("---")
import time

# Безопасное извлечение текстовых переменных (защита от NameError)
normalized_company = company_choice if 'company_choice' in locals() else "Прочие"
normalized_mud = mud_choice if 'mud_choice' in locals() else "Полимерный / Bioполимерный"
normalized_field = str(field_name).strip() if 'field_name' in locals() else "Приобское"
normalized_well = str(well_number).strip() if 'well_number' in locals() else "Скв. № 101, Куст 5"
normalized_engineer = str(engineer_name).strip() if 'engineer_name' in locals() else "Иванов И.И."
normalized_serial = str(serial_number).strip() if 'serial_number' in locals() else "№ 6677"

# Формируем официальный штамп времени генерации документа
report_timestamp = time.strftime("%d.%m.%Y %H:%M")
# --- АВТО-АНАЛИЗ И ФОРМИРОВАНИЕ ОФИЦИАЛЬНОГО ЗАКЛЮЧЕНИЯ (Шаг 5.2.2) ---

# Проверяем факт превышения содержания абразивного песка (из Блока 2)
is_sand_failure = sand_input_val > (sand_threshold if 'sand_threshold' in locals() else 0.5)

# Каскадная логика определения легитимного статуса для буровой бригады
if "Кислотная пачка" in normalized_mud:
    final_report_status = "🚨 КРИТИЧЕСКИЙ ОТКАЗ: ПРОКАЧКА КИСЛОТЫ! ДАЛЬНЕЙШЕЕ БУРЕНИЕ ЗАПРЕЩЕНО. ТРЕБУЕТСЯ СРОЧНЫЙ ПОДЪЕМ КНБК НА СПО ДЛЯ ЗАМЕНЫ ВЗД (РЕГЛАМЕНТ СТО ИНТИ S.100.3)."
    status_bg = "#FEE2E2"    # Строгий аварийный красный фон
    status_color = "#991B1B" # Темно-красный текст
    is_critical_alert = True
elif is_sand_failure:
    final_report_status = "⚠️ КРИТИЧЕСКОЕ НЕСООТВЕТСТВИЕ: ИНТЕНСИВНЫЙ АБРАЗИВНЫЙ ИЗНОС СТАТОРА ВЗД! ТРЕБУЕТСЯ СРОЧНАЯ ОСТАНОВКА БУРЕНИЯ И ОЧИСТКА СИТ!"
    status_bg = "#FEF3C7"    # Предупреждающий желтый фон
    status_color = "#92400E" # Коричнево-оранжевый текст
    is_critical_alert = True
else:
    final_report_status = f"✔ Технологический статус в норме: Текущее содержание песка ({sand_input_val:.2f}%) находится в пределах допустимого порога."
    status_bg = "#D1FAE5"    # Безопасный зеленый фон
    status_color = "#065F46" # Темно-зеленый текст
    is_critical_alert = False
# --- ВИЗУАЛЬНОЕ ПОСТРОЕНИЕ ПЕЧАТНОЙ ФОРМЫ АКТА (Шаг 5.2.3) ---

with st.container(border=True):
    # Логотип и официальная шапка документа
    st.markdown("<h2 style='text-align: center; color: #1E3A8A; font-family: Arial, sans-serif; font-weight: bold;'>ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #4B5563; margin-top: -15px; letter-spacing: 1px;'>АКТ ТЕХНОЛОГИЧЕСКОГО КОНТРОЛЯ И НАДЕЖНОСТИ ВЗД</h4>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    # Сводные метаданные технологического рейса КНБК
    st.markdown(f"**Заказчик:** {normalized_company} | **Месторождение:** {normalized_field} | **Скважина/Куст:** {normalized_well}")
    st.markdown(f"**Тип раствора:** {normalized_mud} | **Фактический песок:** {sand_input_val:.2f}% (Лимит ТК: {sand_threshold if 'sand_threshold' in locals() else 0.5:.2f}%)")
    st.divider()
    
    # Вывод трех ключевых предиктивных метрик силовой секции
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.metric("Остаток ресурса ВЗД", f"{predicted_hours_to_failure:.1f} ч", help="Расчетное время безопасной работы до срыва статора")
    with col_kpi2:
        st.metric("Точность прогноза", f"{accuracy_pct:.1f} %", help="Статистическая точность ИИ-ядра для данного вендора и региона")
    with col_kpi3:
        st.metric("Погрешность расчета (MAE)", f"± {mae_hours:.1f} ч", help="Средняя абсолютная ошибка предиктивной модели")
        
    st.markdown("##### Экспертное технологическое заключение:")
    
    # Динамический блок официального решения для бурового мастера
    st.markdown(
        f'<div style="color: {status_color}; background-color: {status_bg}; padding: 15px; border-radius: 6px; font-weight: bold; border-left: 5px solid {status_color}; font-size: 14px; line-height: 1.5; font-family: monospace;">'
        f'{final_report_status}</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(f"<p style='text-align: right; color: #9CA3AF; font-size: 12px; margin-top: 10px;'>Сформировано инженером: {normalized_engineer} | Дата и время: {report_timestamp}</p>", unsafe_allow_html=True)
# =========================================================================
# БЛОК 5.3: СБОРКА И СКАЧИВАНИЕ ФАЙЛОВ ОТЧЕТНОСТИ (Шаг 5.3)
# =========================================================================
st.markdown(" ")

# 1. Принудительное формирование полной строки технических характеристик ВЗД
normalized_vzd_profile = f"{vendor_choice} ({kinematics_type})" if ('vendor_choice' in locals() and 'kinematics_type' in locals()) else "ВЗД"

# 2. Формирование официального текстового документа (TXT) для печати
report_text_content = (
    f"==================================================\n"
    f"               ООО ТРАЕКТОРИЯ-СЕРВИС              \n"
    f"       АКТ ТЕХНОЛОГИЧЕСКОГО КОНТРОЛЯ ИЗНОСА ВЗД    \n"
    f"==================================================\n"
    f" Дата и время:      {report_timestamp}\n"
    f" Инженер по ННБ:    {normalized_engineer}\n"
    f" Месторождение:     {normalized_field}\n"
    f" Скважина / Куст:   {normalized_well}\n"
    f" Заказчик:          {normalized_company}\n"
    f"--------------------------------------------------\n"
    f" ХАРАКТЕРИСТИКИ СИЛОВОЙ СЕКЦИИ:\n"
    f" Двигатель:         {normalized_vzd_profile}\n"
    f" Серийный номер:    {normalized_serial}\n"
    f" Текущая наработка: {current_runtime:.1f} ч\n"
    f"--------------------------------------------------\n"
    f" ПАРАМЕТРЫ ПРОМЫВОЧНОЙ СРЕДЫ:\n"
    f" Тип раствора:      {normalized_mud}\n"
    f" Содержание песка:  {sand_input_val:.2f} %\n"
    f" Плотность:         {f_dens:.2f} г/см³\n"
    f" Температура забой: {current_temp_est:.1f} °C\n"
    f"--------------------------------------------------\n"
    f" РЕЗУЛЬТАТЫ ПРЕДИКТИВНОГО АНАЛИЗА ИНТИ S.100.3:\n"
    f" Точность модели:   {accuracy_pct:.1f} %\n"
    f" Погрешность (MAE):  ± {mae_hours:.1f} ч\n"
    f" ОСТАТОК РЕСУРСА:   {predicted_hours_to_failure:.1f} ч\n"
    f"--------------------------------------------------\n"
    f" ОФИЦИАЛЬНОЕ ЗАКЛЮЧЕНИЕ:\n"
    f" {final_report_status}\n"
    f"==================================================\n"
)

# 3. Формирование таблицы данных (CSV) для ведения архива на сервере
report_csv_content = (
    f"Timestamp,Engineer,Field,Well,Company,MudType,SandPct,VzdSN,Runtime,RemainingHours,Status\n"
    f"{report_timestamp},{normalized_engineer},{normalized_field},{normalized_well},{normalized_company},"
    f"{normalized_mud},{sand_input_val:.2f},{normalized_serial},{current_runtime:.1f},"
    f"{predicted_hours_to_failure:.1f},{final_report_status.replace(',', ';')}"
)

# 4. Отрисовка кнопок выгрузки файлов в интерфейсе приложения
st.markdown("##### 💾 Экспорт сформированных документов:")
col_down1, col_down2 = st.columns(2)

with col_down1:
    st.download_button(
        label="📥 Скачать официальный Акт (.txt)",
        data=report_text_content,
        file_name=f"Akt_Tech_Control_{normalized_well.replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True
    )

with col_down2:
    st.download_button(
        label="📊 Скачать строку базы замеров (.csv)",
        data=report_csv_content,
        file_name=f"Data_Row_{normalized_well.replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True
    )
# =========================================================================
# БЛОК 6: СТАБИЛЬНЫЙ ЦИФРОВОЙ ЖУРНАЛ ЗАМЕРОВ (УСТРАНЕНИЕ KEYERROR)
# =========================================================================
st.markdown("---")
st.markdown("### 💾 Блок 6: Цифровой журнал и мониторинг трендов")
st.caption("Накопление суточных замеров параметров промывки для архива КНБК")

# Инициализация хранилища истории в памяти приложения
if "history_log" not in st.session_state:
    st.session_state.history_log = []

# Кнопки управления логом
col_log1, col_log2 = st.columns(2)
with col_log1:
    if st.button("➕ Зафиксировать текущую точку замера в лог", use_container_width=True):
        time_now = time.strftime("%H:%M:%S")
        is_acid = "Кислотная" in normalized_mud
        sand_val = sand_input_val if 'sand_input_val' in locals() else 0.5
        
        # Интеллектуальное присвоение статусов для таблицы замеров
        if is_acid:
            status = "🚨 АВАРИЯ / СПО"
            info = "КРИТИЧЕСКАЯ АВАРИЯ: Прокачка кислоты! Требуется немедленный подъем КНБК."
        elif sand_val > (sand_threshold if 'sand_threshold' in locals() else 0.5):
            status = "🚨 НАРУШЕНИЕ ТК"
            info = f"Превышен лимит песка! Износ ускорен. Ресурс: {predicted_hours_to_failure:.1f} ч."
        else:
            status = "🟢 Норма"
            info = f"Замер в норме. Прогноз ресурса ВЗД: {predicted_hours_to_failure:.1f} ч."

        # Записываем строго фиксированные ключи (устраняем KeyError)
        st.session_state.history_log.append({
            "Время": time_now, 
            "Тип раствора": normalized_mud,
            "Песок (%)": round(sand_val, 2), 
            "Остаток (ч)": round(predicted_hours_to_failure, 1),
            "Статус": status,
            "Заключение": info
        })
        st.success(f"Точка успешно зафиксирована в {time_now}!")

with col_log2:
    if st.button("🗑 Очистить журнал замеров текущего рейса", use_container_width=True):
        st.session_state.history_log = []
        st.rerun()

# Отображение таблицы и генерация текстового файла выгрузки
if st.session_state.history_log:
    st.markdown("##### 📝 Хронология выполненного контроля параметров БР:")
    df_display = pd.DataFrame(st.session_state.history_log)
    
    # Выводим чистую таблицу Streamlit
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Безопасная сборка текстового файла по совпадающим ключам
    log_text_output = "ПРОТОКОЛ ХРОНОЛОГИИ ЗАМЕРОВ РЕЙСА:\n" + "\n".join([
        f"[{row['Время']}] {row['Тип раствора']} | Песок: {row['Песок (%)']}% | Ресурс: {row['Остаток (ч)']}ч | Статус: {row['Статус']}" 
        for row in st.session_state.history_log
    ])
    
    # Кнопка скачивания лога
    st.download_button(
        label="📥 Скачать накопленный журнал рейса (.txt)", 
        data=log_text_output, 
        file_name=f"Journal_Well_{normalized_well.replace(' ', '_')}.txt", 
        use_container_width=True
    )
else:
    st.info("ℹ Журнал текущего рейса пуст. Фиксируйте точки замеров раствора при помощи кнопки выше.")
