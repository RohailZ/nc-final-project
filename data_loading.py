import boto3
import awswrangler as wr
import pandas as pd
from datetime import datetime, timedelta
import logging
from botocore.exceptions import ClientError
import json
import os
from awswrangler.exceptions import NoFilesFound
from pg8000.native import Connection
from sqlalchemy import create_engine
import psycopg2
from psycopg2.extras import execute_values
import time

PROCESSED_BUCKET = os.getenv("PROCESSED_BUCKET", "default-processed-bucket")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_engine_conn(secret_name, secrets_manager_client):
    try:
        response = secrets_manager_client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response["SecretString"])
        user = secret_dict["username"]
        pswd = secret_dict["password"]
        db = secret_dict["dbname"]
        port = secret_dict["port"]
        host = secret_dict["host"]
        db_url = f"postgresql://{user}:{pswd}@{host}:{port}/{db}"
        return db_url
    except ClientError as e:
        logger.info(f"Alert: Failed on retrieving secrets: {str(e)}")

def load_data(filename, conn):
    table_name = None  
    try:
        logger.info(f"reading data from {filename}")
        df = wr.s3.read_parquet(f"s3://{PROCESSED_BUCKET}/{filename}/*", dataset=True)
        df.columns = [c.lower() for c in df.columns]
        if filename == "sales_order":
            logger.info("sleeping for 100 seconds")
            time.sleep(100)
            logger.info("i'm back")
            table_name = f"fact_{filename}"
            df = df.rename(
                columns={
                    "staff_id": "sales_staff_id",
                    "updated_date": "last_updated_date",
                    "updated_time": "last_updated_time",
                }
            )
        elif filename == "address":
            table_name = "dim_location"
            df = df.rename(columns={"address_id": "location_id"})
        else:
            table_name = f"dim_{filename}"
        df.to_sql(table_name, con=conn, if_exists="append", index=False)
        logger.info(f"data updated to {table_name}")
        return
    except ClientError as e:
        logger.info(f"Alert: Failed to update {table_name} {str(e)}")
    
def get_object_path(records):
    """Extracts bucket and object references from Records field of event."""
    return records[0]["s3"]["bucket"]["name"], records[0]["s3"]["object"]["key"]

def lambda_handler(event, context):
    """get bucket name and object name from event"""
    try:
        s3_bucket_name, s3_object_name = get_object_path(event["Records"])
        logger.info(f"Bucket is {s3_bucket_name}")
        logger.info(f"Object key is {s3_object_name}")

        filename = s3_object_name.split("/")[1]
        name, format = filename.split(".")
        logger.info(f"loading data to: {name}")
        secrets_manager_client = boto3.client("secretsmanager")
        conn_string = create_engine_conn("data-warehouse-creds", secrets_manager_client)
        db = create_engine(conn_string)
        conn = db.connect()
        load_data(name, conn)
        conn.close()
    except ClientError as e:
        logger.info(f"Alert: Failed to connect {str(e)}")
    

