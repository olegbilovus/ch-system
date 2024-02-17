output "fqdn" {
  value = jsondecode(azapi_resource.container_app.output).properties.configuration.ingress.fqdn
}
