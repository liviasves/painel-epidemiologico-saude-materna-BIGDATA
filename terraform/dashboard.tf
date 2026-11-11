resource "aiven_pg_user" "dashboard" {
  project      = var.aiven_project
  service_name = aiven_pg.banco.service_name
  username     = "dashboard_leitura"
}

output "dashboard_database_url" {
  description = "Conexão somente leitura usada pelo dashboard (vai nos Secrets do Streamlit)"
  value       = "postgresql://${aiven_pg_user.dashboard.username}:${aiven_pg_user.dashboard.password}@${aiven_pg.banco.service_host}:${aiven_pg.banco.service_port}/defaultdb?sslmode=require"
  sensitive   = true
}
