# generate_db.py
import numpy as np
import pandas as pd
import os

def build_drilling_failures_database(filename="failures_db.xlsx", num_records=3000):
    """
    Генератор синтетической базы данных исторических отказов силовой секции ВЗД
    на основе физико-математических моделей износа эластомеров ИРП-1226.
    """
    np.random.seed(42)  # Фиксация случайности для стабильности генерации
    
    # 1. Списки ключевых параметров
    regions = ["ХМАО / Мегион", "ЯНАО / Новый Уренгой", "Западная Сибирь", "Волго-Урал"]
    manufacturers = ["Радиус-Сервис", "ВНИИБТ-Буровой инструмент", "Гидробурмаш", "Дрилл-Технолоджи"]
    
    # 2. Случайное распределение по регионам и вендорам
    chosen_regions = np.random.choice(regions, num_records)
    chosen_vendors = np.random.choice(manufacturers, num_records)
    
    # 3. Генерируем полевые технологические параметры бурения
    # Содержание песка в растворе (от 0.05% до 1.5%)
    sand_pct = np.random.uniform(0.05, 1.5, num_records)
    # Забойная температура (от 50 до 130 °C)
    temperatures = np.random.uniform(50.0, 130.0, num_records)
    # Заходность винтовой пары (кинематика): преобразуем в числовые коэффициенты
    kinematics_types = np.random.choice(["5/6", "7/8", "9/10"], num_records)
    # Агрессивность бурового раствора (коэффициент от 1.0 до 1.8)
    mud_aggressiveness = np.random.uniform(1.0, 1.8, num_records)
    
    # Списки для записи рассчитанных итоговых результатов
    kin_numbers = []
    wear_speeds = []
    lifetimes_hours = []
    
    # 4. Цикл расчета износа на основе трибологии для каждого исторического рейса
    for i in range(num_records):
        vendor = chosen_vendors[i]
        sand = sand_pct[i]
        temp = temperatures[i]
        agg = mud_aggressiveness[i]
        kin_type = kinematics_types[i]
        
        # Перевод типа кинематики в числовой коэффициент (как в вашем основном коде)
        if kin_type == "5/6":
            kin_num = 0.83
        elif kin_type == "7/8":
            kin_num = 0.87
        else:
            kin_num = 0.90
        kin_numbers.append(kin_num)
        
        # Индивидуальная физика базового износа в зависимости от вендора (особенности резин)
        if vendor == "Радиус-Сервис":
            base_speed = 0.0050  # Базовая скорость деградации статора
            # Средняя чувствительность к абразиву, высокая стойкость к температуре
            k_sand = 1.0 + (sand ** 1.3) * 1.5 if sand > 0.5 else 1.0 + sand * 0.5
            k_temp = 1.0 + np.exp((temp - 95) / 22) * 0.5 if temp > 95 else 1.0
            
        elif vendor == "ВНИИБТ-Буровой инструмент":
            base_speed = 0.0055
            # Отличная износостойкая резина против песка, но боится температур выше 90°C
            k_sand = 1.0 + (sand ** 1.5) * 0.9 if sand > 0.5 else 1.0 + sand * 0.3
            k_temp = 1.0 + np.exp((temp - 90) / 14) * 0.8 if temp > 90 else 1.0
            
        elif vendor == "Гидробурмаш":
            base_speed = 0.0060
            # Чувствителен и к температуре, и к абразивному смыву
            k_sand = 1.0 + (sand ** 1.2) * 1.8 if sand > 0.5 else 1.0 + sand * 0.8
            k_temp = 1.0 + np.exp((temp - 85) / 16) * 0.7 if temp > 85 else 1.0
            
        else:  # Дрилл-Технолоджи
            base_speed = 0.0048
            # Спецсерия: повышенная стойкость к химической агрессии пачек растворов и песку
            k_sand = 1.0 + (sand ** 1.4) * 1.1 if sand > 0.5 else 1.0 + sand * 0.4
            k_temp = 1.0 + np.exp((temp - 100) / 25) * 0.4 if temp > 100 else 1.0
            
        # Интегральное уравнение скорости износа эластомера статора
        total_wear_speed = base_speed * k_sand * k_temp * (kin_num * 1.15) * agg
        
        # Добавляем случайный полевой шум технологического процесса бурения (+/- 4%)
        noise = np.random.normal(1.0, 0.04)
        final_wear_speed = max(0.0001, total_wear_speed * noise)
        wear_speeds.append(final_wear_speed)
        
        # Фактическая наработка до отказа (полного разрушения силовой части) в часах
        # Ограничиваем сверху конструктивным пределом силовой секции в 200 часов
        lifetime = min(200.0, 1.0 / final_wear_speed)
        lifetimes_hours.append(round(lifetime, 1))

    # 5. Сборка финального DataFrame под структуру вашего приложения
    df_output = pd.DataFrame({
        "Регион работ": chosen_regions,
        "Производитель_чистый": chosen_vendors,
        "ВЗД": [f"ВЗД-{v}-{k}" for v, k in zip(chosen_vendors, kinematics_types)],
        "Песок (%)": np.round(sand_pct, 2),
        "Забойная Темп. (°C)": np.round(temperatures, 1),
        "Кинематика_число": kin_numbers,
        "Агрессивность_БР": np.round(mud_aggressiveness, 2),
        "Наработка до отказа (Часы)": lifetimes_hours,
        "Скорость_износа": wear_speeds
    })
    
    # Сохраняем в Excel файл
    df_output.to_excel(filename, index=False)
    print(f"🎯 Успех! База данных '{filename}' успешно сформирована. Создано {num_records} записей.")

if __name__ == "__main__":
    build_drilling_failures_database()
