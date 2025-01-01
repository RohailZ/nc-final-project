resource "aws_s3_bucket" "ingestion_bucket" {
    bucket = var.ingestion_bucket
    force_destroy = true
}

resource "aws_s3_bucket" "processed_bucket" {
  bucket = var.processed_bucket
  force_destroy = true
}

resource "aws_s3_bucket" "lambda_code" {
    bucket = var.lambda_bucket
    force_destroy = true
}

resource "aws_s3_object" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id
  key = "ingestion-lambda.zip"
  source = "${path.module}/../ingestion-lambda.zip"
}

resource "aws_s3_object" "process-lambda-code" {
  bucket = aws_s3_bucket.lambda_code.id
  key = "process-lambda.zip"
  source = "${path.module}/../process-lambda.zip"
}

resource "aws_s3_object" "load-lambda-code" {
  bucket = aws_s3_bucket.lambda_code.id
  key = "load-lambda.zip"
  source = "${path.module}/../load-lambda.zip"
}
