# REST API для сервиса по доставке сладостей Candy_delivery

Для установки:
1. Склонируйте репозиторий и зайдите в директорию
```
git clone https://github.com/r-egorov/candy_delivery && cd candy_delivery
```

2. Создайте виртуальное окружение
```
python3 -m venv venv
```

4. Активируйте окружение
```
source venv/bin/activate
```

5. Установите все зависимости
```
pip install -r requirements.txt
```

6. Запустите сервер
```
uwsgi --socket 0.0.0.0:8000 --protocol=http -w wsgi:app
```
