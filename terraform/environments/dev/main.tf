module "reporting_platform" {
  source = "../../modules/reporting-platform"

  aws_region          = var.aws_region
  project_name        = var.project_name
  environment         = "dev"
  enable_frontend     = var.enable_frontend
  enable_full_stack   = var.enable_full_stack
  api_image_uri       = var.api_image_uri
  alb_certificate_arn = var.alb_certificate_arn
  oidc_issuer         = var.oidc_issuer
  oidc_audience       = var.oidc_audience
  notification_email  = var.notification_email
  protect_data        = var.protect_data
}
