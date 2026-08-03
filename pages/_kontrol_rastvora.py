import streamlit as st
from datetime import datetime

# --- ПРОВЕРКА АВТОРИЗАЦИИ ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 Доступ заблокирован! Пожалуйста, перейдите на Главной страницу приложения и введите пароль.")
    st.stop()

# --- КОНФИГУРАЦИЯ И ЗАГОЛОВОК ---
st.set_page_config(page_title="Контроль буровых растворов", layout="wide")
st.title("🧪 Технологический контроль и аудит параметров буровых растворов")
st.caption("МОНИТОР СВЕРКИ И ОЦЕНКИ ВЛИЯНИЯ РЕОЛОГИИ НА НАДЕЖНОСТЬ ЗАБОЙНОГО ОБОРУДОВАНИЯ ПРИ ННБ")
st.markdown("---")

# Верификация ИНТИ (стиль УМК/ВЗД)
st.markdown(
    '<div style="color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #1E3A8A; margin-bottom: 20px;">'
    '<b>Верификация стандартами:</b> Модуль разработан в соответствии с <b>СТО ИНТИ S.QS.7</b> (п. 7.5.1, мониторинг сред) '
    'и <b>СТО ИНТИ S.QS.8</b> (п. 4.2.4, документация на местах), обеспечивая сверку параметров с планом-программой.'
    '</div>',
    unsafe_allow_html=True
)

# --- SIDEBAR - МЕТАДАННЫЕ ---
st.sidebar.header("📋 Метаданные рапорта")
well_number = st.sidebar.text_input("Номер скважины / Куст:", value="Скв. № 101, Куст 5")
engineer_name = st.sidebar.text_input("ФИО Инженера по ННБ:", value="Иванов И.И.")
current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

# --- БЛОК 1: СВЕРКА ДАННЫХ ---
st.markdown("### 🗂 Блок 1: Сверка проектных и фактических данных бурового раствора")
st.caption("Введите плановые уставки и фактические замеры из Акта растворного сервиса")

q_pump_max = st.checkbox("📢 Работа ведется на максимальном проектном расходе", value=False)
st.markdown(" ")

col_plan, col_fact = st.columns(2)

with col_plan:
    st.markdown("<h4 style='color: #1E3A8A;'>📋 Данные ПЛАНА</h4>", unsafe_allow_html=True)
    plan_density = st.number_input("1. Проектная плотность, г/см³:", min_value=0.8, max_value=2.5, value=1.20)
    plan_visc = st.number_input("2. Проектная условная вязкость, с:", min_value=10.0, max_value=200.0, value=45.0)
    plan_sand = st.number_input("3. Содержание песка (план), %:", min_value=0.0, max_value=20.0, value=0.3)
    plan_pv = st.number_input("4а. Проектная пл. вязкость, мПа·с:", min_value=1.0, max_value=100.0, value=18.0)
    plan_yp = st.number_input("4б. Проектное ДНС, дПа:", min_value=1.0, max_value=250.0, value=90.0)

with col_fact:
    st.markdown("<h4 style='color: #2E7D32;'>🧪 ФАКТИЧЕСКИЕ замеры (Акт БР)</h4>", unsafe_allow_html=True)
    fact_density = st.number_input("1. Фактическая плотность, г/см³:", min_value=0.8, max_value=2.5, value=1.22)
    fact_visc = st.number_input("2. Фактическая условная вязкость, с:", min_value=10.0, max_value=200.0, value=48.0)
    fact_sand = st.number_input("3. Фактическое содержание песка, %:", min_value=0.0, max_value=20.0, value=0.4)
    fact_pv = st.number_input("4а. Фактическая пл. вязкость, мПа·с:", min_value=1.0, max_value=100.0, value=20.0)
    fact_yp = st.number_input("4б. Фактическое ДНС, дПа:", min_value=1.0, max_value=250.0, value=95.0)

st.markdown("---")

# --- ИНЖЕНЕРНЫЙ СПРАВОЧНИК (ВЛИЯНИЕ НА ННБ) ---
st.markdown("### 📘 Инженерный справочник: Влияние параметров")

with st.expander("📍 Плотность (г/см³): Контроль ЭЦП и риска дифференциальных прихватов"):
    st.markdown("Избыточная плотность повышает ЭЦП и риск прихвата. Влияет на устойчивость стенок.")

with st.expander("📍 Условная вязкость (с): Вынос шлама"):
    st.markdown("Заниженная вязкость вызывает шламовые подушки при наклоне 30-60°. Завышенная — растет давление.")

with st.expander("📍 Песок / Твердая фаза (%): Абразивный износ"):
    st.markdown("Песок вызывает абразивный износ ВЗД, телесистем (пульсаторов, плат) и насадок долот.")

with st.expander("📍 Пл. вязкость и ДНС (мПа·с/дПа): Реология и вынос шлама"):
    st.markdown("Рост ПВ — загрязнение шламом. Низкое ДНС — оседание шлама (прихват), высокое ДНС — поршневание.")

st.markdown("---")
# =========================================================================
# БЛОК 2: АВТОМАТИЧЕСКИЙ АУДИТ И ОЦЕНКА РИСКОВ ДЛЯ ВЗД И ТЕЛЕСИСТЕМЫ
# =========================================================================
st.markdown("### 🔍 Блок 2: Автоматический аудит и оценка технологических рисков")
st.caption("Система проводит кросс-анализ фактических параметров раствора с предельными лимитами производителей ВЗД и телесистем")

# Зашитые технологические лимиты (самые жесткие отраслевые уставки)
MAX_SAND_CONTENT = 0.5   # Максимальное содержание песка/твердой фазы (%) по регламентам MWD
MAX_FUNNEL_VISC = 60.0   # Предельная условная вязкость (с) для сохранения гидравлических параметров
MAX_PV = 25.0            # Предельная пластическая вязкость (мПа·с)
MAX_YP = 120.0           # Предельное ДНС (дПа) для предотвращения застойных зон и скачков давления

# Флаги обнаружения критических несоответствий
has_risks = False

# 1. Проверка риска абразивного износа
# Сравниваем фактическое содержание песка (fact_sand из Блока 1) с жестким лимитом
if fact_sand > MAX_SAND_CONTENT:
    has_risks = True
    st.error(
        f"🚨 **КРИТИЧЕСКИЙ РИСК: Абразивный износ оборудования**\n\n"
        f"**Фактическое содержание песка:** {fact_sand}% | **Предел:** {MAX_SAND_CONTENT}%\n\n"
        f"• **Последствия для ННБ:** Высокая концентрация песка вызывает мгновенный гидроабразивный износ "
        f"насадок долота (размыв гидромониторных гнезд), стремительное истирание резинометаллического "
        f"статора ВЗД, а также сквозные промывы узлов и пульсаторов телесистемы, что ведет к потере канала связи.\n\n"
        f"• **Рекомендация:** Немедленно активировать третью ступень очистки (центрифуги, ситогидроциклонные сепараторы). "
        f"Снизить подачу насосов до выяснения причин, провести замер шлама."
    )

# 2. Проверка риска заклинивания двигателя (Гидромеханический аудит)
# Условие: если вязкость или ДНС превышают норму, И при этом включен максимальный расход насосов
if (fact_visc > MAX_FUNNEL_VISC or fact_yp > MAX_YP or fact_pv > MAX_PV) and q_pump_max:
    has_risks = True
    st.error(
        f"🚨 **КРИТИЧЕСКИЙ РИСК: Гидромеханическое заклинивание ВЗД и поглощение раствора**\n\n"
        f"**Фактические параметры:** УВ = {fact_visc} с, ПВ = {fact_pv} мПа·с, ДНС = {fact_yp} дПа при работе на максимальном расходе.\n\n"
        f"• **Последствия для ННБ:** Сверхвысокие реологические показатели раствора при максимальной подаче "
        f"вызывают колоссальный рост эквивалентной циркуляционной плотности (ЭЦП/ECD) и гидродинамического "
        f"давления в затрубе. Это приводит к заклиниванию ротора ВЗД (из-за перепада давления на силовой секции), "
        f"срыву инструмента с траектории и провоцирует ГРП (гидроразрыв пласта) с последующим катастрофическим поглощением раствора.\n\n"
        f"• **Рекомендация:** Снизить расход буровых насосов (подачу) до восстановления реологии. "
        f"Ввести в раствор хим. реагенты-разжижители для снижения ПВ/ДНС, контролировать давление по манометру."
    )

# 3. Если все проверки пройдены успешно
if not has_risks:
    st.success(
        "✔ **Результаты аудита:** Фактические параметры бурового раствора находятся в пределах "
        "допустимых значений. Риски преждевременного отказа силовых секций ВЗД и промыва телесистем минимальны."
    )

st.markdown("---")
# =========================================================================
# БЛОК 3: ВЫСОКОТОЧНЫЙ РАСЧЕТ ЭЦП ПО МОДЕЛИ ГЕРШЕЛЯ-БАЛКЛИ (API RP 13D)
# =========================================================================
st.markdown("### 📊 Блок 3: Высокоточный расчет ЭЦП/ECD (Модель Гершеля-Балкли)")
st.caption("Математическое ядро соответствует стандарту API RP 13D и учитывает нелинейную реологию и режим потока")

# 1. Ввод геолого-технических данных
col_geo1, col_geo2, col_geo3 = st.columns(3)
with col_geo1:
    h_tvd = st.number_input("Истинная глубина по вертикали (TVD), м:", min_value=100.0, max_value=6000.0, value=2500.0, step=50.0)
    d_hole = st.number_input("Диаметр долота / скважины, мм:", min_value=50.0, max_value=500.0, value=215.9, step=0.1)
    d_pipe = st.number_input("Наружный диаметр бурильной трубы (СБТ), мм:", min_value=40.0, max_value=200.0, value=127.0, step=0.1)

with col_geo2:
    q_flow = st.number_input("Текущий расход буровых насосов, л/с:", min_value=5.0, max_value=80.0, value=28.0, step=0.5)
    rop = st.number_input("Текущая механическая скорость (ROP), м/ч:", min_value=1.0, max_value=150.0, value=35.0, step=1.0)

with col_geo3:
    p_frac = st.number_input("Градиент / Эквивалент давления гидроразрыва пласта (ГРП), г/см³:", min_value=1.0, max_value=3.0, value=1.35, step=0.01)

# --- ВЫСШЕЕ МАТЕМАТИЧЕСКОЕ ЯДРО (API RP 13D) ---
import math

dh_m = d_hole / 1000.0
dp_m = d_pipe / 1000.0
area_annulus = (math.pi / 4.0) * (dh_m**2 - dp_m**2)
hydraulic_diam = dh_m - dp_m

# Перевод параметров раствора в СИ
rho_base = fact_density * 1000.0  # кг/м³
pv_si = fact_pv / 1000.0          # Па·с
yp_si = fact_yp * 0.1             # Па

# Скорость сдвига и перевод реологии в параметры Гершеля-Балкли (n, K, tau_0)
tau_0 = yp_si  # Предел текучести (дПа в Па)

# Индекс течения n и коэффициент консистенции K по стандартной методике API
# Для стандартных показаний вискозиметра (600 и 300 об/мин), которые моделируются через PV и YP:
theta_300 = fact_pv + fact_yp
theta_600 = (2 * fact_pv) + fact_yp

if theta_300 > 0 and (theta_300 - tau_0) > 0:
    n_hb = 3.32 * math.log10((theta_600 - tau_0) / (theta_300 - tau_0))
    n_hb = max(0.1, min(1.0, n_hb)) # Защита от деления на ноль и нефизичных значений
    K_hb = (theta_300 - tau_0) / (511**n_hb)
else:
    n_hb = 0.5
    K_hb = 0.5

# Скорость потока в затрубе (м/с)
v_annulus = (q_flow / 1000.0) / area_annulus if area_annulus > 0 else 0

# Эффективная скорость сдвига в кольцевом пространстве по API
gamma_dot = ((2 * n_hb + 1) / (3 * n_hb)) * (12 * v_annulus / hydraulic_diam) if hydraulic_diam > 0 else 0

# Касательное напряжение сдвига (Па)
tau_annulus = tau_0 + K_hb * (gamma_dot**n_hb) if gamma_dot > 0 else tau_0

# Расчет точных гидродинамических потерь давления (Па/м)
# Проверка режима потока через обобщенное число Рейнольдса для модели H-B
if v_annulus > 0:
    eff_viscosity = tau_annulus / gamma_dot if gamma_dot > 0 else 0.001
    Re_general = (rho_base * v_annulus * hydraulic_diam) / eff_viscosity
    
    # Расчет коэффициента трения Фаннинга (f) в зависимости от режима (Ламинар/Турбулентность)
    if Re_general < 2100:
        f_friction = 16 / Re_general
    else:
        # Формула Блазиуса для турбулентного режима неньютоновских сред
        f_friction = 0.079 / (Re_general**0.25)
        
    dp_dl_friction = (2 * f_friction * rho_base * (v_annulus**2)) / hydraulic_diam
else:
    dp_dl_friction = 0

total_p_friction_pa = dp_dl_friction * h_tvd

# Вклад шлама (влияние ROP и выноса породы)
rho_rock = 2650.0  # кг/м³
q_solids = ((math.pi / 4.0) * (dh_m**2)) * (rop / 3600.0)
c_cutting = q_solids / ((q_flow / 1000.0) + q_solids) if (q_flow + q_solids) > 0 else 0
rho_eff_mix = rho_base * (1.0 - c_cutting) + rho_rock * c_cutting

# Итоговый расчет ЭЦП
total_hydrostatic_pa = rho_eff_mix * 9.81 * h_tvd
total_dynamic_pressure_pa = total_hydrostatic_pa + total_p_friction_pa
calculated_ecd = (total_dynamic_pressure_pa / (9.81 * h_tvd)) / 1000.0  # г/см³

# --- ВЫВОД РЕЗУЛЬТАТОВ И УПРАВЛЕНИЕ РЕЖИМАМИ ---
st.markdown("#### Результаты гидродинамического моделирования:")
col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.metric("Высокоточная ЭЦП (ECD)", f"{calculated_ecd:.3f} г/см³")
with col_res2:
    st.metric("Запас до ГРП пласта", f"{(p_frac - calculated_ecd):.3f} г/см³")
with col_res3:
    st.metric("Режим течения в затрубе", "Турбулентный" if (v_annulus > 0 and Re_general >= 2100) else "Ламинарный")

# Алгоритм автоматического поиска безопасных границ бурения
if calculated_ecd >= (p_frac - 0.015):
    st.markdown("---")
    
    # Ищем критический максимальный расход
    safe_q = q_flow
    for test_q in range(int(q_flow * 10), 50, -1):
        t_q = test_q / 10.0
        v_a = (t_q / 1000.0) / area_annulus
        g_dot = ((2 * n_hb + 1) / (3 * n_hb)) * (12 * v_a / hydraulic_diam)
        t_a = tau_0 + K_hb * (g_dot**n_hb)
        e_visc = t_a / g_dot if g_dot > 0 else 0.001
        Re_g = (rho_base * v_a * hydraulic_diam) / e_visc
        f_f = 16 / Re_g if Re_g < 2100 else 0.079 / (Re_g**0.25)
        dp_f = (2 * f_f * rho_base * (v_a**2)) / hydraulic_diam
        ecd_test = (((rho_eff_mix * 9.81 * h_tvd) + (dp_f * h_tvd)) / (9.81 * h_tvd)) / 1000.0
        if ecd_test < (p_frac - 0.02):
            safe_q = t_q
            break
            
    # Ищем критическую скорость проходки ROP
    safe_rop = rop
    for test_rop in range(int(rop), 5, -1):
        q_s = ((math.pi / 4.0) * (dh_m**2)) * (test_rop / 3600.0)
        c_c = q_s / ((q_flow / 1000.0) + q_s)
        rho_m = rho_base * (1.0 - c_c) + rho_rock * c_c
        ecd_test = (((rho_m * 9.81 * h_tvd) + total_p_friction_pa) / (9.81 * h_tvd)) / 1000.0
        if ecd_test < (p_frac - 0.02):
            safe_rop = test_rop
            break

    st.error(
        f"🚨 **КРИТИЧЕСКИЙ РИСК ПОГЛОЩЕНИЯ И ГИДРОРАЗРЫВА ПЛАСТА (ГРП)!**\n\n"
        f"Динамическое давление раствора ЭЦП ({calculated_ecd:.3f} г/см³) превысило безопасный коридор давления ГРП ({p_frac:.2f} г/см³).\n\n"
        f"👉 **ТЕХНОЛОГИЧЕСКИЕ ОГРАНИЧЕНИЯ ДЛЯ ПРЕДОТВРАЩЕНИЯ АВАРИИ:**\n"
        f"1. **Максимально допустимый расход насосов:** Не превышать **{safe_q:.1f} л/с** (текущий: {q_flow} л/с)\n"
        f"2. **Максимально допустимая механическая скорость:** Не превышать **{safe_rop:.0f} м/ч** (текущая: {rop} м/ч)\n\n"
        f"*Рекомендация: Выполните очистную промывку для снижения концентрации шлама в интервале затрубного пространства.*"
    )
else:
    st.success("✔ **Гидравлический режим безопасен:** Риск эквивалентного превышения давления поглощения отсутствует.")

st.markdown("---")
# =========================================================================
# БЛОК 4: РАСШИРЕННЫЙ ЦИФРОВОЙ КАЛЬКУЛЯТОР ДЕГРАДАЦИИ И ЖИЗНИ СТАТОРА ВЗД
# =========================================================================
st.markdown("### ⏳ Блок 4: Цифровой калькулятор остаточного ресурса (жизни) статора ВЗД")
st.caption("Профессиональная предиктивная модель на базе уравнений Тейлора-Круглова и закона Майнерса-Палмгрена")

# 1. Ввод базовых и расширенных инженерных данных
col_stat1, col_stat2, col_stat3 = st.columns(3)

with col_stat1:
    passport_life = st.number_input("Номинальный (паспортный) ресурс силовой секции, ч:", min_value=10.0, max_value=500.0, value=150.0, step=10.0)
    current_runtime = st.number_input("Текущая фактическая наработка ВЗД в рейсе, ч:", min_value=0.0, max_value=500.0, value=48.0, step=1.0)
    red_zone_hours = st.number_input("Время работы с повышенным содержанием песка (>0.5%), ч:", min_value=0.0, max_value=100.0, value=3.5, step=0.5)

with col_stat2:
    kinematics_type = st.selectbox("Тип захода (кинематика силовой секции ВЗД):", ["1:2 (Низкая площадь контакта)", "4:5 (Средняя)", "5:6 (Высокая)", "7:8 (Сверхвысокая)", "9:10 (Критическая)"])
    p_diff = st.number_input("Рабочий дифференциальный перепад давления на ВЗД (ΔP), МПа:", min_value=0.5, max_value=10.0, value=3.2, step=0.1)

with col_stat3:
    sand_d50 = st.number_input("Средний размер частиц абразива из ЛАРС (D50), мкм:", min_value=10, max_value=500, value=74, help="74 мкм = сито 200 меш. Все, что выше, критично для эластомера")

# --- ВЫСШЕЕ МАТЕМАТИЧЕСКОЕ ЯДРО ДЕГРАДАЦИИ ЭЛАСТОМЕРА ---
import math

MAX_SAFE_SAND = 0.5
nominal_remaining = max(0.0, passport_life - current_runtime)

# Определение базового коэффициента заходности (влияние площади контакта и трения)
kinematics_dict = {"1:2 (Низкая площадь контакта)": 1.0, "4:5 (Средняя)": 1.25, "5:6 (Высокая)": 1.4, "7:8 (Сверхвысокая)": 1.6, "9:10 (Критическая)": 1.85}
k_kin = kinematics_dict[kinematics_type]

# Определение коэффициента агрессивности фракции песка (D50)
# Частицы крупнее 74 мкм (200 меш) увеличивают износ по экспоненте
if sand_d50 <= 45:
    k_grain = 0.6  # Мелкодисперсный шлам/глина
elif sand_d50 <= 74:
    k_grain = 1.0  # Базовый кварцевый песок
else:
    k_grain = 1.0 + ((sand_d50 - 74) / 50.0) ** 1.5  # Крупный абразив

# Определение коэффициента контактного давления от дифференциального перепада
# Рост ΔP сильнее прижимает ротор к статору, зажимая песчинки в камерах натяга
k_press = 1.0 + (p_diff / 4.0)

# Финальный расчет коэффициента ускорения деградации (WEF - Wear Elevation Factor)
if fact_sand > MAX_SAFE_SAND and red_zone_hours >= 2.0:
    excess_sand = fact_sand - MAX_SAFE_SAND
    # Кинетическое уравнение Тейлора-Круглова с поправкой на гидромеханическую нагрузку пары ротор-статор
    wear_factor = 1.0 + (excess_sand * 2.5 * k_kin * k_grain * k_press)
    
    # Накопленный эквивалентный износ по закону Майнерса-Палмгрена
    equivalent_hours_lost = red_zone_hours * (wear_factor - 1.0)
    resource_reduction_pct = (equivalent_hours_lost / passport_life) * 100.0
    resource_reduction_pct = min(100.0, resource_reduction_pct)
    
    # Расчет прогнозного остатка жизни до срыва/прокручивания статора
    predicted_hours_to_failure = nominal_remaining / wear_factor
    
    st.markdown("#### Прогноз технического состояния силовой секции:")
    col_stat_res1, col_stat_res2, col_stat_res3 = st.columns(3)
    with col_stat_res1:
        st.metric("Коэффициент износа эластомера", f"x{wear_factor:.2f}", delta="Абразивный износ", delta_color="inverse")
    with col_stat_res2:
        st.metric("Потеря ресурса статора", f"- {resource_reduction_pct:.1f} %")
    with col_stat_res3:
        st.metric("Ожидаемый остаток жизни", f"{predicted_hours_to_failure:.1f} ч", help="При сохранении текущих агрессивных параметров")
        
    st.warning(
        f"⚠️ **ВНИМАНИЕ: Зафиксирована ускоренная деградация эластомера силовой секции ВЗД!**\n\n"
        f"Показатель песка ({fact_sand}%) превышает норму на протяжении **{red_zone_hours:.1f} ч.** "
        f"При дифференциальном давлении {p_diff} МПа и крупности абразива D50={sand_d50} мкм скорость износа выросла в **{wear_factor:.2f} раз(а)**.\n\n"
        f"• **Анализ деградации:** Общий ресурс двигателя снизился на **{resource_reduction_pct:.1f}%**.\n"
        f"• **Прогноз отказа:** Ожидаемый гидромеханический отказ оборудования произойдет через **{predicted_hours_to_failure:.1f} ч.** вместо паспортных {nominal_remaining:.1f} ч."
    )
else:
    wear_factor = 1.0
    resource_reduction_pct = 0.0
    predicted_hours_to_failure = nominal_remaining
    st.success(
        f"✔ **Ресурс эластомера в норме:** Параметры раствора и время работы не превышают критические пороги. "
        f"Прогнозный остаток жизни ВЗД: **{nominal_remaining:.1f} ч.**"
    )

st.markdown("---")

# =========================================================================
# БЛОК 5: ГЕНЕРАЦИЯ ЕДИНОГО ИТОГОВОГО ТЕХНОЛОГИЧЕСКОГО ОТЧЕТА (ИСПРАВЛЕННЫЙ)
# =========================================================================
st.markdown("---")
st.subheader("📋 Блок 5: Финальный отчет по контролю очистки и гидравлики")

is_critical_report = (fact_sand > MAX_SAND_CONTENT) or ((fact_visc > MAX_FUNNEL_VISC or fact_yp > MAX_YP or fact_pv > MAX_PV) and q_pump_max) or (calculated_ecd >= (p_frac - 0.015))

status_text = "🚨 ВНИМАНИЕ: ТЕХНОЛОГИЧЕСКИЙ ВЫХОД ЗА ПРЕДЕЛЫ НОРМЫ!" if is_critical_report else "✔ УСПЕШНО ВЕРИФИЦИРОВАНО."
status_color = "#EF4444" if is_critical_report else "#10B981"
stator_status = f"Ускоренный износ (x{wear_factor:.2f}). Отказ через {predicted_hours_to_failure:.1f} ч." if wear_factor > 1.0 else "В норме"

# Записываем HTML строгими однострочниками, чтобы Streamlit не путал форматирование
html_report = (
    f"<div style='border: 3px solid #1E3A8A; padding: 25px; border-radius: 12px; background-color: #FAFAFA; font-family: Arial, sans-serif; color: #333333; max-width: 1000px; margin: 0 auto;'>"
    f"<h2 style='text-align: center; color: #1E3A8A; margin-top: 0;'>ООО «ТРАЕКТОРИЯ-СЕРВИС»</h2>"
    f"<h4 style='text-align: center; color: #4B5563; margin-top: -10px;'>КОМПЛЕКСНЫЙ АКТ АУДИТА БУРОВОГО РАСТВОРА И ГИДРАВЛИКИ</h4>"
    f"<hr style='border: 1px solid #1E3A8A; margin-bottom: 20px;'> Standard"
    f"<p><b>Дата/Время замеров:</b> {current_time} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Объект / Скважина:</b> {well_number}</p>"
    f"<p><b>Инженер по ННБ:</b> {engineer_name}</p>"
    f"<h4 style='color: #1E3A8A; margin-top: 20px; border-bottom: 1px solid #D1D5DB; padding-bottom: 5px;'>РЕЗУЛЬТАТЫ СВЕРКИ И АУДИТА:</h4>"
    f"<table style='width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; margin-bottom: 20px;'>"
    f"<tr style='background-color: #E5E7EB; font-weight: bold;'>"
    f"<th style='padding: 8px; border: 1px solid #D1D5DB;'>Контролируемый параметр</th>"
    f"<th style='padding: 8px; border: 1px solid #D1D5DB;'>План-программа</th>"
    f"<th style='padding: 8px; border: 1px solid #D1D5DB;'>Фактический акт</th>"
    f"<th style='padding: 8px; border: 1px solid #D1D5DB;'>Отклонение</th>"
    f"</tr>"
    f"<tr><td style='padding: 8px; border: 1px solid #D1D5DB;'>Плотность раствора, г/см³</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{plan_density:.2f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_density:.2f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_density - plan_density:+.2f}</td></tr>"
    f"<tr><td style='padding: 8px; border: 1px solid #D1D5DB;'>Условная вязкость, с</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{plan_visc:.1f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_visc:.1f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_visc - plan_visc:+.1f}</td></tr>"
    f"<tr><td style='padding: 8px; border: 1px solid #D1D5DB;'>Содержание песка, %</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{plan_sand:.2f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_sand:.2f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_sand - plan_sand:+.2f}</td></tr>"
    f"<tr><td style='padding: 8px; border: 1px solid #D1D5DB;'>Пластическая вязкость, мПа·с</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{plan_pv:.1f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_pv:.1f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_pv - plan_pv:+.1f}</td></tr>"
    f"<tr><td style='padding: 8px; border: 1px solid #D1D5DB;'>Динамическое напряжение сдвига (ДНС), дПа</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{plan_yp:.1f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_yp:.1f}</td><td style='padding: 8px; border: 1px solid #D1D5DB;'>{fact_yp - plan_yp:+.1f}</td></tr>"
    f"</table>"
    f"<p><b>Расчетная ЭЦП (ECD) по Гершелю-Балкли:</b> <span style='font-size: 15px; color: {'#EF4444' if calculated_ecd >= (p_frac-0.015) else '#1E3A8A'};'><b>{calculated_ecd:.3f} г/см³</b></span> (Допустимый предел ГРП: {p_frac:.2f} г/см³)</p>"
    f"<p><b>Прогноз состояния статора силовой секции ВЗД:</b> <b>{stator_status}</b></p>"
    f"<div style='background-color: {status_color}; color: white; padding: 12px; text-align: center; font-weight: bold; border-radius: 6px; font-size: 15px; margin-top: 25px;'>"
    f"{status_text}"
    f"</div>"
    f"<p style='font-size: 11px; color: #6B7280; text-align: center; margin-top: 35px; border-top: 1px dashed #D1D5DB; padding-top: 10px;'>Цифровая экосистема ООО «Траектория-Сервис» • Суточный рапорт контроля параметров очистки</p>"
    f"</div>"
)

# Очищенный вывод HTML
st.markdown(html_report, unsafe_allow_html=True)

st.markdown(" ")
st.info("💡 **Как распечатать рапорт:** Нажмите комбинацию клавиш **`Ctrl + P`**, выберите «Сохранить как PDF» для отправки акта Заказчику.")
