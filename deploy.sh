#!/bin/bash

# Скрипт развертывания для VPS Beget

echo "🚀 Начинаем развертывание бота..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и Docker Compose."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose."
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Скопируйте .env.example в .env и заполните переменные."
    exit 1
fi

# Остановка и удаление старых контейнеров
echo "🛑 Останавливаем старые контейнеры..."
docker-compose down

# Сборка и запуск контейнеров
echo "🏗️ Сборка и запуск контейнеров..."
docker-compose up -d --build

# Ожидание запуска базы данных
echo "⏳ Ожидание запуска PostgreSQL..."
sleep 10

# Создание таблиц в БД
echo "📊 Создание таблиц в базе данных..."
docker-compose exec bot python database/migrations.py

echo "✅ Развертывание завершено!"
echo "🤖 Бот запущен и готов к работе."
echo ""
echo "Для просмотра логов используйте: docker-compose logs -f bot"
echo "Для остановки: docker-compose down"
echo "Для перезапуска: docker-compose restart"