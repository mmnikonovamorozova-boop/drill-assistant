import streamlit as st
import json
import os
import requests
import pandas as pd
import io
from datetime import datetime

# --- СИНХРОНИЗАЦИЯ И ИНИЦИАЛИЗАЦИЯ МЕТАДАННЫХ ---
# Если данные уже были введены на 4-й странице, они подтянутся сюда автоматически
if "well_number" not in st.session_state:
    st.session_state["well_number"] = "Скв. № 102, Куст 12"
if "engineer_name" not in st.session_state:
    st.session_state["engineer_name"] = "Иванов И.И."
if "field_name" not in st.session_state:
    st.session_state["field_name"] = "Приобское"

# --- ПРОВЕРКА АВТОРИЗАЦИИ СЕССИИ ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Выполните авторизацию на главной странице.")
    st.stop()

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ТЕХКАРТ ---
st.set_page_config(page_title="Технологические карты инцидентов", page_icon="🛠️", layout="wide")
st.title("🛠️ Технологические карты и Профили инцидентов (DD/MWD)")
st.caption("Автоматизированные чек-листы ликвидации брака, трибологические расчеты и верификация по СТО ИНТИ")

# Принудительные CSS-стили для корректного вывода бланка на печать в PDF
st.markdown("""
<style>
    /* Делаем так, чтобы при прямой генерации документа не было лишних полей */
    @page {
        size: A4;
        margin: 20mm;
    }
    .print-preview {
        font-family: 'Arial', sans-serif;
        color: #000000 !important;
        background-color: #ffffff !important;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# БЛОК ВЕРИФИКАЦИИ ИНТИ (НАВЕРХУ СТРАНИЦЫ)
# ==============================================================================
st.markdown("<div style='color: #4B5563; font-size: 13px; background-color: #F3F4F6; padding: 12px; border-radius: 6px; border-left: 4px solid #6B7280; margin-bottom: 20px; line-height: 1.5; font-family: Arial, sans-serif;'><b>Верификация стандартами:</b> Данный интерактивный модуль оперативного контроля технологической дисциплины на устье разработан в строгом соответствии с требованиями отраслевых стандартов <b>СТО ИНТИ S.30.13</b> в части проведения визуально-измерительного контроля резьбовых соединений и регламентации гидроиспытаний, <b>СТО ИНТИ S.QS.7 (п. 7.4.2 «Верификация закупаемой продукции», п. 7.5.1 «Управление производством и предоставлением услуг»)</b> в части обеспечения персонала четкими документированными инструкциями, регламентации процессов нанесения резьбовых смазок и контроля крутящих моментов свинчивания КНБК, а также <b>СТО ИНТИ S.QS.8 (п. 5.3.1 «Управление процессами. Контроль параметров» и п. 5.7.2 «Управление оборудованием для мониторинга и измерений»)</b> в части обязательного вывода буровых насосов на регламентный режим расхода при опрессовке (не менее 25% от рабочего) и контроля исправности, калибровки и метрологического подтверждения применяемых на буровой площадке гидравлических ключей и манометров устьевого манифольда.</div>", unsafe_allow_html=True)

st.markdown("---")

# --- СБОР И СИНХРОНИЗАЦИЯ МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")

# Связываем инпуты с session_state для сквозной синхронизации страниц
well_number = st.sidebar.text_input(
    "Номер скважины / Куст:", 
    value=st.session_state["well_number"],
    key="well_input"
)
st.session_state["well_number"] = well_number

engineer_name = st.sidebar.text_input(
    "ФИО Инженера по ННБ:", 
    value=st.session_state["engineer_name"],
    key="eng_input"
)
st.session_state["engineer_name"] = engineer_name

field_name = st.sidebar.text_input(
    "Месторождение:", 
    value=st.session_state["field_name"],
    key="field_input"
)
st.session_state["field_name"] = field_name

st.sidebar.markdown("---")
st.sidebar.info("💡 Метаданные синхронизированы с модулем Матрицы ЛНД и автоматически попадут во все генерируемые акты.")
# --- ОТКАЗОУСТОЙЧИВАЯ ФУНКЦИЯ ЗАГРУЗКИ ТЕХКАРТ ---
@st.cache_data(ttl=60)
@st.cache_data(ttl=60)
@st.cache_data(ttl=60)
def load_tech_cards_database():
    filename = "tech_requirements.json"
    
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.sidebar.error(f"⚠️ Ошибка чтения {filename}: {str(e)}")
            
    st.sidebar.warning(f"⚠️ База данных {filename} инициализирована официальными регламентами.")
    
    fallback_data = {
        "Предупреждение незапланированных СПО (Р-ТС-16)": {
            "title": "Регламент предупреждения дополнительных СПО при снижении МСП на Пальяновской площади",
            "inti_standard": "Р-ТС-16, СТО ИНТИ S.QS.7, СТО ИНТИ S.QS.8",
            "description": "Порядок действий инженеров по телеметрии и ННБ при падении механической скорости проходки в целях исключения необоснованного подъема исправного оборудования и НПВ.",
            "verification_route": [
                {"step": "Провести дрилл-тест с составлением официального акта за подписью супервайзера", "role": "Инженер по ННБ"},
                {"step": "Проверить фактическое число ходов буровых насосов и запросить у ГТИ шламограмму", "role": "Инженер по бурению"},
                {"step": "Произвести контроль содержания силицитов в шламе (особое внимание при превышении 10%)", "role": "Инженер по бурению"},
                {"step": "Проверить данные инклинометрии и спектр забойных вибраций на наличие магнитных помех", "role": "Инженер по телеметрии"}
            ],
            "recommendations": [
                "При распоряжении Заказчика о подъеме КНБК из-за снижения МСП незамедлительно информировать координатора проекта.",
                "Только после проведения всех регламентных проверок и дрилл-теста, если ситуация не улучшилась, приступать к СПО."
            ],
            "diagrams": {
                "Роснефть": "pages/img/r_ts_16_rn.png",
                "Газпром нефть": "pages/img/r_ts_16_gpn.png",
                "Лукойл": "pages/img/r_ts_16_luk.png"
            }
        },
        "Ликвидация затяжек и прихватов (Р-ТС-19)": {
            "title": "Алгоритм ИТР при возникновении затяжек, посадок и угрозы прихвата бурильной колонны",
            "inti_standard": "Р-ТС-19 (Приложение 1 и 2), СТО ИНТИ S.QS.8",
            "description": "Экстренный регламент действий буровой бригады и инженеров ННБ при потере подвижности инструмента на устье или в открытом стволе.",
            "verification_route": [
                {"step": "При затяжке > 5 т прекратить подъем, опустить колонну ниже места затяжки на 1-2 свечи", "role": "Инженер по бурению"},
                {"step": "Восстановить циркуляцию с минимальной подачей, ступенчато доводя расход до нормы после выравнивания давления", "role": "Буровой подрядчик"},
                {"step": "Для улучшения слайдирования в интервалах ориентированного бурения обеспечить ввод смазки 2-5% по объему", "role": "Супервайзер"},
                {"step": "При бурении в прихватоопасной зоне / продуктивном пласте ограничить время простоя без движения до <= 3 минут", "role": "Инженер по бурению"}
            ],
            "recommendations": [
                "Для КНБК с ВЗД-172 выдерживать щадящий расход 26-30 л/с, для ВЗД-240 – 46-48 л/с во во избежание гидроразрыва пласта.",
                "Промывку перед наращиванием (минимум 15 мин) вести строго с вращением инструмента >= 40 об/мин и интенсивным расхаживанием."
            ],
            "diagrams": {
                "Роснефть": "pages/img/r_ts_19_prihvat_rn.png",
                "Газпром нефть": "pages/img/r_ts_19_prihvat_gpn.png",
                "Лукойл": "pages/img/r_ts_19_prihvat_luk.png",
                "ИНТИ": "pages/img/r_ts_19_prihvat_inti.png"
            }
        },
        "Борьба с вибрациями КНБК (И-ТС-55)": {
            "title": "Порядок действий персонала при обнаружении признаков вибраций КНБК",
            "inti_standard": "И-ТС-55, СТО ИНТИ S.QS.8",
            "description": "Методы оперативного гашения осевых, радиальных и торсионных колебаний бурильной колонны.",
            "verification_route": [
                {"step": "Запрограммировать ТМС на вывод показаний вибрации в реальном времени (на объектах с ожидаемой вибрацией)", "role": "Инженер по телеметрии"},
                {"step": "При фиксации вибрации 1-го уровня (зеленый) незамедлительно принять меры по изменению нагрузки/оборотов", "role": "Инженер по бурению"},
                {"step": "При 2-м уровне (желтый) известить супервайзера и бурового мастера; при 3-м уровне (красного) — немедленно остановить бурение", "role": "Инженер по бурению"},
                {"step": "После окончания рейса считать архивную память прибора по вибрациям и передать диаграмму в сервисный центр", "role": "Инженер по телеметрии"}
            ],
            "recommendations": [
                "При осевой вибрации: увеличить нагрузку на долото на 1 т и синхронно уменьшить количество оборотов.",
                "При радиальной вибрации: уменьшить скорость вращения на 10% и увеличить нагрузку на долото на 10%.",
                "При торсионной вибрации: переключить верхний привод на верхнюю передачу, уменьшить нагрузку на 5%, обороты на 10%."
            ],
            "diagrams": {
                "Роснефть": "pages/img/i_ts_55_vibrations_rn.png",
                "Газпром нефть": "pages/img/i_ts_55_vibrations_gpn.png",
                "Лукойл": "pages/img/i_ts_55_vibrations_luk.png",
                "ИНТИ": "pages/img/i_ts_55_vibrations_inti.png"
            }
        }
    }
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(fallback_data, f, ensure_ascii=False, indent=4)
    except:
        pass
        
    return fallback_data

    # Финальное сохранение сгенерированного файла и возврат данных
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(fallback_data, f, ensure_ascii=False, indent=4)
    except:
        pass
        
    return fallback_data
# --- БЛОК ИНТЕГРАЦИИ ГРАФИЧЕСКИХ БЛОК-СХЕМ И СЛАЙДОВ (Р-ТС-12/16/19, И-ТС-55) ---
card_diagrams = current_card.get("diagrams", {})

if card_diagrams and isinstance(card_diagrams, dict):
    # Пытаемся получить путь к картинке для конкретно выбранного инженером Заказчика
    img_path = card_diagrams.get(selected_client)
    
    if img_path:
        st.markdown(f"#### 🗺️ Технологическая схема регламента под требования: {selected_client}")
        
        # Проверяем физическое наличие файла в репозитории перед выводом, чтобы избежать сбоев
        if os.path.exists(img_path):
            st.image(
                img_path, 
                caption=f"Официальный регламентный слайд / блок-схема ликвидации осложнения компании {selected_client}",
                use_container_width=True
            )
        else:
            st.info(f"ℹ️ Для просмотра графической схемы загрузите файл `{img_path}` в папку вашего репозитория GitHub.")
            st.caption("При отсутствии файла на сервере система автоматически переключается на текстовый маршрут верификации ИНТИ ниже.")

    # Сохраняем её локально, чтобы файл физически появился в системе
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(fallback_data, f, ensure_ascii=False, indent=4)
    except:
        pass
        
    return fallback_data

# Инициализируем базу данных техкарт
tech_data = load_tech_cards_database()
if not tech_data:
    st.error("❌ Критическая ошибка: Не удалось загрузить базу данных техкарт.")
    st.stop()
st.subheader("🎯 Выбор технологической карты инцидента")

# Получаем полный список инцидентов из загруженной базы данных
incident_list = list(tech_data.keys())

# Логика сквозного перехода: проверяем, пришел ли автоматический запрос со страницы Матрицы ЛНД
default_index = 0
if "auto_incident" in st.session_state and st.session_state["auto_incident"] in incident_list:
    # Находим индекс инцидента, переданного из матрицы, чтобы подставить его по умолчанию
    default_index = incident_list.index(st.session_state["auto_incident"])
    st.info(f"🔄 Автоматический переход из Матрицы ЛНД по инциденту: **{st.session_state['auto_incident']}**")
    # Сразу очищаем триггер, чтобы при ручном обновлении страницы индекс не залипал
    del st.session_state["auto_incident"]

# Интерактивный селектбокс с динамическим индексом
selected_incident = st.selectbox(
    "Выберите тип брака или инцидента для ликвидации:",
    incident_list,
    index=default_index,
    key="incident_selector"
)

# Вытаскиваем все данные по выбранной техкарте
current_card = tech_data.get(selected_incident, {})
st.markdown("---")

# 1. Основное описание инцидента и стандарты ИНТИ
title_text = current_card.get("title", selected_incident)
inti_text = current_card.get("inti_standard", "СТО ИНТИ S.QS.7")
desc_text = current_card.get("description", "")

st.markdown(f"### 📋 {title_text}")
st.markdown(f"**Соответствие стандартам:** `{inti_text}`")
st.write(desc_text)

st.markdown("---")
st.markdown("### 🧮 Трибологический калькулятор момента свинчивания замка")
st.caption("Автоматический расчет момента на гидроключе УМК по СТО ИНТИ S.QS.7 при изменении коэффициента трения смазки")

col_c1, col_c2 = st.columns(2)
with col_c1:
    nominal_torque = st.number_input(
        "Номинальный момент свинчивания по паспорту резьбы (кН*м):", 
        min_value=1.0, 
        max_value=100.0, 
        value=25.0, 
        step=0.5
    )
with col_c2:
    lubricant_type = st.radio(
        "Тип применяемой резьбовой смазки на устье:",
        ["Стандартная (Медно-графитовая)", "Безметалловая полимерная (сертифицированная ИНТИ)"],
        horizontal=True
    )

# Расчет коэффициента и финального момента
friction_coeff = 1.0
if lubricant_type == "Безметалловая полимерная (сертифицированная ИНТИ)":
    # Понижающий трибологический коэффициент 0.875 (-12.5% к трению замка)
    friction_coeff = 0.875

target_torque = round(nominal_torque * friction_coeff, 2)

# Выводим инженеру четкую рекомендацию для гидроключа
if friction_coeff < 1.0:
    st.warning(f"⚠️ Внимание: Безметалловая смазка снижает трение. Для предотвращения скрытого разрыва замка ВЗД снизьте момент на гидроключе УМК!")
    st.markdown(f"🎯 **Рекомендуемый момент затяжки на гидроключе УМК:** `{target_torque} кН*м` *(Понижающий коэффициент {friction_coeff})*")
else:
    st.success(f"✅ Параметры свинчивания в норме.")
    st.markdown(f"🎯 **Рекомендуемый момент затяжки на гидроключе УМК:** `{target_torque} кН*м` *(Номинальный режим)*")
st.markdown("---")
st.markdown("### 🗺️ Маршрут операционной верификации параметров (СТО ИНТИ S.QS.8)")
st.caption("Пошаговый контроль технологических звеньев на устье скважины при ликвидации брака")

route_steps = current_card.get("verification_route", [])
verified_route_data = []

if route_steps and isinstance(route_steps, list):
    for i, step_item in enumerate(route_steps):
        if not isinstance(step_item, dict):
            continue
            
        step_title = step_item.get("step", f"Шаг № {i+1}")
        step_role = step_item.get("role", "ИТР")
        
        st.markdown(f"#### 🛑 Шаг {i+1}: {step_title}")
        st.markdown(f"**Зона контроля:** `{step_role}`")
        
        # Интерактивный выбор статуса прохождения шага на буровой
        step_status = st.radio(
            f"Технологический статус выполнения шага {i+1}:",
            ["Штатно (Параметры верифицированы)", "Сбой (Выявлено отклонение от ЛНД)"],
            key=f"status_step_{i}",
            horizontal=True
        )
        
        # Дополнительное поле для фиксации фактических данных инженером
        fact_comment = st.text_input(
            f"Фактические параметры / Примечание к шагу {i+1}:",
            value="",
            key=f"comment_step_{i}",
            placeholder="Например: Люфт устранен, манометр поверен, смазка нанесена..."
        )
        
        if step_status == "Сбой (Выявлено отклонение от ЛНД)":
            st.error(f"🚨 Внимание: Зафиксировано нарушение регламента на этапе контроля: '{step_role}'!")
            
        st.markdown("---")
        
        # Сохраняем данные шага для генерации итогового рапорта
        verified_route_data.append({
            "step_num": i + 1,
            "title": step_title,
            "role": step_role,
            "status": step_status,
            "comment": fact_comment if fact_comment else "Без комментариев"
        })
else:
    st.info("ℹ️ Для выбранного инцидента маршрут верификации в базе данных не задан.")
st.markdown("### 💼 Ограничения Заказчиков и превентивные рекомендации")

# Вытягиваем ограничения текущего инцидента из словаря current_card
card_restrictions = current_card.get("restrictions", {})
available_card_clients = list(card_restrictions.keys()) if card_restrictions else ["Роснефть", "Газпром нефть", "Лукойл", "ИНТИ"]

# Пытаемся автоматически определить заказчика из глобальной памяти Матрицы ЛНД
default_client_index = 0
if "global_selected_client" in st.session_state and st.session_state["global_selected_client"] in available_card_clients:
    default_client_index = available_card_clients.index(st.session_state["global_selected_client"])

# Селектбокс выбора Заказчика
selected_client = st.selectbox(
    "💼 Выберите компанию Заказчика для адаптации техкарты:",
    available_card_clients,
    index=default_client_index,
    key="client_selector_tech"
)
st.markdown("---")
if card_restrictions and isinstance(card_restrictions, dict):
    client_res = card_restrictions.get(selected_client, "Специфических ограничений не зафиксировано.")
    st.warning(f"⚠️ Ограничение компании {selected_client}: {client_res}")
else:
    st.info("ℹ️ Специфических ограничений Заказчиков для данного инцидента не найдено.")
recommendations = current_card.get("recommendations", [])
if recommendations and isinstance(recommendations, list):
    st.markdown("#### 💡 Рекомендации по предотвращению повторения брака:")
    for rec in recommendations:
        st.info(f"• {rec}")

st.markdown("### 📄 Отчетность и фиксация параметров")

# 3. Кнопка формирования и скачивания рапорта верификации инцидента
if st.button("📝 Сформировать Рапорт ликвидации технологического брака"):
    # Собираем текстовый документ построчно через список строк
    lines = [
        "РАПОРТ ЛИКВИДАЦИИ ТЕХНОЛОГИЧЕСКОГО БРАКА И ВЕРИФИКАЦИИ ПАРАМЕТРОВ",
        f"Дата и время формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        f"Месторождение: {st.session_state['field_name']}",
        f"Скважина / Куст: {st.session_state['well_number']}",
        f"Инженер по ННБ: {st.session_state['engineer_name']}",
        "========================================",
        f"Тип инцидента: {title_text}",
        f"Нормативная база: {inti_text}",
        "----------------------------------------",
        "РЕЗУЛЬТАТЫ ТРИБОЛОГИЧЕСКОГО РАСЧЕТА МОМЕНТА СВИНЧИВАНИЯ КНБК:",
        f" Выбранный тип смазки резьбы: {lubricant_type}",
        f" Паспортный (номинальный) момент: {nominal_torque} кН*м",
        f" Финальный расчетный момент для гидроключа УМК: {target_torque} кН*м",
        "----------------------------------------",
        "РЕЗУЛЬТАТЫ ПОШАГОВОЙ ПОЛЕВОЙ ВЕРИФИКАЦИИ МАРШРУТА:",
        ""
    ]
    
    # Добавляем данные по каждому шагу верификации маршрута
    for step in verified_route_data:
        lines.append(f"Шаг {step['step_num']}: {step['title']}")
        lines.append(f" Зона ответственности: {step['role']}")
        lines.append(f" Технологический статус: {step['status']}")
        lines.append(f" Примечание инженера: {step['comment']}")
        lines.append("")
        
    lines.append("========================================")
    lines.append("Подписи сторон на устье скважины:")
    lines.append("")
    lines.append("Инженер по ННБ: _______________________")
    lines.append("")
    lines.append("Представитель Бурового подрядчика: _______________________")
    lines.append("")
    lines.append("Супервайзер Заказчика: _______________________")
    
    # Объединяем список строк в единую текстовую переменную
    report_content = "  ".join([l + "  " for l in lines])
    
    st.success("✅ Официальный Рапорт верификации успешно сформирован!")
    st.download_button(
        label="📥 Скачать Рапорт ликвидации инцидента (TXT)",
        data=report_content,
        file_name=f"Incident_Report_{st.session_state['well_number'].replace(' ', '_')}.txt",
        mime="text/plain"
    )
