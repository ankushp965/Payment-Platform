resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.project_name}/database-credentials"
  description             = "PostgreSQL master credentials for Ledger service"
  recovery_window_in_days = 0 # Immediate deletion on destroy (no 30-day retention cost!)
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = "postgres"
    password = var.db_password
    dbname   = "ledger_db"
  })
}

output "secrets_manager_arn" {
  description = "ARN of database secret in AWS Secrets Manager"
  value       = aws_secretsmanager_secret.db_credentials.arn
}