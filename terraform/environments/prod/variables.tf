variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "project_name" {
  type    = string
  default = "health-reporting-demo"
}

variable "enable_frontend" {
  type    = bool
  default = true
}

variable "enable_full_stack" {
  type    = bool
  default = false
}

variable "api_image_uri" {
  type    = string
  default = ""
}

variable "alb_certificate_arn" {
  type    = string
  default = ""
}

variable "oidc_issuer" {
  type    = string
  default = ""
}

variable "oidc_audience" {
  type    = string
  default = ""
}

variable "notification_email" {
  type    = string
  default = ""
}

variable "protect_data" {
  type    = bool
  default = true
}
