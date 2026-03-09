
# Этапы сборки для меньшего размера образа
FROM python:3.9-slim as builder

WORKDIR /app

# Устанавливаем системные зависимости если нужны
# RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.9-slim

WORKDIR /app

# Копируем установленные пакеты из builder
COPY --from=builder /root/.local /root/.local

# Копируем код приложения
COPY . .

# Добавляем локальные пользовательские бинарники в PATH
ENV PATH=/root/.local/bin:$PATH

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Хелсчек для Render
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Запускаем бота
CMD ["python", "main.py"]
