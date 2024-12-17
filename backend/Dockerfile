FROM python:3.13

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput

CMD gunicorn projectname.wsgi:application --bind 0.0.0.0:8000
