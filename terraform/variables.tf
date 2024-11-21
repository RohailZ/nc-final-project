variable "region" {
  default = "eu-west-2"
}

variable "ingestion_bucket" {
    default = "team-501-dimensional-transformers-ingestion-bucket"
}

variable "processed_bucket" {
  default = "team-501-dimensional-transformers-process-bucket"
}

variable "lambda_bucket" {
    default = "team-501-dimensional-transformers-lambda-bucket"
}

variable "lambda_ingestion" {
  default = "lambda-ingestion-handler"
}

variable "lambda_process" {
  default = "lambda-process-handler"
}

variable "python_runtime" {
  type    = string
  default = "python3.9"
}
variable "lambda_load" {
  default = "lambda-load-handler"
}