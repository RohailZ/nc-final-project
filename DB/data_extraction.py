from datetime import datetime
import pyarrow.parquet as pq
import boto3
from io import BytesIO
import pandas as pd
import pyarrow as pa
from pg8000.native import Connection
import os
from dotenv import load_dotenv
load_dotenv()

def connect_db():
    user=os.environ['USER']
    pswd=os.environ['PASSWORD']
    db=os.environ['DATABASE']
    port=os.environ['PORT']
    host=os.environ['HOST']

    conn = Connection(user=user, password=pswd, database=db, host=host, port=port)
    return conn

def close_db(conn):
    conn.close()

def store_secret(table_name,last_updated):
     secrets_manager_client = boto3.client('secretsmanager')
     response = secrets_manager_client.create_secret(
            Name=table_name,  
            SecretString=str(last_updated),  
        )

def format_to_parquet(data, conn, table_name):
    columns = [col["name"] for col in conn.columns]
    df = pd.DataFrame(data, columns=columns)
    last_updated = df['last_updated'].max()
    table = pa.Table.from_pandas(df)
    return table

def write_table_to_parquet_buffer(pyarrow_table):
    parquet_buffer = BytesIO()
    pq.write_table(pyarrow_table, parquet_buffer)
    parquet_buffer.seek(0)
    return parquet_buffer



def data_extract():
    conn = connect_db()
    s3_client = boto3.client('s3')
    secret_manager_client = boto3.client('secretsmanager')

    
    table_names = conn.run("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name NOT LIKE '%prisma%';")
    
    for table in table_names:
        
        response = secret_manager_client.get_secret_value(SecretId=table[0])
        last_updated = response['SecretString']
        
       
        last_updated_obj = datetime.strptime(last_updated, '%Y-%m-%d %H:%M:%S.%f')
        
        
        last_updated_str = last_updated_obj.strftime('%Y-%m-%d %H:%M:%S.%f')

        
        query = f"SELECT * FROM {table[0]} WHERE last_updated > '{last_updated_str}';"

        
        data = conn.run(query)
        print(f"New Data: {data}")

        if data:
            formatted_data = format_to_parquet(data, conn, table[0])
            parquet_buffer = write_table_to_parquet_buffer(formatted_data)
            
        
            s3_client.put_object(Bucket='hamza-test-bucket', Key=f'data/{table[0]}.parquet', Body=parquet_buffer)
    
    close_db(conn)


data_extract()
