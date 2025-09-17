FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UVICORN_ACCESS_LOG=0

# Устанавливаем nginx и supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx supervisor \
    && rm -rf /var/lib/apt/lists/*

# Непривилегированный пользователь
RUN adduser --disabled-password --gecos "" appuser

# venv
RUN python -m venv /venv
ENV PATH="/venv/bin:${PATH}"

WORKDIR /app

# Устанавливаем зависимости; перекодируйте requirements.txt в UTF-8!
COPY be/requirements.txt /app/be/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r /app/be/requirements.txt

# Бэкенд
COPY be /app/be

# Фронтенд-статика → стандартный путь nginx
COPY fe /usr/share/nginx/html

# Конфиги
RUN rm -f /etc/nginx/conf.d/* /etc/nginx/sites-enabled/* /etc/nginx/sites-available/* || true
COPY deploy/nginx/app.conf /etc/nginx/conf.d/00-app.conf
COPY deploy/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN chown -R www-data:www-data /usr/share/nginx/html

EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
