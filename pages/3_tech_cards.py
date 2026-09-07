import streamlit as st
import json
import os
import requests
import pandas as pd
import io
from datetime import datetime

# Инициализация сессионных переменных и проверка авторизации
if "well_number" not in st.session_state:
    st.session_state["well_number"] = "Скв. № 102, Куст 12"
if "engineer_name" not in st.session_state:
    st.session_state["engineer_name"] = "Иванов И.И."
if "field_name" not in st.session_state:
    st.session_state["field_name"] = "Приобское"

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("🚨 ДОСТУП ОГРАНИЧЕН: Выполните авторизацию на главной странице.")
    st.stop()

st.set_page_config(page_title="Технологические карты инцидентов", page_icon="🛠", layout="wide")
st.title("🛠 Технологические карты и Профили инцидентов (DD/MWD)")
st.caption("Автоматизированные чек-листы ликвидации брака, трибологические расчеты и верификация по СТО ИНТИ")
# --- СБОР И СИНХРОНИЗАЦИЯ МЕТАДАННЫХ (SIDEBAR) ---
st.sidebar.header("📋 Метаданные рапорта")

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

@st.cache_data(ttl=10)
def load_tech_cards_database():
    base_dir = "repository"
    tech_cards = {}
    
    # Справочник красивых имен для категорий
    categories = {
        "1_methods": "Методики и навигация",
        "2_tech_processes": "Технологические процессы",
        "3_incidents": "Ликвидация осложнений"
    }
    
    # 1. СЛОВАРЬ ПЕРЕВОДА ДЛЯ ПАПКИ 1_METHODS
    translation_map = {
        "mwd_downhole_failure_flowchart": "Регламент локализации скважинного отказа ТМС на забое",
        "mwd_surface_testing_flowchart": "Тестирование и дефектоскопия ТМС на поверхности перед спуском",
        "tech_incidents_response_flowchart": "Порядок реагирования ИТР на технологические инциденты",
        "trajectory_deviation_control_flowchart": "Контроль интенсивности увода ствола и пространственного угла"
    }
  
    # 2.1. СЛОВАРЬ ПЕРЕВОДА ДЛЯ ПАПКИ 2_TECH_PROCESSES (ЧАСТЬ А)
    translation_map.update({
        "anti_collision_monitoring_flowchart": "Регламент предотвращения пересечения стволов (Анти-коллизия)",
        "bha_inspection_and_tally_flowchart": "Инспекция, дефектоскопия элементов КНБК и калибровка на мостках",
        "bha_run_in_hole_protocol": "Протокол контроля и верификации КНБК при спуске в скважину",
        "bottom_hole_survey_extrapolation_protocol": "Методика экстраполяции инклинометрических замеров до забоя",
        "casing_window_milling_flowchart": "Технологическая схема фрезерования окна в обсадной колонне",
        "geosteering_horizontal_navigation": "Геонавигационное сопровождение при проводке горизонтальной секции",
        "bha_oscillator_testing_flowchart": "Регламент наземного тестирования осциллятора КНБК перед спуском",
        "bha_rig_site_acceptance_flowchart": "Технологическая карта приемки элементов КНБК на буровой площадке",
        "bha_lwd_marking_and_tally_flowchart": "Регламент разметки, калибровки и учета элементов LWD (каротажа)",
        "horizontal_hole_cleaning_matrix": "Матрица контроля качества очистки горизонтального ствола от шлама"
    })
    # 2.2. СЛОВАРЬ ПЕРЕВОДА ДЛЯ ПАПКИ 2_TECH_PROCESSES (ЧАСТЬ Б)
    translation_map.update({
        "horizontal_projection_building_flowchart": "Регламент контроля интенсивности набора угла в горизонтальной проекции",
        "liner_deployment_and_cementing_flowchart": "Технологическая карта контроля при спуске и цементировании хвостовика",
        "mwd_lwd_qa_qc_protocol": "Протокол контроля качества (QA/QC) данных телеметрии и каротажа",
        "mwd_surface_testing_and_calibration": "Наземное тестирование, калибровка и программирование пульсатора ТМС",
        "pipe_reactive_twist_calculation": "Методика расчета реактивного момента кручения бурильной колонны",
        "rotary_drilling_stabilization_flowchart": "Стабилизация параметров КНБК при роторном способе бурения",
        "sidetrack_initiation_protocol": "Протокол инициализации и контроля начального зарезного трека БС"
    })
    # 2.3. СЛОВАРЬ ПЕРЕВОДА ДЛЯ ПАПКИ 2_TECH_PROCESSES (ЧАСТЬ В)
    translation_map.update({
        "sliding_drilling_directional_control": "Регламент направленного управления траекторией при слайдировании",
        "survey_taking_on_connection": "Технологическая карта снятия инклинометрического замера на наращивании",
        "trajectory_correction_calculation_matrix": "Матрица расчета и выдачи инженерных корректировок траектории",
        "vertical_section_building_flowchart": "Регламент контроля интенсивности набора угла в вертикальной проекции",
        "wellbore_conditioning_before_casing": "Техкарта проработки и шаблонирования ствола перед спуском обсадной колонны",
        "whipstock_toolface_setting_flowchart": "Технологическая карта ориентирования и установки клина-отклонителя"
    })
    # 3.1а. СЛОВАРЬ ПЕРЕВОДА ДЛЯ ПАПКИ 3_INCIDENTS (ЧАСТЬ А)
    translation_map.update({
        "axial_vibration": "Блок-схема контроля осевой вибрации КНБК",
        "balling_up_sticking": "Регламент ликвидации сальникообразования и затяжек",
        "casing_shoe_drilling": "Технологическая карта разбуривания башмака обсадной колонны",
        "cement_plug_spinning": "Регламент ликвидации прокручивания цементного моста",
        "differential_sticking": "Инструкция по ликвидации дифференциального прихвата колонны"
    })
    # 3.1б. СЛОВАРЬ ПЕРЕВОДА ДЛЯ ПАПКИ 3_INCIDENTS (ЧАСТЬ Б)
    translation_map.update({
        "drilling_fluid_prevention_flowchart": "Регламент предотвращения поглощений бурового раствора",
        "fluid_pill_placement_flowchart": "Технологическая карта установки технологической пачки в интервал прихвата",
        "jar-operation-matrix": "Матрица-навигатор активации и работы с буровым яссом при прихвате",
        "landing_losses_spg": "Инструкция по ликвидации поглощений при посадках инструмента",
        "pulling_overpull_spg": "Регламент действий при возникновении затяжек при подъеме КНБК",
        "radial_vibration": "Блок-схема контроля радиальной вибрации бурильной колонны",
        "torsional_vibration": "Блок-схема контроля крутильной вибрации (Stick-Slip) инструмента",
        "wellbore_normalization_flowchart": "Регламент нормализации и очистки ствола скважины от шлама",
        "zbs_window_passing": "Регламент безопасного прохождения интервала окна ЗБС без затяжек"
    })
    # 3.2а. ЗАПУСК ОБХОДА ДИРЕКТОРИЙ РЕПОЗИТОРИЯ
    for folder, cat_name in categories.items():
        folder_path = os.path.join(base_dir, folder)
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(".png"):
                    file_key = file.replace(".png", "").lower()
                    card_name = translation_map.get(file_key, file_key.replace("_", " ").capitalize())
                    img_relative_path = f"repository/{folder}/{file}"
                    v_route = [
                        {"step": f"Аудит и сверка геометрии по схеме {card_name}", "role": "Инженер ННБ"},
                        {"step": "Верификация калибров и датчиков перед началом работ", "role": "Инженер MWD"},
                        {"step": "Контроль параметров и подписание акта ликвидации", "role": "Супервайзер"}
                    ]
                    
                    tech_cards[card_name] = {
                        "title": card_name,
                        "inti_standard": f"СТО ИНТИ S.QS.7 / S.QS.8 ({cat_name})",
                        "description": f"Автоматизированный регламент верификации параметров на устье скважины по технологической схеме: {card_name}.",
                        "verification_route": v_route,
                        "restrictions": {"Роснефть": f"Действия по регламенту Роснефти: {file}", "Газпром нефть": "Контроль параметров по ЛНД Газпром нефти", "ЛУКОЙЛ": "Согласовать операцию с супервайзером ЛУКОЙЛ", "Прочие": "Действия по плану работ"},
                        "recommendations": ["Перед началом работ открыть схему на экране", "Проверить связь с Оперативным центром"],
                        "diagrams": {"Роснефть": img_relative_path, "Газпром нефть": img_relative_path, "ЛУКОЙЛ": img_relative_path, "Прочие": img_relative_path}
                    }
    # Закрытие циклов сканирования и возврат собранной базы данных
    
    return tech_cards

# === АКТИВАЦИЯ АВТОМАТИЧЕСКОГО СКАНЕРА И ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ===
tech_data = load_tech_cards_database()
incident_list = list(tech_data.keys()) if tech_data else []

default_index = 0
if "auto_incident" in st.session_state and st.session_state["auto_incident"] in incident_list:
    default_index = incident_list.index(st.session_state["auto_incident"])
    st.info(f"🔄 Выполнен автоматический переход из Матрицы ЛНД по инциденту: **{st.session_state['auto_incident']}**")
    del st.session_state["auto_incident"]

st.subheader("🎯 Поиск и выбор технологической карты инцидента")
search_query = st.text_input(
    "🔍 Введите ключевое слово для быстрого поиска (например: ясс, прихват, mwd, окно):",
    value="",
    placeholder="Начните вводить название операции или осложнения...",
    key="tech_cards_search_input"
).strip().lower()

if search_query:
    filtered_incident_list = [card for card in incident_list if search_query in card.lower()]
    if not filtered_incident_list:
        st.warning(f"🔕 По запросу '{search_query}' ничего не найдено. Показан полный архив карт.")
        filtered_incident_list = incident_list
else:
    filtered_incident_list = incident_list

final_index = 0 if search_query else min(default_index, max(0, len(filtered_incident_list) - 1))

selected_incident = st.selectbox(
    "Выберите тип брака или инцидента для ликвидации:",
    filtered_incident_list,
    index=final_index,
    key="incident_selector"
)

# Вытаскиваем все данные по выбранной техкарте из базы данных
current_card = tech_data.get(selected_incident, {})
st.markdown("---")

# Вывод основного описания инцидента и стандартов СТО ИНТИ
title_text = current_card.get("title", selected_incident)
inti_text = current_card.get("inti_standard", "СТО ИНТИ S.QS.7")
desc_text = current_card.get("description", "")

st.markdown(f"### 📋 {title_text}")
st.markdown(f"**Соответствие стандартам:** `{inti_text}`")
st.write(desc_text)
st.markdown("---")
st.markdown("### 🧮 Трибологический и тригонометрический контроль (Модуль 2)")
st.caption("Для проведения предиктивного расчета целевых параметров натяжения и крутящих моментов перейдите в Модуль 2")

# Интеграция навигационного барьера верификации СТО ИНТИ
with st.container(border=True):
    st.warning("⚠ ВНИМАНИЕ ИТР: Любое изменение типа резьбовой смазки (СТО ИНТИ S.QS.7) или фактического угла натяжения каната ключа УМК требует обязательного пересчета уставок.")
    
    # Бесшовная ссылка перехода на вашу страницу Модуля 2
    st.page_link(
        "pages/2_raschet_umk.py", 
        label="🔧 ПЕРЕЙТИ В МОДУЛЬ 2: КОНТРОЛЬ МОМЕНТА СВИНЧИВАНИЯ УМК", 
        icon="📊", 
        use_container_width=True
    )

st.markdown("---")
st.markdown("### 🗺 Маршрут операционной верификации параметров (СТО ИНТИ S.QS.8)")
st.caption("Пошаговый контроль технологических звеньев на устье скважины при ликвидации брака")

# Извлекаем шаги верификации текущего инцидента из словаря базы данных
route_steps = current_card.get("verification_route", [])
verified_route_data = []

# Проверяем корректность структуры данных перед запуском цикла
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
        # Вывод предупреждения в случае фиксации технологического нарушения
        if step_status == "Сбой (Выявлено отклонение от ЛНД)":
            st.error(f"🚨 Внимание: Зафиксировано нарушение регламента на этапе контроля: '{step_role}'!")
        st.markdown("---")

        # Сохраняем агрегированные данные шага для последующей генерации рапорта
        verified_route_data.append({
            "step_num": i + 1,
            "title": step_title,
            "role": step_role,
            "status": step_status,
            "comment": fact_comment if fact_comment else "Без комментариев"
        })
else:
    st.info("ℹ Для выбранного инцидента маршрут верификации в базе данных не задан.")
# ==============================================================================
# БЛОК 4: СИНХРОНИЗАЦИЯ ЗАКАЗЧИКОВ И ПРЕВЕНТИВНЫЕ РЕКОМЕНДАЦИИ (СВЯЗЬ С МОДУЛЕМ 4)
# ==============================================================================
st.markdown("### 💼 Ограничения Заказчиков и превентивные рекомендации")

# Подтягиваем ограничения и настраиваем выборку клиентов (полный код доступен в)
card_restrictions = current_card.get("restrictions", {})
available_card_clients = st.session_state.get("global_available_clients") or ["Роснефть", "Газпром нефть", "ЛУКОЙЛ", "Прочие"]

selected_client = st.selectbox(
    "💼 Выберите компанию Заказчика для адаптации техкарты под ЛНД:",
    available_card_clients,
    index=0,
    key="client_selector_tech"
)

st.markdown("---")

# Интеллектуальный адаптер для новых заказчиков (ООО СПД и др.)
def get_internal_client_key(client_name):
    name_upper = str(client_name).upper()
    if "СПД" in name_upper or "САЛЫМ" in name_upper:
        return "Газпром нефть"
    elif "РОСНЕФТЬ" in name_upper or "РН" in name_upper:
        return "Роснефть"
    elif "ЛУКОЙЛ" in name_upper or "ЛК" in name_upper:
        return "ЛУКОЙЛ"
    else:
        return "Прочие"

internal_key = get_internal_client_key(selected_client)

if card_restrictions and isinstance(card_restrictions, dict):
    client_res = card_restrictions.get(internal_key, card_restrictions.get("Прочие", "Выполнять работы согласно утвержденному плану бурения."))
    if selected_client == "ООО СПД":
        client_res = "⚠️ Ограничение СПД-ННБ-2026: Обязательный контроль Dogleg Severity каждые 10 метров при зарезке бокового ствола."
    st.warning(f"⚠ **Специфическое ограничение компании {selected_client}:** {client_res}")
else:
    st.info(f"ℹ Для выбранной техкарты специфических ограничений не зафиксировано.")

# Вывод рекомендаций и графических блок-схем (подробности реализации в)
recommendations = current_card.get("recommendations", [])
if recommendations and isinstance(recommendations, list):
    st.markdown("#### 💡 Рекомендации по предотвращению повторения брака:")
    for rec in recommendations:
        st.info(f"• {rec}")

card_diagrams = current_card.get("diagrams", {})
if card_diagrams and isinstance(card_diagrams, dict):
    img_path = card_diagrams.get(internal_key)
    if img_path and os.path.exists(img_path):
        st.markdown(f"#### 🗺 Технологическая схема регламента под требования: {selected_client}")
        st.image(img_path, caption=f"Регламентный слайд компании {selected_client}", use_container_width=True)

# Интерактивная кнопка формирования рапорта верификации инцидента с базовыми метаданными (полный код формирования массива строк доступен в исходных материалах)
if st.button("📝 Сформировать Рапорт ликвидации технологического брака"):
    lines = []
    lines.append("РАПОРТ ЛИКВИДАЦИИ ТЕХНОЛОГИЧЕСКОГО БРАКА")
    lines.append(f"Месторождение: {st.session_state.get('field_name', 'Приобское')}")
    lines.append(f"Скважина / Куст: {st.session_state.get('well_number', 'Скв. № 101')}")
    lines.append(f"Инженер по ННБ: {st.session_state.get('engineer_name', 'Иванов И.И.')}")
    lines.append(f"Тип инцидента: {title_text}")
    lines.append(f"Нормативная база: {inti_text}")
    lines.append("----------------------------------------")
    for step in verified_route_data:
        lines.append(f"Шаг {step['step_num']}: {step['title']}")
        lines.append(f" Зона ответственности: {step['role']}")
        lines.append(f" Технологический статус: {step['status']}")
        lines.append(f" Примечание инженера: {step['comment']}")
        lines.append("")
    lines.append("========================================")
    lines.append("Подписи сторон на устье скважины:")
    lines.append("Инженер по ННБ: _______________________")
    lines.append("Супервайзер Заказчика: _______________________")
    report_content = "\n".join(lines)
    st.success("✅ Официальный Рапорт верификации успешно сформирован!")
    st.download_button(
        label="📥 Скачать Рапорт ликвидации инцидента (TXT)",
        data=report_content,
        file_name=f"Incident_Report_{st.session_state.get('well_number', '101').replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True
    )
