Реализовать на FastApi веб-приложение формата Json RPC Реализовать хранение данных через Postgres Кэширование через redis
Две таблицы customer и orders: customer (id, name, options - jsonb поле ) orders (id, items -- jsonb поле, customer_id - foreign key на customer таблицу)
Customer.create , Customer.list , Customer.get
Order.create , Order.list , Order.get, Order.delete
