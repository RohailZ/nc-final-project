import json
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from moto import mock_aws
import boto3
import awswrangler as wr
import logging
from botocore.exceptions import ClientError
from data_loading import create_engine_conn, get_object_path, load_data, lambda_handler, PROCESSED_BUCKET
import time
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@mock_aws
@patch("data_loading.boto3.client")
def test_create_engine_conn(mock_boto_client):
    mock_secrets_manager = mock_boto_client.return_value
    mock_secrets_manager.get_secret_value.return_value = {
        "SecretString": json.dumps({
            "username": "test_user",
            "password": "test_password",
            "dbname": "test_db",
            "port": 5432,
            "host": "test_host"
        })
    }
    conn_string = create_engine_conn("test-secret", mock_secrets_manager)

    expected = "postgresql://test_user:test_password@test_host:5432/test_db"
    assert conn_string == expected

def test_create_engine_conn_error():
    mock_secrets_manager = MagicMock()
    mock_secrets_manager.get_secret_value.side_effect = ClientError(
        {"Error": {"Code": "NoSuchEntity", "Message": "Secret not found"}}, "GetSecretValue"
    )
    conn_string = create_engine_conn("data-warehouse-creds", mock_secrets_manager)
    assert conn_string is None

def test_get_object_path():
    mock_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": "my-bucket"
                    },
                    "object": {
                        "key": "1/2/3.parquet"
                    }
                }
            }
        ]
    }
    bucket_name, object_key = get_object_path(mock_event["Records"])

    assert bucket_name == "my-bucket"
    assert object_key == "1/2/3.parquet"

@mock_aws
@patch("data_loading.wr.s3.read_parquet")
@patch("data_loading.pd.DataFrame.to_sql")
def test_load_data_error_handling(mock_to_sql, mock_read_parquet):
    mock_conn = MagicMock()
    mock_read_parquet.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}}, "GetObject"
    )
    load_data("non_existent_file", mock_conn)
    mock_read_parquet.assert_called_once_with(f"s3://{PROCESSED_BUCKET}/non_existent_file/*", dataset=True)
    mock_to_sql.assert_not_called()


@mock_aws
@patch("data_loading.wr.s3.read_parquet")
@patch("data_loading.pd.DataFrame.to_sql")
def test_load_data_address(mock_to_sql, mock_read_parquet):
    mock_conn = MagicMock()
    mock_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": "test-bucket"
                    },
                    "object": {
                        "key": "address.parquet"
                    }
                }
            }
        ]
    }

    mock_read_parquet.return_value = pd.DataFrame({
        "address_id": [101, 102],
        "city": ["City A", "City B"]
    })

    load_data("address", mock_conn)

    mock_read_parquet.assert_called_once_with(f"s3://{PROCESSED_BUCKET}/address/*", dataset=True)
    

    mock_to_sql.assert_called_once_with(
        "dim_location", con=mock_conn, if_exists="append", index=False
    )


@pytest.fixture
def mock_db_conn():
    """Fixture to mock database connection"""
    mock_conn = MagicMock()
    mock_conn.return_value = mock_conn
    return mock_conn

@patch("data_loading.wr.s3.read_parquet")
@patch("data_loading.pd.DataFrame.to_sql")
@patch("time.sleep")  
def test_load_data_sales_order(mock_sleep, mock_to_sql, mock_read_parquet):
    mock_read_parquet.return_value = pd.DataFrame({
        "staff_id": [1, 2],
        "updated_date": ["2021-01-01", "2021-01-02"],
        "updated_time": ["12:00:00", "13:00:00"],
        "address_id": [101, 102],
        "city": ["City A", "City B"]
    })
    mock_conn = MagicMock()


    load_data("sales_order", mock_conn)

    mock_read_parquet.assert_called_once_with(f"s3://{PROCESSED_BUCKET}/sales_order/*", dataset=True)

    mock_to_sql.assert_called_once_with(
        "fact_sales_order", con=mock_conn, if_exists="append", index=False
    )
    mock_sleep.assert_called_once_with(100)


@patch("boto3.client")
@patch("data_loading.create_engine")
@patch("data_loading.load_data")
def test_lambda_handler(mock_load_data, mock_create_engine, mock_boto_client):
    mock_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": "test-bucket"
                    },
                    "object": {
                        "key": "data/sales_order.parquet"
                    }
                }
            }
        ]
    }
    
    mock_secrets_manager = MagicMock()
    mock_boto_client.return_value = mock_secrets_manager
    mock_secrets_manager.get_secret_value.return_value = {
        "SecretString": json.dumps({
            "username": "test_user",
            "password": "test_password",
            "dbname": "test_db",
            "port": 5432,
            "host": "test_host"
        })
    }

    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_engine.connect.return_value = MagicMock()
    
    mock_load_data.return_value = None
    
    lambda_handler(mock_event, None)

    mock_secrets_manager.get_secret_value.assert_called_once_with(SecretId="data-warehouse-creds")
    mock_create_engine.assert_called_once_with(
        "postgresql://test_user:test_password@test_host:5432/test_db"
    )
    mock_load_data.assert_called_once_with("sales_order", mock_engine.connect.return_value)

    mock_engine.connect.return_value.close.assert_called_once()
