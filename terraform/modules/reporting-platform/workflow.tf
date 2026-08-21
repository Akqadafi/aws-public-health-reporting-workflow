data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../../application/backend/src"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_iam_role" "lambda" {
  name = "${local.name_prefix}-lambda"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_data" {
  name = "least-privilege-data-access"
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadInputsAndConfiguration"
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:GetObjectVersion"]
        Resource = [
          "${aws_s3_bucket.data.arn}/incoming/*",
          "${aws_s3_bucket.data.arn}/configuration/*",
          "${aws_s3_bucket.data.arn}/validated/*"
        ]
      },
      {
        Sid    = "WriteControlledOutputs"
        Effect = "Allow"
        Action = ["s3:PutObject"]
        Resource = [
          "${aws_s3_bucket.data.arn}/quarantine/*",
          "${aws_s3_bucket.data.arn}/validated/*",
          "${aws_s3_bucket.data.arn}/curated/*"
        ]
      },
      {
        Sid      = "UseDataKey"
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey"]
        Resource = aws_kms_key.data.arn
      }
    ]
  })
}

resource "aws_lambda_function" "validate" {
  function_name    = "${local.name_prefix}-validate"
  role             = aws_iam_role.lambda.arn
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  handler          = "health_reporting.aws_handlers.validate_handler"
  runtime          = "python3.13"
  architectures    = ["arm64"]
  memory_size      = 512
  timeout          = 60

  environment {
    variables = { KMS_KEY_ARN = aws_kms_key.data.arn }
  }
}

resource "aws_lambda_function" "transform" {
  function_name    = "${local.name_prefix}-transform"
  role             = aws_iam_role.lambda.arn
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  handler          = "health_reporting.aws_handlers.transform_handler"
  runtime          = "python3.13"
  architectures    = ["arm64"]
  memory_size      = 512
  timeout          = 60

  environment {
    variables = { KMS_KEY_ARN = aws_kms_key.data.arn }
  }
}

resource "aws_sns_topic" "operations" {
  name              = "${local.name_prefix}-operations"
  kms_master_key_id = "alias/aws/sns"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.notification_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.operations.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

resource "aws_cloudwatch_log_group" "workflow" {
  name              = "/aws/vendedlogs/states/${local.name_prefix}"
  retention_in_days = 30
}

resource "aws_iam_role" "step_functions" {
  name = "${local.name_prefix}-step-functions"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "step_functions" {
  role = aws_iam_role.step_functions.id
  name = "invoke-workflow-services"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = [aws_lambda_function.validate.arn, aws_lambda_function.transform.arn]
      },
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.operations.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery", "logs:GetLogDelivery", "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery", "logs:ListLogDeliveries", "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies", "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_sfn_state_machine" "reporting" {
  name     = "${local.name_prefix}-file-processing"
  role_arn = aws_iam_role.step_functions.arn

  logging_configuration {
    include_execution_data = false
    level                  = "ERROR"
    log_destination        = "${aws_cloudwatch_log_group.workflow.arn}:*"
  }

  tracing_configuration { enabled = true }

  definition = jsonencode({
    Comment = "Validate, quarantine, or curate an incoming reporting file"
    StartAt = "ValidateFile"
    States = {
      ValidateFile = {
        Type       = "Task"
        Resource   = "arn:${data.aws_partition.current.partition}:states:::lambda:invoke"
        OutputPath = "$.Payload"
        Parameters = {
          FunctionName = aws_lambda_function.validate.arn
          "Payload.$"  = "$"
        }
        Retry = [{
          ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
          IntervalSeconds = 2
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{ ErrorEquals = ["States.ALL"], ResultPath = "$.failure", Next = "WorkflowFailed" }]
        Next  = "ValidationPassed"
      }
      ValidationPassed = {
        Type    = "Choice"
        Choices = [{ Variable = "$.status", StringEquals = "PASS", Next = "TransformFile" }]
        Default = "NotifyQuarantine"
      }
      TransformFile = {
        Type       = "Task"
        Resource   = "arn:${data.aws_partition.current.partition}:states:::lambda:invoke"
        OutputPath = "$.Payload"
        Parameters = {
          FunctionName = aws_lambda_function.transform.arn
          "Payload.$"  = "$"
        }
        Retry = [{
          ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
          IntervalSeconds = 2
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{ ErrorEquals = ["States.ALL"], ResultPath = "$.failure", Next = "WorkflowFailed" }]
        Next  = "AwaitingManagerApproval"
      }
      NotifyQuarantine = {
        Type     = "Task"
        Resource = "arn:${data.aws_partition.current.partition}:states:::sns:publish"
        Parameters = {
          TopicArn    = aws_sns_topic.operations.arn
          Subject     = "Reporting file quarantined"
          "Message.$" = "States.Format('Cycle {} run {} failed validation. Review the encrypted error report at s3://{}/{}.', $.cycle_id, $.run_id, $.bucket, $.report_key)"
        }
        Next = "Quarantined"
      }
      Quarantined             = { Type = "Succeed" }
      AwaitingManagerApproval = { Type = "Succeed" }
      WorkflowFailed = {
        Type  = "Fail"
        Error = "ReportingWorkflowFailed"
        Cause = "An unexpected validation or transformation error occurred."
      }
    }
  })
}

resource "aws_iam_role" "eventbridge" {
  name = "${local.name_prefix}-eventbridge"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge" {
  name = "start-reporting-workflow"
  role = aws_iam_role.eventbridge.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "states:StartExecution", Resource = aws_sfn_state_machine.reporting.arn }]
  })
}

resource "aws_cloudwatch_event_rule" "incoming_object" {
  name = "${local.name_prefix}-incoming-object"
  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = [aws_s3_bucket.data.id] }
      object = { key = [{ prefix = "incoming/" }] }
    }
  })
}

resource "aws_cloudwatch_event_target" "workflow" {
  rule     = aws_cloudwatch_event_rule.incoming_object.name
  arn      = aws_sfn_state_machine.reporting.arn
  role_arn = aws_iam_role.eventbridge.arn
}
