from data_extraction import (
    store_secret,
    write_table_to_parquet_buffer,
    get_created_date,
    reset_secrets,
    existing_secret,
    format_to_parquet,
    lambda_handler,
    connect_db,
    close_db,
    INGESTION_BUCKET,
)
import pyarrow as pa
from moto import mock_aws
import boto3
import pytest
import os
from io import BytesIO
from unittest.mock import MagicMock, patch
import json
import logging
from datetime import datetime


@pytest.fixture()
def aws_creds():
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_SECURITY_TOKEN"] = "test"
    os.environ["AWS_SESSION_TOKEN"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture()
def sm_client(aws_creds):
    with mock_aws():
        mock_sm = boto3.client("secretsmanager")
        yield mock_sm


@pytest.fixture()
def s3_client(aws_creds):
    with mock_aws():
        mock_s3 = boto3.client("s3")
        yield mock_s3


def test_existing_secrets_false_if_no_secret_exists(sm_client):
    secret_name = "sales_order"
    response = existing_secret(sm_client, secret_name)
    assert response == False


def test_existing_secrets_true_if_secret_exists(sm_client):
    sm_client.create_secret(
        Name="northcoders",
        SecretString="pa55word",
    )

    secret_name = "northcoders"
    response = existing_secret(sm_client, secret_name)
    assert response == True


def test_rest_secrets_restes_values(sm_client):
    sm_client.create_secret(
        Name="northcoders",
        SecretString="pa55word",
    )
    reset_secrets(sm_client, "northcoders")
    response = sm_client.get_secret_value(SecretId="northcoders")
    assert response["SecretString"] == "2020-11-14 09:41:09.839000"


def test_get_creted_date_returns_creted_at_date():
    data = [
        [
            1,
            "2020-11-14 09:41:09.839000",
            "2020-11-14 09:41:09.839000",
            "test",
            "test",
            "test",
        ]
    ]
    columns = [
        "design_id",
        "created_at",
        "last_updated",
        "design_name",
        "file_location",
        "file_name",
    ]
    response = get_created_date(data, columns)
    expected_response = datetime(2020, 11, 14, 9, 41, 9, 839000)
    assert response == expected_response


# def test_format_to_parquet_returns_formated_data():
#     mock_conn = MagicMock()
#     data={"column1": [1, 2, 3], "column2": ["a", "b", "c"]}
#     pyarrow_table = pa.table(data)
#     formated_data=format_to_parquet(data,mock_conn,pyarrow_table)
#     close_db(mock_conn)
#     assert isinstance(formated_data,pa.Table)


def test_write_table_to_parquet_buffer_format():
    data = {"column1": [1, 2, 3], "column2": ["a", "b", "c"]}
    pyarrow_table = pa.table(data)
    response = write_table_to_parquet_buffer(pyarrow_table)
    assert isinstance(response, BytesIO)


def test_store_secrets_new_secret_if_not_exist(sm_client):
    secret_name = "northcoders"
    last_updated = "2020-11-14 09:41:09.839000"
    store_secret(secret_name, last_updated, sm_client)
    response = sm_client.get_secret_value(SecretId="northcoders")
    assert response["SecretString"] == "2020-11-14 09:41:09.839000"


def test_store_secrets_update_secret_if_already_exist(sm_client):
    sm_client.create_secret(
        Name="northcoders",
        SecretString="pa55word",
    )
    secret_name = "northcoders"
    last_updated = "2020-11-14 09:41:09.839000"
    store_secret(secret_name, last_updated, sm_client)
    response = sm_client.get_secret_value(SecretId="northcoders")
    assert response["SecretString"] == "2020-11-14 09:41:09.839000"


@mock_aws
@patch("data_extraction.boto3.client")
def test_connect_db(mock_boto_client):
    mock_secrets_client = MagicMock()
    mock_boto_client.return_value = mock_secrets_client
    mock_secrets_client.get_secret_value.return_value = {
        "SecretString": json.dumps(
            {
                "username": "testuser",
                "password": "testpass",
                "dbname": "testdb",
                "host": "localhost",
                "port": 5432,
            }
        )
    }

    class MockDBConnection:
        def __init__(self, user, password, database, host, port):
            self.user = user
            self.password = password
            self.database = database
            self.host = host
            self.port = port

    with patch("data_extraction.Connection", MockDBConnection):
        conn = connect_db("test_secret")
        assert conn.user == "testuser"
        assert conn.password == "testpass"
        assert conn.database == "testdb"
        assert conn.host == "localhost"
        assert conn.port == 5432


def test_close_db():
    mock_conn = MagicMock()
    close_db(mock_conn)
    mock_conn.close.assert_called_once()


class DummyContext:
    pass


@mock_aws
@patch("data_extraction.connect_db")
def test_lambda_handler_end_to_end(mock_pg_connection, caplog, sm_client, s3_client):

    s3_client.create_bucket(
        Bucket=INGESTION_BUCKET,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    sm_client.create_secret(
        Name="test_table", SecretString="2020-11-14 09:41:09.839000"
    )
    sm_client.get_secret_value = MagicMock(
        return_value={
            "SecretString": json.dumps(
                {
                    "username": "test_user",
                    "password": "test_pass",
                    "dbname": "test_db",
                    "port": "5432",
                    "host": "localhost",
                }
            )
        }
    )

    # Mock database connection
    mock_conn = MagicMock()
    mock_conn.run.side_effect = [
        [["test_table"]],
        [[1, "Test Name", "2023-11-14 09:00:00", "2023-11-14 08:00:00"]],
    ]
    mock_conn.columns = [
        {"name": "id"},
        {"name": "name"},
        {"name": "last_updated"},
        {"name": "created_at"},
    ]
    mock_pg_connection.return_value = mock_conn

    # Run the Lambda handler
    event = {}
    context = DummyContext()
    with caplog.at_level(logging.INFO):
        lambda_handler(event, context)
        print("Captured Logs:\n", caplog.text)
        assert "Putting New Data in s3 bucket" in caplog.text
        assert (
            "Alert: Failed to connect to DB" not in caplog.text
        ), f"Logs: {caplog.text}"