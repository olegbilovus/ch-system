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
  vault_uri = "${azurerm_key_vault.keyvault.vault_uri}secrets/"
  ca_postgrest_secrets = {
    (var.s_DB-URI)     = lower(replace(azurerm_key_vault_secret.secrets[var.s_DB-URI].name, "-", ""))
    (var.s_PG-CH-USER) = lower(replace(azurerm_key_vault_secret.secrets[var.s_PG-CH-USER].name, "-", ""))
  }
  ca_postgrest_identity = azurerm_user_assigned_identity.ids[var.postgrest].id
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
        (local.ca_postgrest_identity) = {}
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
            keyVaultUrl = "${local.vault_uri}${var.s_DB-URI}"
            identity    = local.ca_postgrest_identity
          },
          {
            name        = local.ca_postgrest_secrets[var.s_PG-CH-USER]
            keyVaultUrl = "${local.vault_uri}${var.s_PG-CH-USER}"
            identity    = local.ca_postgrest_identity
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
  ch_image = "${azurerm_container_registry.acr.name}.azurecr.io/${var.name}:latest"
  ca_web_secrets = {
    (var.s_LOGTAIL-WEB)     = lower(replace(azurerm_key_vault_secret.secrets[var.s_LOGTAIL-WEB].name, "-", ""))
    (var.s_POSTGREST-URL)   = lower(replace(azurerm_key_vault_secret.POSTGREST-URL.name, "-", ""))
    (var.s_HOST)            = lower(replace(azurerm_key_vault_secret.secrets[var.s_HOST].name, "-", ""))
    (var.s_PWL-URL)         = lower(replace(azurerm_key_vault_secret.secrets[var.s_PWL-URL].name, "-", ""))
    (var.s_PWL-PRIVATE-KEY) = lower(replace(azurerm_key_vault_secret.secrets[var.s_PWL-PRIVATE-KEY].name, "-", ""))
    (var.s_PWL-PUBLIC-KEY)  = lower(replace(azurerm_key_vault_secret.secrets[var.s_PWL-PUBLIC-KEY].name, "-", ""))
  }
  ca_web_identity = azurerm_user_assigned_identity.ids[var.web].id
}

# Container App: Web
## Can not use the module here because the lifecycle is needed but modules do not support the lifecycle
resource "azapi_resource" "container_app_web" {
  type      = var.azapi_container-app-type
  name      = "${var.name}-web"
  parent_id = azurerm_resource_group.containers.id
  location  = var.location

  body = jsonencode({
    identity = {
      type = var.container-app_identity-type
      userAssignedIdentities = {
        (local.ca_web_identity) = {}
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
            identity = local.ca_web_identity
            server   = azurerm_container_registry.acr.login_server
          }
        ]
        # this will delete any other secret not defined here
        secrets = [
          {
            name        = local.ca_web_secrets[var.s_LOGTAIL-WEB]
            keyVaultUrl = "${local.vault_uri}${var.s_LOGTAIL-WEB}"
            identity    = local.ca_web_identity
          },
          {
            name        = local.ca_web_secrets[var.s_POSTGREST-URL]
            keyVaultUrl = "${local.vault_uri}${var.s_POSTGREST-URL}"
            identity    = local.ca_web_identity
          },
          {
            name        = local.ca_web_secrets[var.s_HOST]
            keyVaultUrl = "${local.vault_uri}${var.s_HOST}"
            identity    = local.ca_web_identity
          },
          {
            name        = local.ca_web_secrets[var.s_PWL-URL]
            keyVaultUrl = "${local.vault_uri}${var.s_PWL-URL}"
            identity    = local.ca_web_identity
          },
          {
            name        = local.ca_web_secrets[var.s_PWL-PRIVATE-KEY]
            keyVaultUrl = "${local.vault_uri}${var.s_PWL-PRIVATE-KEY}"
            identity    = local.ca_web_identity
          },
          {
            name        = local.ca_web_secrets[var.s_PWL-PUBLIC-KEY]
            keyVaultUrl = "${local.vault_uri}${var.s_PWL-PUBLIC-KEY}"
            identity    = local.ca_web_identity
          }
        ]
      }
      environmentId = azapi_resource.containerapp_environment.id
      template = {
        containers = [
          {
            name  = "${var.name}-web"
            image = local.ch_image
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
  ca_discord_identity = azurerm_user_assigned_identity.ids[var.discord].id
}

# Container App: Discord
module "container_app_discord" {
  source = "./modules/container-app"

  name          = "${var.name}-discord"
  resource-id   = azurerm_resource_group.containers.id
  location      = var.location
  environmentId = azapi_resource.containerapp_environment.id
  identity-id   = local.ca_discord_identity

  acr-login_server = azurerm_container_registry.acr.login_server

  container = {
    image   = local.ch_image
    cpu     = 1
    memory  = "2Gi"
    command = ["python3", "chsystem/discord/discordBot.py"]
  }

  secrets = [
    {
      name        = local.ca_discord_secrets[var.s_DB-URI]
      keyVaultUrl = "${local.vault_uri}${var.s_DB-URI}"
      identity    = local.ca_discord_identity
    },
    {
      name        = local.ca_discord_secrets[var.s_DISCORD-TOKEN]
      keyVaultUrl = "${local.vault_uri}${var.s_DISCORD-TOKEN}"
      identity    = local.ca_discord_identity
    },
    {
      name        = local.ca_discord_secrets[var.s_LOGTAIL-DISCORD]
      keyVaultUrl = "${local.vault_uri}${var.s_LOGTAIL-DISCORD}"
      identity    = local.ca_discord_identity
    },
    {
      name        = local.ca_discord_secrets[var.s_LOGTAIL-DATABASE]
      keyVaultUrl = "${local.vault_uri}${var.s_LOGTAIL-DATABASE}"
      identity    = local.ca_discord_identity
    }
  ]

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

  scale = {
    minReplicas = 1
    maxReplicas = 1
  }

  depends_on = [azurerm_role_assignment.discord_secrets]
}

# need to remove dashes and lower case the name of the secrets
locals {
  ca_notify_secrets = {
    (var.s_DB-URI)           = lower(replace(azurerm_key_vault_secret.secrets[var.s_DB-URI].name, "-", ""))
    (var.s_LOGTAIL-NOTIFY)   = lower(replace(azurerm_key_vault_secret.secrets[var.s_LOGTAIL-NOTIFY].name, "-", ""))
    (var.s_LOGTAIL-DATABASE) = lower(replace(azurerm_key_vault_secret.secrets[var.s_LOGTAIL-DATABASE].name, "-", ""))
  }
  ca_notify_identity = azurerm_user_assigned_identity.ids[var.notify].id
}

# Container App: Notify
module "container_app_notify" {
  source = "./modules/container-app"

  name          = "${var.name}-notify"
  resource-id   = azurerm_resource_group.containers.id
  location      = var.location
  environmentId = azapi_resource.containerapp_environment.id
  identity-id   = local.ca_notify_identity

  acr-login_server = azurerm_container_registry.acr.login_server

  container = {
    image   = local.ch_image
    cpu     = 1
    memory  = "2Gi"
    command = ["python3", "chsystem/notify/notify.py"]
  }

  secrets = [
    {
      name        = local.ca_notify_secrets[var.s_DB-URI]
      keyVaultUrl = "${local.vault_uri}${var.s_DB-URI}"
      identity    = local.ca_notify_identity
    },
    {
      name        = local.ca_notify_secrets[var.s_LOGTAIL-NOTIFY]
      keyVaultUrl = "${local.vault_uri}${var.s_LOGTAIL-NOTIFY}"
      identity    = local.ca_notify_identity
    },
    {
      name        = local.ca_notify_secrets[var.s_LOGTAIL-DATABASE]
      keyVaultUrl = "${local.vault_uri}${var.s_LOGTAIL-DATABASE}"
      identity    = local.ca_notify_identity
    }
  ]

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

  scale = {
    minReplicas = 1
    maxReplicas = 1
  }

  depends_on = [azurerm_role_assignment.notify_secrets]
}
