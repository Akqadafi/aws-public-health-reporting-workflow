provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project        = var.project_name
      Environment    = "prod"
      ManagedBy      = "Terraform"
      DataClass      = "SyntheticDemo"
      PortfolioClone = "true"
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project        = var.project_name
      Environment    = "prod"
      ManagedBy      = "Terraform"
      DataClass      = "SyntheticDemo"
      PortfolioClone = "true"
    }
  }
}
