locals {
  services = ["payment-api", "ledger", "notification"]
}

resource "aws_ecr_repository" "microservices" {
  for_each = toset(local.services)

  name                 = "${var.project_name}/${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true # Automated AWS vulnerability scanning
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

output "ecr_repository_urls" {
  description = "ECR Repository URLs"
  value = {
    for k, v in aws_ecr_repository.microservices : k => v.repository_url
  }
}