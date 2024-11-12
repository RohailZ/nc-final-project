resource "aws_cloudwatch_event_rule" "scheduler" {
  name = "lambda_5_minutes"
  schedule_expression = "rate(2 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
    target_id = "lambda_target"
    rule = aws_cloudwatch_event_rule.scheduler.name
    arn = aws_lambda_function.lambda_ingestion_func.arn # TODO
}
 
resource "aws_lambda_permission" "allow_cloudwatch_events" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.lambda_ingestion_func.function_name #TODO
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.scheduler.arn

}