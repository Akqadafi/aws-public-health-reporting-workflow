variable "aws_region" {
  description = "AWS Region for regional resources."
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Lowercase name used in resource names."
  type        = string
  default     = "health-reporting-demo"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.project_name))
    error_message = "project_name must be 3-31 lowercase letters, numbers, or hyphens."
  }
}

variable "environment" {
  type    = string
  default = "portfolio"
}

variable "enable_frontend" {
  description = "Create the CloudFront distribution and frontend S3 origin."
  type        = bool
  default     = true
}

variable "enable_full_stack" {
  description = "Create cost-bearing VPC, NAT, ECS, ALB, and RDS resources."
  type        = bool
  default     = false
}

variable "api_image_uri" {
  description = "Container image for the FastAPI service; required when enable_full_stack is true."
  type        = string
  default     = ""

  validation {
    condition     = !var.enable_full_stack || length(var.api_image_uri) > 0
    error_message = "api_image_uri is required when enable_full_stack is true."
  }
}

variable "alb_certificate_arn" {
  description = "ACM certificate for the HTTPS API listener; required for the full stack."
  type        = string
  default     = ""

  validation {
    condition     = !var.enable_full_stack || length(var.alb_certificate_arn) > 0
    error_message = "alb_certificate_arn is required when enable_full_stack is true."
  }
}

variable "oidc_issuer" {
  description = "OIDC issuer used by the API to validate staff tokens."
  type        = string
  default     = ""
}

variable "oidc_audience" {
  description = "Expected audience in staff access tokens."
  type        = string
  default     = ""
}

variable "notification_email" {
  description = "Optional address for workflow alarms; subscription confirmation is required."
  type        = string
  default     = ""
}

variable "protect_data" {
  description = "Enable deletion protection and a final RDS snapshot in the full stack."
  type        = bool
  default     = true
}
