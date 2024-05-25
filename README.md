# Веб-приложение FastAPI JSON RPC

Это веб-приложение FastAPI, которое использует формат JSON RPC. Оно использует PostgreSQL для хранения данных и Redis для кэширования.

Приложение включает в себя две таблицы: `customer` и `orders`.

- Поля таблицы `customer`: `id`, `name`, `options` (поле jsonb)
- Поля таблицы `orders`: `id`, `items` (поле jsonb), `customer_id` (внешний ключ, ссылающийся на таблицу `customer`)

## Доступные методы

Приложение предоставляет следующие методы:

- `Customer.create`
- `Customer.list`
- `Customer.get`
- `Order.create`
- `Order.list`
- `Order.get`
- `Order.delete`

## Установка

Установите необходимые зависимости с помощью следующей команды:

```bash
python -m pip install -r requirements.txt
```

## Использование

Чтобы запустить приложение, используйте следующую команду:

```bash
python main.py run
```

Чтобы пересоздать таблицы в базе данных, используйте следующую команду:

```bash
python main.py recreate
```
