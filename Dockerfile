FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN echo 'deb http://deb.debian.org/debian stretch main' >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get autoremove -y && \
    apt-get install -y libssl1.0-dev curl git nano wget && \
    rm -rf /var/lib/apt/lists/* && rm -rf /var/lib/apt/lists/partial/*

ADD https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz /
RUN set -ex; wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
RUN set -ex; tar xvf /wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
RUN set -ex; mv wkhtmltox/bin/wkhtmlto* /usr/bin/
RUN set -ex; ln -nfs /usr/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
#RUN python manage.py migrate
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]