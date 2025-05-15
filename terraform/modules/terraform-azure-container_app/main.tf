terraform {
  required_providers {
    azapi = {
      source  = "azure/azapi"
      version = "2.4.0"
    }
  }
}

resource "azapi_resource" "container_app" {
  type      = "Microsoft.App/containerApps@2023-05-01"
  name      = var.name
  parent_id = var.resource-id
  location  = var.location

  body = jsonencode({
    identity = {
      type = "UserAssigned"
      userAssignedIdentities = {
        (var.identity-id) = {}
      }
    }
    properties = {
      configuration = {
        activeRevisionsMode = "Single"
        registries = [
          {
            identity = var.identity-id
            server   = var.acr-login_server
          }
        ]
        # this will delete any other secret not defined here
        secrets = var.secrets
      }
      environmentId = var.environmentId
      template = {
        containers = [
          {
            name  = var.name
            image = var.container.image
            resources = {
              cpu    = var.container.cpu,
              memory = var.container.memory
            }
            command = var.container.command
            env     = var.env
          }
        ]
        scale = var.scale
      }
      workloadProfileName = var.workload_profile_name
    }
  })

  ignore_missing_property = var.ignore_missing_property
  response_export_values  = var.response_export_values
}
