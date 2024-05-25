import argparse
import asyncio
from contextlib import asynccontextmanager
from json import dumps, loads

import redis.asyncio as redis
import sqlalchemy.exc
import uvicorn
from fastapi import FastAPI, Request, Response
from jsonrpcserver import Result, async_dispatch, InvalidParams, Error, method, Success
from sqlalchemy import select, delete

from config import REDIS_URL, CACHE_TTL, SERVER_HOST, SERVER_PORT
from database import engine, recreate_tables, check_db, create_tables
from models import NAME_MAX_LENGTH
from models import customer_table, orders_table


@asynccontextmanager
async def lifespan(app):
    await check_db()
    await create_tables()
    yield


app = FastAPI(lifespan=lifespan)
cache = redis.from_url(REDIS_URL, decode_responses=True)


@method(name="Customer.create")
async def add_customer(name: str, options: dict) -> Result:
    if not isinstance(name, str) or not name:
        return InvalidParams("Name must be a non-empty string")
    if not isinstance(options, dict) or not options:
        return InvalidParams("Options must be a non-empty dictionary")
    if len(name) > NAME_MAX_LENGTH:
        return InvalidParams("Name must be 50 characters or less")

    async with engine.begin() as conn:
        try:
            result = await conn.execute(
                customer_table.insert().values(name=name, options=options).returning(customer_table)
            )
            customer = result.fetchone()._asdict()
        except sqlalchemy.exc.SQLAlchemyError as e:
            return Error(-32603, "Database error", str(e))

        await cache.set(f"customer:{customer['id']}", dumps(customer), ex=CACHE_TTL)
        await cache.delete("customers")
        return Success("Customer added")


@method(name="Customer.list")
async def list_customers() -> Result:
    cashed_customers = await cache.get("customers")
    if cashed_customers:
        print("Cache hit")
        return Success(loads(cashed_customers))
    async with engine.begin() as conn:
        try:
            result = await conn.execute(select(customer_table))
        except sqlalchemy.exc.SQLAlchemyError as e:
            return Error(-32603, "Database error", str(e))
        customers = [row._asdict() for row in result.fetchall()]
        await cache.set("customers", dumps(customers), ex=CACHE_TTL)
        return Success(customers)


@method(name="Customer.get")
async def get_customer(id: int) -> Result:
    if not isinstance(id, int) or id < 1:
        return InvalidParams("Invalid customer ID")
    cached_customers = await cache.get(f"customer:{id}")
    if cached_customers:
        print("Cache hit")
        return Success(loads(cached_customers))
    async with engine.begin() as conn:
        result = await conn.execute(select(customer_table).where(customer_table.c.id == id))
        customer_data = result.fetchone()
        if customer_data is None:
            return Success(dict())
        customer_data_dict = customer_data._asdict()
        await cache.set(f"customers", dumps(customer_data_dict), ex=CACHE_TTL)
        return Success(customer_data_dict)


@method(name="Order.create")
async def create_order(customer_id: int, items: dict) -> Result:
    if not isinstance(customer_id, int) or customer_id < 1:
        return InvalidParams("Invalid customer ID")
    if not isinstance(items, dict) or not items:
        return InvalidParams("Items must be a non-empty dictionary")
    async with engine.begin() as conn:
        try:
            result = await conn.execute(
                orders_table.insert().values(customer_id=customer_id, items=items).returning(orders_table))
            order = result.fetchone()._asdict()
        except sqlalchemy.exc.IntegrityError:
            return InvalidParams("Customer with that ID does not exist")
        await cache.set(f"order:{order['id']}", dumps(order), ex=CACHE_TTL)
        await cache.delete("orders")
        return Success("Order created")


@method(name="Order.list")
async def list_orders() -> Result:
    cached_orders = await cache.get("orders")
    if cached_orders:
        print("Cache hit")
        return Success(loads(cached_orders))
    async with engine.begin() as conn:
        try:
            result = await conn.execute(select(orders_table))
        except sqlalchemy.exc.SQLAlchemyError as e:
            return Error(-32603, "Database error", str(e))
        orders = [row._asdict() for row in result.fetchall()]
        await cache.set("orders", dumps(orders), ex=CACHE_TTL)
        return Success(orders)


@method(name="Order.get")
async def get_order(id: int) -> Result:
    cached_order = await cache.get(f"order:{id}")
    if cached_order:
        print("Cache hit")
        return Success(loads(cached_order))
    async with engine.begin() as conn:
        result = await conn.execute(select(orders_table).where(orders_table.c.id == id))
        order_data = result.fetchone()
        if order_data is None:
            return Success(dict())
        order_data_dict = order_data._asdict()
        await cache.set(f"order:{id}", dumps(order_data_dict), ex=CACHE_TTL)
        return Success(order_data_dict)


@method(name="Order.delete")
async def delete_order(id: int) -> Result:
    if not isinstance(id, int) or id < 1:
        return InvalidParams("Invalid order ID")
    async with engine.begin() as conn:
        try:
            result = await conn.execute(delete(orders_table).where(orders_table.c.id == id))
        except sqlalchemy.exc.SQLAlchemyError as e:
            return Error(-32603, "Database error", str(e))
        if result.rowcount == 0:
            return InvalidParams("Order not found")
        await cache.delete(f"order:{id}")
        await cache.delete("orders")
        return Success("Order deleted")


@app.post("/")
async def rpc_endpoint(request: Request):
    return Response(await async_dispatch(await request.body()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage your FastAPI application.")
    parser.add_argument('command', type=str, help='The command to execute. "recreate" or "run".')
    args = parser.parse_args()
    if args.command == "recreate":
        asyncio.get_event_loop().run_until_complete(recreate_tables())
        print("Tables recreated")
    elif args.command == "run":
        uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
    else:
        print(f'Unknown command: {args.command}. The available commands are "create" and "run".')
