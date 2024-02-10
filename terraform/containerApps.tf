############### Containers Apps ################################
# Container Apps Environment
resource "azapi_resource" "containerapp_environment" {
  type      = "Microsoft.App/managedEnvironments@2023-05-01"
  name      = "container-env"
  parent_id = azurerm_resource_group.containers.id
  location  = var.location

  body = jsonencode({
    properties = {
      appLogsConfiguration = {
        destination               = null,
        logAnalyticsConfiguration = null
      },
      workloadProfiles = [
        {
          name                = var.workload_profile_name,
          workloadProfileType = var.workload_profile_name
        }
      ],
      vnetConfiguration = {
        internal               = false
        infrastructureSubnetId = azurerm_subnet.container.id
      }
      zoneRedundant = false
    }
    }
  )
  depends_on = [
    azurerm_virtual_network.chsystem, azurerm_subnet.container
  ]
  response_export_values  = ["properties.defaultDomain", "properties.staticIp"]
  ignore_missing_property = true
}

# need to remove dashes and lower case the name of the secrets
locals {
  ca_postgrest_secrets = {
    (var.s_DB-URI)     = lower(replace(azurerm_key_vault_secret.secrets[var.s_DB-URI].name, "-", ""))
    (var.s_PG-CH-USER) = lower(replace(azurerm_key_vault_secret.secrets[var.s_PG-CH-USER].name, "-", ""))
  }
}

# Container App: PostgREST
resource "azapi_resource" "container_app_postgrest" {
  type      = var.azapi_container-app-type
  name      = "${var.name}-postgrest"
  parent_id = azurerm_resource_group.containers.id
  location  = var.location

  body = jsonencode({
    identity = {
      type = var.container-app_identity-type
      userAssignedIdentities = {
        azurerm_user_assigned_identity.ids[var.postgrest].id = {}
      }
    }
    properties = {
      configuration = {
        activeRevisionsMode = "Single"
        ingress = {
          allowInsecure = true
          targetPort    = 3000
          transport     = "Auto"
          traffic = [
            {
              latestRevision = true
              weight         = 100
            }
          ]
        }
        # this will delete any other secret not defined here
        secrets = [
          {
            name        = local.ca_postgrest_secrets[var.s_DB-URI]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_DB-URI}"
            identity    = azurerm_user_assigned_identity.ids[var.postgrest].id
          },
          {
            name        = local.ca_postgrest_secrets[var.s_PG-CH-USER]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_PG-CH-USER}"
            identity    = azurerm_user_assigned_identity.ids[var.postgrest].id
          }
        ]
      }
      environmentId = azapi_resource.containerapp_environment.id
      template = {
        containers = [
          {
            name  = "${var.name}-postgrest"
            image = "docker.io/postgrest/postgrest"
            resources = {
              cpu    = 1,
              memory = "2Gi"
            }
            env = [
              {
                name      = "PGRST_DB_URI"
                secretRef = local.ca_postgrest_secrets[var.s_DB-URI]
              },
              {
                name      = "PGRST_DB_ANON_ROLE"
                secretRef = local.ca_postgrest_secrets[var.s_PG-CH-USER]
              }
            ]
          }
        ]
        scale = {
          minReplicas = 0
        }
      }
      workloadProfileName = var.workload_profile_name
    }
  })

  response_export_values  = ["properties.configuration.ingress.fqdn"]
  ignore_missing_property = true

  depends_on = [azurerm_role_assignment.postgrest_secrets]
}

# RBAC for ACR Pull
resource "azurerm_role_assignment" "acr_pull" {
  for_each = toset([
    var.web,
    var.discord,
    var.notify,
  ])

  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.ids[each.key].principal_id
}

# add POSTGREST-URL secrete value
resource "azurerm_key_vault_secret" "POSTGREST-URL" {
  name         = var.s_POSTGREST-URL
  value        = "https://${jsondecode(azapi_resource.container_app_postgrest.output).properties.configuration.ingress.fqdn}"
  key_vault_id = azurerm_key_vault.keyvault.id

  lifecycle {
    replace_triggered_by = [
      azapi_resource.container_app_postgrest
    ]
  }
}

# web RBAC for POSTGREST-URL
resource "azurerm_role_assignment" "POSTGREST-URL" {
  scope                = azurerm_key_vault_secret.POSTGREST-URL.resource_versionless_id
  role_definition_name = var.RBAC_SECRET_USER
  principal_id         = azurerm_user_assigned_identity.ids[var.web].principal_id
}

# need to remove dashes and lower case the name of the secrets
locals {
  ca_web_secrets = {
    (var.s_LOGTAIL-WEB)     = lower(replace(azurerm_key_vault_secret.secrets[var.s_LOGTAIL-WEB].name, "-", ""))
    (var.s_POSTGREST-URL)   = lower(replace(azurerm_key_vault_secret.POSTGREST-URL.name, "-", ""))
    (var.s_HOST)            = lower(replace(azurerm_key_vault_secret.secrets[var.s_HOST].name, "-", ""))
    (var.s_PWL-URL)         = lower(replace(azurerm_key_vault_secret.secrets[var.s_PWL-URL].name, "-", ""))
    (var.s_PWL-PRIVATE-KEY) = lower(replace(azurerm_key_vault_secret.secrets[var.s_PWL-PRIVATE-KEY].name, "-", ""))
    (var.s_PWL-PUBLIC-KEY)  = lower(replace(azurerm_key_vault_secret.secrets[var.s_PWL-PUBLIC-KEY].name, "-", ""))
  }
}

# Container App: Web
resource "azapi_resource" "container_app_web" {
  type      = var.azapi_container-app-type
  name      = "${var.name}-web"
  parent_id = azurerm_resource_group.containers.id
  location  = var.location

  body = jsonencode({
    identity = {
      type = var.container-app_identity-type
      userAssignedIdentities = {
        azurerm_user_assigned_identity.ids[var.web].id = {}
      }
    }
    properties = {
      configuration = {
        activeRevisionsMode = "Single"
        ingress = {
          external      = true
          allowInsecure = false
          targetPort    = 8080
          transport     = "Auto"
          traffic = [
            {
              latestRevision = true
              weight         = 100
            }
          ]
          stickySessions = {
            affinity = "sticky"
          }
        }
        registries = [
          {
            identity = azurerm_user_assigned_identity.ids[var.web].id
            server   = azurerm_container_registry.acr.login_server
          }
        ]
        # this will delete any other secret not defined here
        secrets = [
          {
            name        = local.ca_web_secrets[var.s_LOGTAIL-WEB]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_LOGTAIL-WEB}"
            identity    = azurerm_user_assigned_identity.ids[var.web].id
          },
          {
            name        = local.ca_web_secrets[var.s_POSTGREST-URL]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_POSTGREST-URL}"
            identity    = azurerm_user_assigned_identity.ids[var.web].id
          },
          {
            name        = local.ca_web_secrets[var.s_HOST]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_HOST}"
            identity    = azurerm_user_assigned_identity.ids[var.web].id
          },
          {
            name        = local.ca_web_secrets[var.s_PWL-URL]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_PWL-URL}"
            identity    = azurerm_user_assigned_identity.ids[var.web].id
          },
          {
            name        = local.ca_web_secrets[var.s_PWL-PRIVATE-KEY]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_PWL-PRIVATE-KEY}"
            identity    = azurerm_user_assigned_identity.ids[var.web].id
          },
          {
            name        = local.ca_web_secrets[var.s_PWL-PUBLIC-KEY]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_PWL-PUBLIC-KEY}"
            identity    = azurerm_user_assigned_identity.ids[var.web].id
          }
        ]
      }
      environmentId = azapi_resource.containerapp_environment.id
      template = {
        containers = [
          {
            name  = "${var.name}-web"
            image = "${azurerm_container_registry.acr.name}.azurecr.io/${var.name}:latest"
            resources = {
              cpu    = 1,
              memory = "2Gi"
            }
            command = ["python3", "chsystem/web/main.py"]
            env = [
              {
                name      = "URL"
                secretRef = local.ca_web_secrets[var.s_POSTGREST-URL]
              },
              {
                name      = "LOGTAIL_WEB"
                secretRef = local.ca_web_secrets[var.s_LOGTAIL-WEB]
              },
              {
                name      = "HOST"
                secretRef = local.ca_web_secrets[var.s_HOST]
              },
              {
                name      = "PWL_URL"
                secretRef = local.ca_web_secrets[var.s_PWL-URL]
              },
              {
                name      = "PWL_PRIVATE_KEY"
                secretRef = local.ca_web_secrets[var.s_PWL-PRIVATE-KEY]
              },
              {
                name      = "PWL_PUBLIC_KEY"
                secretRef = local.ca_web_secrets[var.s_PWL-PUBLIC-KEY]
              }
            ]
          }
        ]
        scale = {
          minReplicas = 0
        }
      }
      workloadProfileName = var.workload_profile_name
    }
  })

  response_export_values  = ["properties.configuration.ingress.fqdn"]
  ignore_missing_property = true

  depends_on = [
    azurerm_role_assignment.web_secrets,
    azurerm_key_vault_secret.POSTGREST-URL,
    azurerm_role_assignment.POSTGREST-URL
  ]

  lifecycle {
    replace_triggered_by = [
      azurerm_key_vault_secret.POSTGREST-URL
    ]
  }
}

# need to remove dashes and lower case the name of the secrets
locals {
  ca_discord_secrets = {
    (var.s_DB-URI)           = lower(replace(azurerm_key_vault_secret.secrets[var.s_DB-URI].name, "-", ""))
    (var.s_DISCORD-TOKEN)    = lower(replace(azurerm_key_vault_secret.secrets[var.s_DISCORD-TOKEN].name, "-", ""))
    (var.s_LOGTAIL-DISCORD)  = lower(replace(azurerm_key_vault_secret.secrets[var.s_LOGTAIL-DISCORD].name, "-", ""))
    (var.s_LOGTAIL-DATABASE) = lower(replace(azurerm_key_vault_secret.secrets[var.s_LOGTAIL-DATABASE].name, "-", ""))
  }
}

# Container App: Discord
resource "azapi_resource" "container_app_discord" {
  type      = var.azapi_container-app-type
  name      = "${var.name}-discord"
  parent_id = azurerm_resource_group.containers.id
  location  = var.location

  body = jsonencode({
    identity = {
      type = var.container-app_identity-type
      userAssignedIdentities = {
        azurerm_user_assigned_identity.ids[var.discord].id = {}
      }
    }
    properties = {
      configuration = {
        activeRevisionsMode = "Single"
        registries = [
          {
            identity = azurerm_user_assigned_identity.ids[var.discord].id
            server   = azurerm_container_registry.acr.login_server
          }
        ]
        # this will delete any other secret not defined here
        secrets = [
          {
            name        = local.ca_discord_secrets[var.s_DB-URI]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_DB-URI}"
            identity    = azurerm_user_assigned_identity.ids[var.discord].id
          },
          {
            name        = local.ca_discord_secrets[var.s_DISCORD-TOKEN]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_DISCORD-TOKEN}"
            identity    = azurerm_user_assigned_identity.ids[var.discord].id
          },
          {
            name        = local.ca_discord_secrets[var.s_LOGTAIL-DISCORD]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_LOGTAIL-DISCORD}"
            identity    = azurerm_user_assigned_identity.ids[var.discord].id
          },
          {
            name        = local.ca_discord_secrets[var.s_LOGTAIL-DATABASE]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_LOGTAIL-DATABASE}"
            identity    = azurerm_user_assigned_identity.ids[var.discord].id
          }
        ]
      }
      environmentId = azapi_resource.containerapp_environment.id
      template = {
        containers = [
          {
            name  = "${var.name}-discord"
            image = "${azurerm_container_registry.acr.name}.azurecr.io/${var.name}:latest"
            resources = {
              cpu    = 1,
              memory = "2Gi"
            }
            command = ["python3", "chsystem/discord/discordBot.py"]
            env = [
              {
                name      = "DB_URI"
                secretRef = local.ca_discord_secrets[var.s_DB-URI]
              },
              {
                name      = "DISCORD_TOKEN"
                secretRef = local.ca_discord_secrets[var.s_DISCORD-TOKEN]
              },
              {
                name      = "LOGTAIL_DISCORD"
                secretRef = local.ca_discord_secrets[var.s_LOGTAIL-DISCORD]
              },
              {
                name      = "LOGTAIL_DATABASE"
                secretRef = local.ca_discord_secrets[var.s_LOGTAIL-DATABASE]
              }
            ]
          }
        ]
        scale = {
          minReplicas = 1
          maxReplicas = 1
        }
      }
      workloadProfileName = var.workload_profile_name
    }
  })

  ignore_missing_property = true

  depends_on = [azurerm_role_assignment.discord_secrets]
}

# need to remove dashes and lower case the name of the secrets
locals {
  ca_notify_secrets = {
    (var.s_DB-URI)           = lower(replace(azurerm_key_vault_secret.secrets[var.s_DB-URI].name, "-", ""))
    (var.s_LOGTAIL-NOTIFY)   = lower(replace(azurerm_key_vault_secret.secrets[var.s_LOGTAIL-NOTIFY].name, "-", ""))
    (var.s_LOGTAIL-DATABASE) = lower(replace(azurerm_key_vault_secret.secrets[var.s_LOGTAIL-DATABASE].name, "-", ""))
  }
}

# Container App: Notify
resource "azapi_resource" "container_app_notify" {
  type      = var.azapi_container-app-type
  name      = "${var.name}-notify"
  parent_id = azurerm_resource_group.containers.id
  location  = var.location

  body = jsonencode({
    identity = {
      type = var.container-app_identity-type
      userAssignedIdentities = {
        azurerm_user_assigned_identity.ids[var.notify].id = {}
      }
    }
    properties = {
      configuration = {
        activeRevisionsMode = "Single"
        registries = [
          {
            identity = azurerm_user_assigned_identity.ids[var.notify].id
            server   = azurerm_container_registry.acr.login_server
          }
        ]
        # this will delete any other secret not defined here
        secrets = [
          {
            name        = local.ca_notify_secrets[var.s_DB-URI]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_DB-URI}"
            identity    = azurerm_user_assigned_identity.ids[var.notify].id
          },
          {
            name        = local.ca_notify_secrets[var.s_LOGTAIL-NOTIFY]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_LOGTAIL-NOTIFY}"
            identity    = azurerm_user_assigned_identity.ids[var.notify].id
          },
          {
            name        = local.ca_notify_secrets[var.s_LOGTAIL-DATABASE]
            keyVaultUrl = "${azurerm_key_vault.keyvault.vault_uri}secrets/${var.s_LOGTAIL-DATABASE}"
            identity    = azurerm_user_assigned_identity.ids[var.notify].id
          }
        ]
      }
      environmentId = azapi_resource.containerapp_environment.id
      template = {
        containers = [
          {
            name  = "${var.name}-notify"
            image = "${azurerm_container_registry.acr.name}.azurecr.io/${var.name}:latest"
            resources = {
              cpu    = 1,
              memory = "2Gi"
            }
            command = ["python3", "chsystem/notify/notify.py"]
            env = [
              {
                name      = "DB_URI"
                secretRef = local.ca_notify_secrets[var.s_DB-URI]
              },
              {
                name      = "LOGTAIL_NOTIFY"
                secretRef = local.ca_notify_secrets[var.s_LOGTAIL-NOTIFY]
              },
              {
                name      = "LOGTAIL_DATABASE"
                secretRef = local.ca_notify_secrets[var.s_LOGTAIL-DATABASE]
              }
            ]
          }
        ]
        scale = {
          minReplicas = 1
          maxReplicas = 1
        }
      }
      workloadProfileName = var.workload_profile_name
    }
  })

  ignore_missing_property = true

  depends_on = [azurerm_role_assignment.notify_secrets]
}
