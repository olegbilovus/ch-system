output "PostgreSQL_FQDN" {
  value = azurerm_postgresql_flexible_server.db.fqdn
}

output "VM_FQDN" {
  value = azurerm_public_ip.vm.fqdn
}

output "SSH_PRIVATE_KEY" {
  value     = tls_private_key.ssh.private_key_pem
  sensitive = true
}

output "ACR_FQDN" {
  value = azurerm_container_registry.acr.login_server
}

output "CH-WEB_FQDN" {
  value = jsondecode(azapi_resource.container_app_web.output).properties.configuration.ingress.fqdn
}
