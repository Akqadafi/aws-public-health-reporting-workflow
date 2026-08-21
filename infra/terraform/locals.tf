locals {
  name_prefix = "${var.project_name}-${var.environment}"
  bucket_base = "${local.name_prefix}-${data.aws_caller_identity.current.account_id}-${var.aws_region}"

  common_tags = {
    Project        = var.project_name
    Environment    = var.environment
    ManagedBy      = "Terraform"
    DataClass      = "SyntheticDemo"
    PortfolioClone = "true"
  }
}
