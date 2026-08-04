# Нам понадобятся новые библиотеки для оптимизации и сохранения обученных данных
from scipy.optimize import minimize_scalar
import json

# Инициализируем сессию Streamlit для хранения «обученных» коэффициентов в памяти,
# чтобы система не забывала их при обновлении страницы браузера
if "learned_han" not in st.session_state:
    st.session_state.learned_han = {}

# -----------------------------------------------------------------------------
# МАТЕМАТИЧЕСКАЯ ФУНКЦИЯ ОБРАТНОГО РАСЧЕТА (ОБУЧЕНИЕ СИСТЕМЫ)
# -----------------------------------------------------------------------------
def back_analysis_calibration(fact_dogleg, wob_t, angle_deg, L_m, stiffness_factor, mud_rho):
    """
    Обратный расчет (Back-Analysis) истинного коэффициента анизотропии.
    Минимизирует среднеквадратичную ошибку между фактом и математической моделью.
    """
    # Функция ошибки, которую Python будет сводить к нулю
    def loss_function(test_han):
        # 1. Считаем боковую силу по физической модели
        P_b_calc = calculate_p_b(wob_t, angle_deg, L_m, stiffness_factor, mud_rho)
        # 2. Считаем прогнозный доглег при тестовом коэффициенте анизотропии
        pred_dogleg = abs(P_b_calc * test_han) / 1000.0
        # 3. Возвращаем квадрат разности (ошибку)
        return (fact_dogleg - pred_dogleg) ** 2
    
    # Запускаем оптимизатор. Ищем истинный H_an в строгих физических границах от 1.0 до 1.5
    result = minimize_scalar(loss_function, bounds=(1.0, 1.5), method='bounded')
    
    if result.success:
        return round(result.x, 3)
    else:
        return None

# -----------------------------------------------------------------------------
# ИНТЕРФЕЙСНЫЙ БЛОК САМООБУЧЕНИЯ (Внедрить внизу вашего файла)
# -----------------------------------------------------------------------------
st.header("🔄 Контур адаптивного самообучения системы (PDCA)")

with st.expander("Открыть панель калибровки модели по пробуренным скважинам", expanded=False):
    st.write("Введите фактические параметры с буровой по завершенному интервалу, чтобы обучить систему.")
    
    col_cal1, col_cal2 = st.columns(2)
    with col_cal1:
        fact_dogleg = st.number_input("Реальная пространственная интенсивность по инклинометру (°/10м):", min_value=0.0, max_value=7.0, value=2.1, step=0.1)
        cal_wob = st.number_input("Фактическая осевая нагрузка в этом интервале (тонн):", min_value=2.0, max_value=25.0, value=12.0, step=0.5)
    with col_cal2:
        cal_angle = st.number_input("Фактический зенитный угол в интервале (°):", min_value=0.0, max_value=90.0, value=32.0, step=1.0)
        cal_mud = st.number_input("Фактическая плотность БР при бурении (г/см³):", min_value=1.0, max_value=2.2, value=mud_density, step=0.01)

    if st.button("🧠 Запустить Back-Analysis и обучить модель"):
        # Вызываем оптимизатор
        new_han = back_analysis_calibration(fact_dogleg, cal_wob, cal_angle, L_param, stiff_param, cal_mud)
        
        if new_han:
            # Сохраняем обученный коэффициент для текущей свиты в память сессии
            st.session_state.learned_han[current_suite] = new_han
            st.success(f"📈 Система успешно обучена! Настоящий коэффициент анизотропии для свиты '{current_suite}' равен: **{new_han}**")
            st.balloons() # Немного Streamlit-магии для настроения
        else:
            st.error("Не удалось сойтись к стабильному решению. Проверьте корректность введенных физических данных.")

# Корректируем базовую логику: если в памяти есть обученный коэффициент, приоритет отдается ему!
if current_suite in st.session_state.learned_han:
    h_an_active = st.session_state.learned_han[current_suite]
    st.caption(f"🤖 **Внимание:** Базовый коэффициент перехвачен контуром обучения. Используется калиброванное значение: **{h_an_active}**")
