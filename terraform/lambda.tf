# Ingestion Lambda

resource "aws_lambda_function" "lambda_ingestion_func" {
  function_name = var.lambda_ingestion
  role          = aws_iam_role.lambda_executive_role.arn
  handler       = "data_extraction.lambda_handler"  
  runtime       = var.python_runtime
  timeout = 600
  s3_bucket = aws_s3_bucket.lambda_code.id
  s3_key = aws_s3_object.lambda_code.key
  layers = [
    "arn:aws:lambda:eu-west-2:336392948345:layer:AWSSDKPandas-Python39:26"
  ]
  environment {
    variables = {
      INGESTION_BUCKET = var.ingestion_bucket
      PROCESSED_BUCKET = var.processed_bucket
      LAMBDA_BUCKET    = var.lambda_bucket
    }
  }
}

data "archive_file" "lambda" {
  type             = "zip"
  output_file_mode = "0666"
  source_file      = "${path.module}/../data_extraction.py" 
  output_path      = "${path.module}/../ingestion-lambda.zip"
}

# Process Lambda

resource "aws_lambda_function" "lambda_process_func" {
  function_name = var.lambda_process
  role          = aws_iam_role.lambda_executive_role.arn
  handler       = "data_transformation.lambda_handler"  
  runtime       = var.python_runtime
  timeout = 600
  s3_bucket = aws_s3_bucket.lambda_code.id
  s3_key = aws_s3_object.process-lambda-code.key
  layers = [
    "arn:aws:lambda:eu-west-2:336392948345:layer:AWSSDKPandas-Python39:26"
  ]
  environment {
    variables = {
      INGESTION_BUCKET = var.ingestion_bucket
      PROCESSED_BUCKET = var.processed_bucket
      LAMBDA_BUCKET    = var.lambda_bucket
    }
  }
}

data "archive_file" "process-lambda" {
  type             = "zip"
  output_file_mode = "0666"
  source_file      = "${path.module}/../data_transformation.py" 
  output_path      = "${path.module}/../process-lambda.zip"
}

# Load Lambda

resource "aws_lambda_function" "lambda_load_func" {
  function_name = var.lambda_load
  role          = aws_iam_role.lambda_executive_role.arn
  handler       = "data_loading.lambda_handler"  
  runtime       = var.python_runtime
  memory_size = 512
  timeout = 600
  s3_bucket = aws_s3_bucket.lambda_code.id
  s3_key = aws_s3_object.load-lambda-code.key
  layers = [
    "arn:aws:lambda:eu-west-2:336392948345:layer:AWSSDKPandas-Python39:26",
    "arn:aws:lambda:eu-west-2:770693421928:layer:Klayers-p39-SQLAlchemy:20",
    "arn:aws:lambda:eu-west-2:770693421928:layer:Klayers-p39-psycopg2-binary:1"
  ]
  environment {
    variables = {
      INGESTION_BUCKET = var.ingestion_bucket
      PROCESSED_BUCKET = var.processed_bucket
      LAMBDA_BUCKET    = var.lambda_bucket
    }
  }
}

data "archive_file" "load-lambda" {
  type             = "zip"
  output_file_mode = "0666"
  source_file      = "${path.module}/../data_loading.py" 
  output_path      = "${path.module}/../load-lambda.zip"
}


