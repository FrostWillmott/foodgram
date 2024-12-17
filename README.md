# Проект Foodgram

Foodgram — это онлайн-сервис, на котором пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в избранное и в список покупок, а перед походом в магазин скачивать сводный список ингредиентов.

## Технологии
- Python 3.13
- Django 5.1.3
- PostgreSQL
- Gunicorn
- Nginx
- Docker, docker-compose
- GitHub Actions

## Подготовка к запуску в продакшен

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/username/projectname.git
2. Перейдите в директорию проекта:
    ```bash
    cd projectname
   
3. Создайте файл `.env` и добавьте в него переменные окружения:
    ```dotenv
    SECRET_KEY=your_secret_key
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1
    DATABASE_URL=postgres://user:password@localhost:5432/foodgram
      ...
    ```
4. Находясь в папке foodgram, выполните команду:
    ```bash
    docker-compose up
    ```

5. Миграции и создание суперпользователя:
После запуска контейнеров выполните миграции и создайте суперпользователя:
    ```bash
    docker-compose exec backend python manage.py migrate
    docker-compose exec backend python manage.py createsuperuser
    ```

6. Загрузка данных в базу:
    ```bash
    docker-compose exec backend python manage.py load_ingredients path/to/ingredients.json
    ```

### Лицензия
Этот проект лицензирован под лицензией MIT.
