from sqlalchemy import Column, Integer, ForeignKey, String, MetaData, Table
from sqlalchemy.dialects.postgresql import JSONB

from config import NAME_MAX_LENGTH

meta = MetaData()

customer_table = Table(
    "customer", meta,
    Column("id", Integer, primary_key=True),
    Column("name", String(NAME_MAX_LENGTH)),
    Column("options", JSONB)
)

orders_table = Table(
    "orders", meta,
    Column("id", Integer, primary_key=True),
    Column("items", JSONB),
    Column("customer_id", Integer, ForeignKey("customer.id"))
)
