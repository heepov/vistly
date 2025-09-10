#!/bin/bash

# Скрипт для развертывания Vistly Bot в Docker

echo "🚀 Развертывание Vistly Bot..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Скопируйте env.example в .env и заполните необходимые переменные:"
    echo "   cp env.example .env"
    echo "   nano .env"
    exit 1
fi

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose down

# Собираем образ
echo "🔨 Собираем Docker образ..."
docker-compose build --no-cache

# Запускаем сервисы
echo "▶️  Запускаем сервисы..."
docker-compose up -d

# Проверяем статус
echo "📊 Статус сервисов:"
docker-compose ps

echo "✅ Развертывание завершено!"
echo "📋 Для просмотра логов используйте: docker-compose logs -f bot"
echo "🛑 Для остановки: docker-compose down"
 