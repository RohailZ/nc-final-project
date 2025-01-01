from data_transformation import (
    INGESTION_BUCKET,
    PROCESSED_BUCKET,
    lambda_handler,
    design,
    dim_date,
    update_dim_date,
    counterparty,
    currency,
    address,
    staff,
    sales_order,
    NoFilesFound,
)
from moto import mock_aws
from unittest.mock import patch
import pandas as pd
import boto3
import awswrangler as wr
import os
import pytest
from datetime import datetime, date, time
from botocore.exceptions import ClientError
from pyarrow import ArrowInvalid
from freezegun import freeze_time


"""Mock Extracted DataFrames"""
mock_staff = pd.DataFrame(
    {
        "staff_id": [1, 2],
        "first_name": ["will", "bill"],
        "last_name": ["robb", "bobb"],
        "department_id": [63, 36],
        "email_address": ["willrobb63@bmail.com", "billbobb@pmail.com"],
        "created_at": [datetime.now(), datetime.now()],
        "last_updated": [datetime.now(), datetime.now()],
    }
)

mock_design = pd.DataFrame(
    {
        "design_id": [1],
        "design_name": ["abc"],
        "file_location": ["path"],
        "file_name": ["path name"],
        "created_at": [datetime.now()],
        "last_updated": [datetime.now()],
    }
)

mock_address = pd.DataFrame(
    {
        "address_id": [1, 2, 3],
        "address_line_1": ["sesame street", "number 10", "bikini bottom"],
        "address_line_2": ["xxx", "yyy", ""],
        "district": ["nine", "", ""],
        "city": ["muppets city", "London", "the sea"],
        "postal_code": ["12345", "w1 4cd", "456Seaway"],
        "country": ["USA", "UK", "belgium"],
        "phone": ["123456789", "987654321", "123987543"],
        "created_at": [datetime.now(), datetime.now(), datetime.now()],
        "last_updated": [datetime.now(), datetime.now(), datetime.now()],
    }
)

mock_currency = pd.DataFrame(
    {
        "currency_id": [1, 2, 3],
        "currency_code": ["GBP", "USD", "EUR"],
        "created_at": [datetime.now(), datetime.now(), datetime.now()],
        "last_updated": [datetime.now(), datetime.now(), datetime.now()],
    }
)

mock_cp = pd.DataFrame(
    {
        "counterparty_id": [1, 2],
        "counterparty_legal_name": ["AMAZON", "NORTHCODERS"],
        "legal_address_id": [1, 2],
        "commercial_contact": ["boy", "girl"],
        "delivery_contact": ["cat", "dog"],
        "created_at": [datetime.now(), datetime.now()],
        "last_updated": [datetime.now(), datetime.now()],
    }
)

mock_sales_order = pd.DataFrame(
    {
        "sales_order_id": [101, 102],
        "created_at": [datetime.now(), datetime.now()],
        "last_updated": [datetime.now(), datetime.now()],
        "design_id": [1, 3],
        "staff_id": [4, 5],
        "counterparty_id": [1, 5],
        "units_sold": [23, 2],
        "unit_price": [10.00, 5.00],
        "currency_id": [1, 2],
        "agreed_delivery_date": [date(2023, 8, 1), date(2023, 8, 10)],
        "agreed_payment_date": [date(2023, 7, 1), date(2023, 7, 5)],
        "agreed_delivery_location_id": [1, 2],
    }
)

mock_department = pd.DataFrame(
    {
        "department_id": [63, 36],
        "department_name": ["Northcoders", "CodersNorth"],
        "location": ["manchester", "leeds"],
        "manager": ["none", "none"],
        "created_at": [datetime.now(), datetime.now()],
        "last_updated": [datetime.now(), datetime.now()],
    }
)

mock_date = pd.DataFrame(
    {
        "date_id": [datetime(2024, 11, 19)],
        "year": [2024],
        "month": [11],
        "day": [19],
        "day_of_week": [1],
        "day_name": ["Tuesday"],
        "month_name": ["November"],
        "quarter": [4],
    }
)


@pytest.fixture()
def aws_creds():
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_SECURITY_TOKEN"] = "test"
    os.environ["AWS_SESSION_TOKEN"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


"""Mock s3 buckets"""


@pytest.fixture(autouse=True)
def s3_client(aws_creds):
    with mock_aws():
        mock_s3 = boto3.client("s3")
        mock_s3.create_bucket(
            Bucket=INGESTION_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        mock_s3.create_bucket(
            Bucket=PROCESSED_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        yield mock_s3


"""Test staff function for dim_staff"""


def test_staff_merge(s3_client):
    wr.s3.to_parquet(
        df=mock_staff,
        path=f"s3://{INGESTION_BUCKET}/staff/a/a/a/staff 2024-11-20",
        dataset=False,
    )
    wr.s3.to_parquet(
        df=mock_department,
        path=f"s3://{INGESTION_BUCKET}/department/a/a/a/department 2024-11-20",
        dataset=False,
    )
    result = staff("staff", "2024-11-20")
    assert result["department_name"].iloc[0] == "Northcoders"
    assert result["first_name"].notnull().all(), "First name has null values"
    assert (
        result["department_name"].nunique() == 2
    ), "More than one department in the result"


"""Test design function for dim_design"""


def test_design_returns_correct_dim_design_columns(s3_client):
    wr.s3.to_parquet(
        df=mock_design,
        path=f"s3://{INGESTION_BUCKET}/design/a/a/a/design 2024-11-20",
        dataset=False,
    )
    dim_design = design("design", "2024-11-20")
    assert list(dim_design.columns) == [
        "design_id",
        "design_name",
        "file_location",
        "file_name",
    ]


def test_missing_column_raises_error(s3_client):
    missing_design_id_df = pd.DataFrame(
        {"design_name": ["abc"], "file_location": ["location"], "file_name": ["name"]}
    )
    wr.s3.to_parquet(
        df=missing_design_id_df,
        path=f"s3://{INGESTION_BUCKET}/design/a/a/a/design 2024-11-20",
        dataset=False,
    )
    with pytest.raises(KeyError):
        design("design", "2024-11-20")


def test_design_invalid_file_type_raises_error(s3_client):
    wr.s3.to_csv(
        df=mock_design,
        path=f"s3://{INGESTION_BUCKET}/design/a/a/a/design 2024-11-20",
        dataset=False,
    )
    with pytest.raises(ArrowInvalid):
        design("design", "2024-11-20")


"""Test counterparty function for dim_counterparty"""


def test_counterparty_merge(s3_client):
    wr.s3.to_parquet(
        df=mock_address, path=f"s3://{INGESTION_BUCKET}/address/a", dataset=False
    )
    wr.s3.to_parquet(
        df=mock_cp,
        path=f"s3://{INGESTION_BUCKET}/counterparty/a/a/a/counterparty 2024-11-20",
        dataset=False,
    )
    result = counterparty("counterparty", "2024-11-20")
    assert "counterparty_id" in result.columns
    assert "counterparty_legal_name" in result.columns
    assert "counterparty_legal_address_line_1" in result.columns
    assert "counterparty_legal_address_line_2" in result.columns
    assert "counterparty_legal_district" in result.columns
    assert "counterparty_legal_city" in result.columns
    assert "counterparty_legal_postal_code" in result.columns
    assert "counterparty_legal_country" in result.columns
    assert "counterparty_legal_phone_number" in result.columns
    assert result["counterparty_legal_name"].iloc[0] == "AMAZON"
    assert result["counterparty_legal_city"].iloc[1] == "London"


"""Test address function for dim_location"""


def test_location_merge(s3_client):
    wr.s3.to_parquet(
        df=mock_address,
        path=f"s3://{INGESTION_BUCKET}/address/a/a/a/address 2024-11-20",
        dataset=False,
    )
    result = address("address", "2024-11-20")
    assert result["location_id"].iloc[0] == 1
    assert result["city"].iloc[1] == "London"


def test_address_returns_correct_dim_location_columns(s3_client):
    wr.s3.to_parquet(
        df=mock_address,
        path=f"s3://{INGESTION_BUCKET}/address/a/a/a/address 2024-11-20",
        dataset=False,
    )
    dim_location = address("address", "2024-11-20")
    expected_columns = [
        "location_id",
        "address_line_1",
        "address_line_2",
        "district",
        "city",
        "postal_code",
        "country",
        "phone",
    ]
    assert list(dim_location.columns) == expected_columns


"""Test currency function for dim_currency"""


def test_currency_returns_correct_dim_currency_columns(s3_client):
    expected_columns = ["currency_id", "currency_code", "currency_name"]
    wr.s3.to_parquet(
        df=mock_currency,
        path=f"s3://{INGESTION_BUCKET}/currency/a/a/a/currency 2024-11-20",
        dataset=False,
    )
    dim_currency = currency("currency", "2024-11-20")
    assert list(dim_currency.columns) == expected_columns


def test_currency_mapping(s3_client):
    wr.s3.to_parquet(
        df=mock_currency,
        path=f"s3://{INGESTION_BUCKET}/currency/a/a/a/currency 2024-11-20",
        dataset=False,
    )
    dim_currency = currency("currency", "2024-11-20")
    assert "currency_name" in dim_currency.columns
    assert dim_currency["currency_name"].iloc[0] == "Great British Pound"
    assert dim_currency["currency_name"].iloc[1] == "United States Dollar"
    assert dim_currency["currency_name"].iloc[2] == "Euro"


"""Test date functions for dim_date"""


def test_update_dim_date_returns_correct_columns():
    mocked_date = datetime(2024, 11, 20)
    dim_date_df = update_dim_date(mocked_date)
    assert "date_id" in dim_date_df.columns
    assert "year" in dim_date_df.columns
    assert "month" in dim_date_df.columns
    assert "day" in dim_date_df.columns
    assert "day_of_week" in dim_date_df.columns
    assert "day_name" in dim_date_df.columns
    assert "month_name" in dim_date_df.columns
    assert "quarter" in dim_date_df.columns


@freeze_time("2024-10-20")
def test_dim_date_with_existing_data(s3_client):
    wr.s3.to_parquet(
        df=mock_date, path=f"s3://{PROCESSED_BUCKET}/date/date.parquet", dataset=False
    )
    result = dim_date()
    assert result == "Pass: no actions required for date"


def test_dim_date_with_no_files_found(s3_client):
    result = dim_date()
    assert result == datetime(2020, 1, 1)


def test_dim_date_calls_update_dim_date_with_future_data(s3_client):
    wr.s3.to_parquet(
        df=mock_date, path=f"s3://{PROCESSED_BUCKET}/date/date.parquet", dataset=False
    )
    result = dim_date()
    assert result == datetime(2024, 11, 20).date()


def test_update_dim_date(s3_client):
    start_date = datetime(2024, 11, 20).date()
    result = update_dim_date(start_date)
    assert result.iloc[0]["date_id"] == datetime(2024, 11, 20)


"""Test sales order function for fact_sales_order"""


def test_sales_order_returns_correct_columns(s3_client):
    wr.s3.to_parquet(
        df=mock_sales_order,
        path=f"s3://{INGESTION_BUCKET}/sales_order/a/a/a/sales_order 2024-11-20",
        dataset=False,
    )
    fso_df = sales_order("sales_order", "2024-11-20")
    assert "sales_order_id" in fso_df.columns
    assert "created_date" in fso_df.columns
    assert "created_time" in fso_df.columns
    assert "last_updated_date" in fso_df.columns
    assert "last_updated_time" in fso_df.columns
    assert "sales_staff_id" in fso_df.columns
    assert "units_sold" in fso_df.columns
    assert "unit_price" in fso_df.columns
    assert "currency_id" in fso_df.columns
    assert "design_id" in fso_df.columns
    assert "agreed_payment_date" in fso_df.columns
    assert "agreed_delivery_date" in fso_df.columns
    assert "agreed_delivery_location_id" in fso_df.columns


def test_sales_order_raises_error_for_invalid_file_type(s3_client):
    wr.s3.to_csv(
        df=mock_design,
        path=f"s3://{INGESTION_BUCKET}/sales_order/a/a/a/sales_order 2024-11-20",
        dataset=False,
    )
    with pytest.raises(ArrowInvalid):
        sales_order("sales_order", "2024-11-20")


"""Test Lambda Handler"""


def test_lambda_handler(s3_client):
    mock_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "mock-bucket"},
                    "object": {"key": "design/a/a/a/design+2024-11-20"},
                }
            }
        ]
    }
    with patch("data_transformation.design") as mock_design_func:
        response = lambda_handler(mock_event, {})
        mock_design_func.assert_called_once_with("design", "2024-11-20")
        assert response["statusCode"] == 200
        assert "design processed successfully" in response["body"]


def test_lambda_handler_no_action_required_for_invalid_tablename(s3_client):
    mock_event_no_action = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "mock-bucket"},
                    "object": {"key": "toys/a/a/a/toys+2024-11-20"},
                }
            }
        ]
    }
    response = lambda_handler(mock_event_no_action, {})
    assert "Pass: no actions required" in response["body"]