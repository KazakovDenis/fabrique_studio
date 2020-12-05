# API бекенда для сервиса опросов
[Техническое задание](https://github.com/KazakovDenis/fabrique_studio/blob/main/task.txt)  

## Использованный технологический стек
* Django 2.2.10
* Django REST framework 3.12.2
* Docker

## Запуск сервиса
* Для запуска в docker-контейнере необходимо:  
  
    1). добавить следующие данные в переменные окружения:  
    ```
    export SURVEY_SECRET_KEY="ваш_секретный_ключ"
    ```
    2). запустить сервис  
    ```
    docker-compose up --build
    ```
    3). создать администратора  
    ```
    docker-compose run surveys python3 manage.py createsuperuser
    ```
    4). проверить работу сервиса: http://localhost:8000/
  
## Документация
* [Руководство по использованию данного API](https://github.com/KazakovDenis/fabrique_studio/blob/main/survey_service/api/v1/docs/docs.md)  
* OpenAPI-спецификация доступна по URL:  */api/v1/doc*  

## Схема базы данных  
![Схема БД](https://github.com/KazakovDenis/fabrique_studio/blob/main/scheme.png)  
