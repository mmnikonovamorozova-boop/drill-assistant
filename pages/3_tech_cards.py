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
    
    # Справочник красивых имен для папок
    categories = {
        "1_methods": "Методики и навигация",
        "2_tech_processes": "Технологические процессы",
        "3_incidents": "Ликвидация осложнений"
    }
    
    # Если папки вообще нет — создаем базовую заглушку
    if not os.path.exists(base_dir):
        return {"Пример техкарты (База пуста)": {"title": "Пример техкарты", "inti_standard": "СТО ИНТИ S.QS.7"}}
        
    # Сканируем подпапки репозитория
    for folder, cat_name in categories.items():
        folder_path = os.path.join(base_dir, folder)
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(".png"):
                    # Убираем расширение и нижние подчеркивания для красивого имени
                    card_name = file.replace(".png", "").replace("_", " ").capitalize()
                    img_relative_path = f"repository/{folder}/{file}"
                    
                    tech_cards[card_name] = {
                        "title": card_name,
                        "inti_standard": f"СТО ИНТИ S.QS.7 / S.QS.8 ({cat_name})",
                        "description": f"Автоматизированный регламент верификации параметров на устье скважины по технологической схеме: {card_name}.",
                        "verification_route": [
                            {"step": f"Визуальный аудит и сверка геометрии по схеме {card_name}", "role": "Инженер ННБ / MWD"},
                            {"step": "Инструментальная верификация калибров и датчиков перед началом работ", "role": "Инженер MWD"},
                            {"step": "Контроль параметров и подписание акта ликвидации отклонения на устье", "role": "Супервайзер / ИТР"}
                        ],
                        "restrictions": {
                            "Роснефть": f"Согласно регламентам Роснефти, действия выполняются строго по схеме {file}.",
                            "Газпром нефть": f"Контроль параметров с записью в суточный рапорт бурения по стандартам Газпром нефти.",
                            "ЛУКОЙЛ": f"Обязательное согласование операции с супервайзером ЛУКОЙЛ на кусту.",
                            "Прочие": "Действия выполняются по согласованию с Заказчиком."
                        },
                        "recommendations": [
                            "Перед началом работ убедиться, что схема открыта на экране и понятна ИТР.",
                            "Проверить исправность средств связи с Оперативным центром."
                        ],
                        "diagrams": {
                            "Роснефть": img_relative_path,
                            "Газпром нефть": img_relative_path,
                            "ЛУКОЙЛ": img_relative_path,
                            "Прочие": img_relative_path
                        }
                    }
    return tech_cards

# ==============================================================================
# БЛОК 3: ВЫБОР ТЕХНОЛОГИЧЕСКОЙ КАРТЫ И ОБРАБОТКА СКВОЗНЫХ ПЕРЕХОДОВ
# ==============================================================================
st.subheader("🎯 Выбор технологической карты инцидента")

# Получаем полный упорядоченный список инцидентов из загруженной базы данных
incident_list = list(tech_data.keys())

# Автоматическая логика: проверяем, пришел ли сквозной запрос из Матрицы ЛНД
default_index = 0
if "auto_incident" in st.session_state and st.session_state["auto_incident"] in incident_list:
    # Находим точный индекс инцидента в массиве для автовыбора в селектбоксе
    default_index = incident_list.index(st.session_state["auto_incident"])
    st.info(f"🔄 Выполнен автоматический переход из Матрицы ЛНД по инциденту: **{st.session_state['auto_incident']}**")
    # Сразу очищаем сессионный триггер, чтобы избежать залипания индекса при перезапуске страницы
    del st.session_state["auto_incident"]
# Интерактивный селектбокс выбора инцидента с динамическим индексом
selected_incident = st.selectbox(
    "Выберите тип брака или инцидента для ликвидации:",
    incident_list,
    index=default_index,
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
# БЛОК 4: СИНХРОНИЗАЦИЯ ЗАКАЗЧИКОВ С МОДУЛЕМ 4 И ПРЕВЕНТИВНЫЕ РЕКОМЕНДАЦИИ
# ==============================================================================
st.markdown("### 💼 Ограничения Заказчиков и превентивные рекомендации")

# Вытягиваем ограничения текущего инцидента из словаря current_card
card_restrictions = current_card.get("restrictions", {})

# Выпадающий перечень динамически берется из глобальной сессии Модуля 4
if "global_available_clients" in st.session_state and st.session_state["global_available_clients"]:
    available_card_clients = st.session_state["global_available_clients"]
else:
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
# Выводим на экран ЛНД-требования недропользователей
if card_restrictions and isinstance(card_restrictions, dict):
    client_res = card_restrictions.get(selected_client, "Специфических ограничений не зафиксировано.")
    st.warning(f"⚠ Ограничение компании {selected_client}: {client_res}")
else:
    st.info("ℹ Специфических ограничений Заказчиков для данного инцидента не найдено.")

# Извлекаем и генерируем список общих превентивных рекомендаций
recommendations = current_card.get("recommendations", [])
if recommendations and isinstance(recommendations, list):
    st.markdown("#### 💡 Рекомендации по предотвращению повторения брака:")
    for rec in recommendations:
        st.info(f"• {rec}")
# --- БЛОК ИНТЕГРАЦИИ ГРАФИЧЕСКИХ БЛОК-СХЕМ ПРОЦЕССОВ ИЗ РЕПОЗИТОРИЯ ---
card_diagrams = current_card.get("diagrams", {})

if card_diagrams and isinstance(card_diagrams, dict):
    # Пытаемся получить путь к файлу блок-схемы для конкретного Заказчика
    img_path = card_diagrams.get(selected_client)
    if img_path:
        st.markdown(f"#### 🗺 Технологическая схема регламента под требования: {selected_client}")
        
        # Проверяем физическое наличие файла схемы в репозитории перед выводом
        if os.path.exists(img_path):
            st.image(
                img_path,
                caption=f"Официальный регламентный слайд / блок-схема ликвидации осложнения компании {selected_client}",
                use_container_width=True
            )
        else:
            st.info(f"ℹ Для просмотра графической схемы загрузите файл `{img_path}` в папку вашего репозитория GitHub.")
            st.caption("При отсутствии файла на сервере система автоматически переключается на текстовый маршрут верификации ИНТИ выше.")
st.markdown("### 📄 Отчетность и фиксация параметров")

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
