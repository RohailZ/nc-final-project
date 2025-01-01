# Event for ingestion lambda

resource "aws_cloudwatch_event_rule" "scheduler" {
  name = "lambda_5_minutes"
  schedule_expression = "rate(5 minutes)" # Time to be finalised
}

resource "aws_cloudwatch_event_target" "lambda_target" {
    target_id = "lambda_target"
    rule = aws_cloudwatch_event_rule.scheduler.name
    arn = aws_lambda_function.lambda_ingestion_func.arn 
}
 
resource "aws_lambda_permission" "allow_cloudwatch_events" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.lambda_ingestion_func.function_name 
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.scheduler.arn

}

# Event for process lambda

resource "aws_s3_bucket_notification" "s3_trigger_lambda_notification" {
  bucket = aws_s3_bucket.ingestion_bucket.id
  depends_on = [ aws_lambda_permission.allow_s3_to_invoke_lambda ]

  lambda_function {
    events = ["s3:ObjectCreated:*"]  # Trigger on all object creation events
    lambda_function_arn = aws_lambda_function.lambda_process_func.arn
  }
}

resource "aws_lambda_permission" "allow_s3_to_invoke_lambda" {
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_process_func.function_name
  principal = "s3.amazonaws.com"
  source_arn = aws_s3_bucket.ingestion_bucket.arn
}

# Event for Load lambda

resource "aws_s3_bucket_notification" "s3_trigger_load_lambda_notification" {
  bucket = aws_s3_bucket.processed_bucket.id
  depends_on = [ aws_lambda_permission.allow_s3_to_invoke_load_lambda ]

  lambda_function {
    events = ["s3:ObjectCreated:*"]  # Trigger on all object creation events
    lambda_function_arn = aws_lambda_function.lambda_load_func.arn
  }
}

resource "aws_lambda_permission" "allow_s3_to_invoke_load_lambda" {
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_load_func.function_name
  principal = "s3.amazonaws.com"
  source_arn = aws_s3_bucket.processed_bucket.arn
}