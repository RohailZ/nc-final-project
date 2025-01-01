
# SNS for ingestion lambda

resource "aws_sns_topic" "ingestion-topic" {
  name = "ingestion-topic"
  }

resource "aws_sns_topic_subscription" "email-target" {
  topic_arn = aws_sns_topic.ingestion-topic.arn
  protocol  = "email"
  endpoint  = "dimensionaltransformers1@gmail.com" 
}

resource "aws_cloudwatch_log_metric_filter" "ingestion-error-filter" {
  name           = "ingestion-error-filter"
  pattern        = "Alert"
  log_group_name = "/aws/lambda/${var.lambda_ingestion}"

  metric_transformation {
    name      = "ErrorCount"
    namespace = "Lambda/test"
    value     = "1"
  }
  depends_on = [ aws_lambda_function.lambda_ingestion_func ]
}


resource "aws_cloudwatch_metric_alarm" "ingestion_sns_alarm" {
  alarm_name          = "ingestion_sns_alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "ErrorCount"
  namespace           = "Lambda/test"
  period              = 300 #TODO depends on eventbridge timer
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alert! ingestion phase needs your attention" 
  actions_enabled     = "true"
  alarm_actions       = [aws_sns_topic.ingestion-topic.arn]
  ok_actions          = [aws_sns_topic.ingestion-topic.arn]
  insufficient_data_actions = []
  treat_missing_data = "notBreaching"
  
}

# SNS for process lambda function 

resource "aws_sns_topic" "process-topic" {
  name = "process-topic"
  }

resource "aws_sns_topic_subscription" "email-target-for-process" {
  topic_arn = aws_sns_topic.process-topic.arn
  protocol  = "email"
  endpoint  = "dimensionaltransformers1@gmail.com" 
}

resource "aws_cloudwatch_log_metric_filter" "process-error-filter" {
  name           = "process-error-filter"
  pattern        = "Alert"
  log_group_name = "/aws/lambda/${var.lambda_process}"

  metric_transformation {
    name      = "ProcessErrorCount"
    namespace = "Lambda/test-process"
    value     = "1"
  }
  depends_on = [ aws_lambda_function.lambda_process_func ]
}

resource "aws_cloudwatch_metric_alarm" "process_sns_alarm" {
  alarm_name          = "process_sns_alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "ProcessErrorCount"
  namespace           = "Lambda/test-process"
  period              = 300 #TODO depends on eventbridge timer
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alert! pocess phase needs your attention" 
  actions_enabled     = "true"
  alarm_actions       = [aws_sns_topic.process-topic.arn]
  ok_actions          = [aws_sns_topic.process-topic.arn]
  insufficient_data_actions = []
  treat_missing_data = "notBreaching"
}

# SNS for load lambda

resource "aws_sns_topic" "load-topic" {
  name = "load-topic"
  }

resource "aws_sns_topic_subscription" "email-target-for-load" {
  topic_arn = aws_sns_topic.load-topic.arn
  protocol  = "email"
  endpoint  = "dimensionaltransformers1@gmail.com" 
}

resource "aws_cloudwatch_log_metric_filter" "load-error-filter" {
  name           = "process-error-filter"
  pattern        = "Alert"
  log_group_name = "/aws/lambda/${var.lambda_load}"

  metric_transformation {
    name      = "LoadErrorCount"
    namespace = "Lambda/test-load"
    value     = "1"
  }
  depends_on = [ aws_lambda_function.lambda_load_func ]
}

resource "aws_cloudwatch_metric_alarm" "load_sns_alarm" {
  alarm_name          = "load_sns_alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "LoadErrorCount"
  namespace           = "Lambda/test-load"
  period              = 300 #TODO depends on eventbridge timer
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alert! load phase needs your attention" 
  actions_enabled     = "true"
  alarm_actions       = [aws_sns_topic.load-topic.arn]
  ok_actions          = [aws_sns_topic.load-topic.arn]
  insufficient_data_actions = []
  treat_missing_data = "notBreaching"
  
}