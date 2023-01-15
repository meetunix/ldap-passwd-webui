FROM python:3.11-bullseye
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD [ "waitress-serve", "--listen=*:8080", "app:application" ]
