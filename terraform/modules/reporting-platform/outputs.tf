output "data_bucket" {
  value       = aws_s3_bucket.data.id
  description = "Encrypted bucket containing controlled workflow prefixes."
}

output "workflow_arn" {
  value = aws_sfn_state_machine.reporting.arn
}

output "frontend_bucket" {
  value = var.enable_frontend ? aws_s3_bucket.frontend[0].id : null
}

output "frontend_distribution_id" {
  value = var.enable_frontend ? aws_cloudfront_distribution.frontend[0].id : null
}

output "frontend_url" {
  value = var.enable_frontend ? "https://${aws_cloudfront_distribution.frontend[0].domain_name}" : null
}

output "operations_topic_arn" {
  value = aws_sns_topic.operations.arn
}

output "audit_bucket" {
  value       = aws_s3_bucket.audit.id
  description = "Bucket containing CloudTrail audit records."
}
