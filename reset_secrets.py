from data_extraction import connect_db, reset_secrets, close_db
import boto3


conn = connect_db("psql_creds")
secret_manager_client = boto3.client("secretsmanager")
table_names = conn.run(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name NOT LIKE '%prisma%';"
)
for table in table_names:
    reset_secrets(secret_manager_client, table[0])
close_db(conn)

conn = connect_db("data-warehouse-creds")

tables = [
    "fact_sales_order",
    "dim_date",
    "dim_design",
    "dim_location",
    "dim_counterparty",
    "dim_currency",
    "dim_staff",
]
for table in tables:
    conn.run(f"DELETE FROM {table};")
close_db(conn)
