# ИСПОЛЬЗУЕМ СТАБИЛЬНЫЙ И ЛЕГКОВЕСНЫЙ ОБРАЗ PYTHON
FROM python:3.11-slim

# УСТАНОВКА СИСТЕМНЫХ ЗАВИСИМОСТЕЙ
# Они необходимы для сборки некоторых библиотек Python (например, для работы с базой данных)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# СОЗДАЕМ РАБОЧУЮ ДИРЕКТОРИЮ ВНУТРИ КОНТЕЙНЕРА
WORKDIR /app

# КОПИРУЕМ И УСТАНАВЛИВАЕМ ЗАВИСИМОСТИ PYTHON
# Docker сначала установит библиотеки из вашего requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# КОПИРУЕМ ВСЕ ОСТАЛЬНЫЕ ИСХОДНЫЕ ФАЙЛЫ ПРОЕКТА ИЗ ГИТХАБА
COPY . .

# СОЗДАЕМ БЕЗОПАСНОГО ПОЛЬЗОВАТЕЛЯ
# Запуск приложений от имени суперпользователя (root) в корпоративной среде запрещен
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# ОТКРЫВАЕМ ВНУТРЕННИЙ ПОРТ STREAMLIT
EXPOSE 8501

# НАСТРОЙКА ПРОВЕРКИ ЗДОРОВЬЯ КОНТЕЙНЕРА (HEALTHCHECK)
# Система будет автоматически проверять, что Streamlit работает и не завис
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# КОМАНДА ЗАПУСКА ПРИЛОЖЕНИЯ
# Отключаем сбор избыточной статистики и телеметрии (gatherUsageStats=false)
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]
