# Проект Foodgram

Foodgram — это онлайн-сервис, на котором пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в избранное и в список покупок, а перед походом в магазин скачивать сводный список ингредиентов.

## Домен проекта:
   kittygram.biz

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
   git clone git@github.com:FrostWillmott/foodgram.git
2. Перейдите в директорию проекта:
    ```bash
    cd foodgram
   
3. Создайте файл `.env` и добавьте в него переменные окружения:
    ```dotenv
       SECRET_KEY=your_secret_key
       DEBUG=True
       ALLOWED_HOSTS=localhost,127.0.0.1
       DATABASE_URL=postgres://user:password@localhost:5432/foodgram
       POSTGRES_DB=DB_Name
       POSTGRES_USER=DB_user
       POSTGRES_PASSWORD=DB_password
       DB_HOST=db
       DB_PORT=1111
       DEBUG=False
       CSRF_TRUSTED_ORIGINS=localhost,127.0.0.1
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

### Примеры запросов/ответов

1. Создание рецепта:

   Запрос:
      ```
      POST /api/recipes/
      ```
   Ответ:
      ```
      {
        "ingredients": [
          {
            "id": 1123,
            "amount": 10
          }
        ],
        "tags": [
          1,
          2
        ],
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
        "name": "string",
        "text": "string",
        "cooking_time": 1
      }
      ```
2. Добавление рецепта в список покупок:

   Запрос:
      ```
      POST /api/recipes/{id}/shopping_cart/
      ```
   Ответ:
      ```
      {
         "id": 0,
         "name": "string",
         "image": "http://foodgram.example.org/media/recipes/images/image.png",
         "cooking_time": 1
      }
      ```
3. Подписаться на пользователя:

      Запрос:
      ```
      POST /api/users/{id}/subscribe/
      ```
   Ответ:
      ```
      {
         "email": "user@example.com",
         "id": 0,
         "username": "string",
         "first_name": "Вася",
         "last_name": "Иванов",
         "is_subscribed": true,
         "recipes": [
             {
                 "id": 0,
                 "name": "string",
                 "image": "http://foodgram.example.org/media/recipes/images/image.png",
                 "cooking_time": 1
             }
         ],
         "recipes_count": 0,
         "avatar": "http://foodgram.example.org/media/users/image.png"
      }
      ```
   

### Авторство
Автор проекта: Иван Ткаченко

### Лицензия
@Этот проект лицензирован под лицензией MIT.
