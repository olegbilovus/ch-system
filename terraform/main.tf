terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.90.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "4.0.5"
    }
    azapi = {
      source  = "azure/azapi"
      version = "1.12.0"
    }
  }

  required_version = ">= 1.7.3"
}

provider "azurerm" {
  features {}
}

provider "tls" {}

provider "azapi" {
}

resource "random_string" "random_suffix" {
  length  = 5
  special = false
  upper   = false
  keepers = {
    # need to change the seed value when creating again some resource like KeyVault
    # because it reserves the FQDN for some days after deleting the resource
    seed = 1
  }
}

locals {
  rnd_str = random_string.random_suffix.result
}

################ Network #####################################
# RG
resource "azurerm_resource_group" "network" {
  name     = "${var.name}-network"
  location = var.location
}

# vnet
resource "azurerm_virtual_network" "chsystem" {
  name                = "chsystem"
  address_space       = ["10.0.0.0/16"]
  location            = var.location
  resource_group_name = azurerm_resource_group.network.name
}

# subnets
resource "azurerm_subnet" "vm" {
  name                 = "vm"
  resource_group_name  = azurerm_resource_group.network.name
  virtual_network_name = azurerm_virtual_network.chsystem.name
  address_prefixes     = ["10.0.2.0/24"]
}

resource "azurerm_subnet" "postgres" {
  name                 = "postgres"
  resource_group_name  = azurerm_resource_group.network.name
  virtual_network_name = azurerm_virtual_network.chsystem.name
  address_prefixes     = ["10.0.3.0/24"]
  service_endpoints    = ["Microsoft.Storage"]

  delegation {
    name = "fs"
    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

resource "azurerm_subnet" "container" {
  name                 = "container"
  resource_group_name  = azurerm_resource_group.network.name
  virtual_network_name = azurerm_virtual_network.chsystem.name
  address_prefixes     = ["10.0.4.0/24"]
  service_endpoints    = ["Microsoft.KeyVault"]

  delegation {
    name = "Microsoft.App.environments"
    service_delegation {
      name = "Microsoft.App/environments"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

################ VM #########################################

# RG
resource "azurerm_resource_group" "vm" {
  name     = "${var.name}-vm"
  location = var.location
}

# network security group
resource "azurerm_network_security_group" "nsg" {
  name                = "nsg"
  location            = var.location
  resource_group_name = azurerm_resource_group.vm.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# public ip
resource "azurerm_public_ip" "vm" {
  name                = "vm_ip"
  resource_group_name = azurerm_resource_group.vm.name
  location            = var.location
  allocation_method   = "Dynamic"
  domain_name_label   = "${var.name}-${local.rnd_str}"
}

# network interface
resource "azurerm_network_interface" "vm" {
  name                = "vm"
  location            = var.location
  resource_group_name = azurerm_resource_group.vm.name


  ip_configuration {
    name                          = "vm"
    subnet_id                     = azurerm_subnet.vm.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.vm.id
  }
}

# Connect the security group to the network interface
resource "azurerm_network_interface_security_group_association" "ni_nsg" {
  network_interface_id      = azurerm_network_interface.vm.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}

# Connect the security group to the internal subnet
resource "azurerm_subnet_network_security_group_association" "nsg-vm_internal" {
  subnet_id                 = azurerm_subnet.vm.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}

# ssh key
resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = "4096"
}

# save ssh private key
resource "local_file" "private_key" {
  content         = tls_private_key.ssh.private_key_pem
  filename        = "chsystem.pem"
  file_permission = "0600"
}

# The VM
resource "azurerm_linux_virtual_machine" "vm" {
  name                = "vm"
  resource_group_name = azurerm_resource_group.vm.name
  location            = var.location
  size                = "Standard_B1s"
  admin_username      = var.vm_user
  network_interface_ids = [
    azurerm_network_interface.vm.id,
  ]

  admin_ssh_key {
    username   = var.vm_user
    public_key = chomp(tls_private_key.ssh.public_key_openssh)
  }

  os_disk {
    storage_account_type = "Standard_LRS"
    caching              = "None"
    disk_size_gb         = 64
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  depends_on = [local_file.private_key]
}

########## PostgreSQL #########################################

# RG
resource "azurerm_resource_group" "db" {
  name     = "${var.name}-postgres"
  location = var.location
}

# DNS
resource "azurerm_private_dns_zone" "db" {
  name                = "${var.name}-${local.rnd_str}.private.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.db.name
}

# connect dns with vnet
resource "azurerm_private_dns_zone_virtual_network_link" "db" {
  name                  = "${var.name}-${local.rnd_str}-vnetlink.com"
  private_dns_zone_name = azurerm_private_dns_zone.db.name
  virtual_network_id    = azurerm_virtual_network.chsystem.id
  resource_group_name   = azurerm_resource_group.db.name
  depends_on            = [azurerm_subnet.postgres]
}

# PostgreSQL
resource "azurerm_postgresql_flexible_server" "db" {
  name                   = "${var.name}${local.rnd_str}"
  resource_group_name    = azurerm_resource_group.db.name
  location               = var.location
  version                = "16"
  delegated_subnet_id    = azurerm_subnet.postgres.id
  private_dns_zone_id    = azurerm_private_dns_zone.db.id
  administrator_login    = var.PG_USER
  administrator_password = var.PG_PASS
  zone                   = 2
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"
  depends_on = [
    azurerm_private_dns_zone_virtual_network_link.db,
    azurerm_linux_virtual_machine.vm
  ]

  connection {
    type            = "ssh"
    target_platform = "unix"
    user            = var.vm_user
    private_key     = tls_private_key.ssh.private_key_pem
    host            = azurerm_public_ip.vm.fqdn
  }

  provisioner "file" {
    source      = var.PG_INIT_SCRIPT
    destination = var.PG_INIT_SCRIPT
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt -qq update && sudo apt -qq install postgresql-client-common postgresql-client -y",
      "export PGPASSWORD=${var.PG_PASS}",
      "psql -h ${self.fqdn} -U ${var.PG_USER} -c \"CREATE ROLE ${var.PG_CH_USER} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION PASSWORD '${var.PG_CH_PASS}';\"",
      "psql -h ${self.fqdn} -U ${var.PG_USER} -c 'CREATE DATABASE ${var.name};'",
      "psql -h ${self.fqdn} -U ${var.PG_USER} -d ${var.name} -f ${var.PG_INIT_SCRIPT}",
      "psql -h ${self.fqdn} -U ${var.PG_USER} -d ${var.name} -c 'GRANT USAGE ON SCHEMA public TO ${var.PG_CH_USER};'",
      "psql -h ${self.fqdn} -U ${var.PG_USER} -d ${var.name} -c 'GRANT ALL ON ALL TABLES IN SCHEMA public TO ${var.PG_CH_USER};'",
      "psql -h ${self.fqdn} -U ${var.PG_USER} -d ${var.name} -c 'GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO ${var.PG_CH_USER};'"
    ]
  }
}

############# Azure Key Vault ####################################################
data "azurerm_client_config" "current" {}

# RG
resource "azurerm_resource_group" "keyvault" {
  name     = "${var.name}-vault"
  location = var.location
}

# Key Vault
resource "azurerm_key_vault" "keyvault" {
  name                       = "${var.name}-${local.rnd_str}-vault"
  location                   = var.location
  resource_group_name        = azurerm_resource_group.keyvault.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  enable_rbac_authorization  = true
  sku_name                   = "standard"

  network_acls {
    bypass                     = "AzureServices"
    default_action             = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.container.id]
    ip_rules                   = [var.myip]
  }

  # Assign yourself as Key Vault Admin
  provisioner "local-exec" {
    command = "az role assignment create --assignee \"${var.AZ_ObjectID}\" --role \"Key Vault Administrator\" --scope \"${self.id}\""
  }
}

# Managed Identities
resource "azurerm_user_assigned_identity" "ids" {
  for_each            = toset([var.web, var.postgrest, var.discord, var.notify])
  location            = var.location
  name                = "${var.name}-${each.key}"
  resource_group_name = azurerm_resource_group.keyvault.name
}

# Secrets. 
# Need to assign yourself as KeyVault Admin from the portal or az cli. Terraform will inherit from the Collab role
resource "azurerm_key_vault_secret" "secrets" {
  for_each = {
    (var.s_DB-URI)           = "postgresql://${var.PG_CH_USER}:${var.PG_CH_PASS}@${azurerm_postgresql_flexible_server.db.fqdn}:5432/${var.name}",
    (var.s_PG-CH-USER)       = var.PG_CH_USER,
    (var.s_HOST)             = "Azure",
    (var.s_PWL-URL)          = var.PWL-URL,
    (var.s_PWL-PRIVATE-KEY)  = var.PWL-PRIVATE-KEY,
    (var.s_PWL-PUBLIC-KEY)   = var.PWL-PUBLIC-KEY,
    (var.s_DISCORD-TOKEN)    = var.DISCORD-TOKEN,
    (var.s_LOGTAIL-DISCORD)  = var.LOGTAIL-DISCORD,
    (var.s_LOGTAIL-DATABASE) = var.LOGTAIL-DATABASE,
    (var.s_LOGTAIL-NOTIFY)   = var.LOGTAIL-NOTIFY,
    (var.s_LOGTAIL-WEB)      = var.LOGTAIL-WEB,
  }

  name         = each.key
  value        = each.value == null ? "init" : each.value
  key_vault_id = azurerm_key_vault.keyvault.id
}

# web RBAC for Secrets
resource "azurerm_role_assignment" "web_secrets" {
  for_each = toset([
    var.s_LOGTAIL-WEB,
    var.s_HOST,
    var.s_PWL-URL,
    var.s_PWL-PRIVATE-KEY,
    var.s_PWL-PUBLIC-KEY
  ])

  scope                = azurerm_key_vault_secret.secrets[each.key].resource_versionless_id
  role_definition_name = var.RBAC_SECRET_USER
  principal_id         = azurerm_user_assigned_identity.ids[var.web].principal_id
}

# postgrest RBAC for Secrets
resource "azurerm_role_assignment" "postgrest_secrets" {
  for_each = toset([var.s_DB-URI, var.s_PG-CH-USER])

  scope                = azurerm_key_vault_secret.secrets[each.key].resource_versionless_id
  role_definition_name = var.RBAC_SECRET_USER
  principal_id         = azurerm_user_assigned_identity.ids[var.postgrest].principal_id
}

# discord RBAC for Secrets
resource "azurerm_role_assignment" "discord_secrets" {
  for_each = toset([
    var.s_DB-URI,
    var.s_DISCORD-TOKEN,
    var.s_LOGTAIL-DISCORD,
    var.s_LOGTAIL-DATABASE
  ])

  scope                = azurerm_key_vault_secret.secrets[each.key].resource_versionless_id
  role_definition_name = var.RBAC_SECRET_USER
  principal_id         = azurerm_user_assigned_identity.ids[var.discord].principal_id
}

# notify RBAC for Secrets
resource "azurerm_role_assignment" "notify_secrets" {
  for_each = toset([
    var.s_DB-URI,
    var.s_LOGTAIL-NOTIFY,
    var.s_LOGTAIL-DATABASE
  ])

  scope                = azurerm_key_vault_secret.secrets[each.key].resource_versionless_id
  role_definition_name = var.RBAC_SECRET_USER
  principal_id         = azurerm_user_assigned_identity.ids[var.notify].principal_id
}

################# Azure Container Registry ############################
# RG
resource "azurerm_resource_group" "containers" {
  name     = "${var.name}-containers"
  location = var.location
}

# Azure Container Registry
resource "azurerm_container_registry" "acr" {
  name                = "${var.name}${local.rnd_str}cr"
  resource_group_name = azurerm_resource_group.containers.name
  location            = var.location
  sku                 = "Standard"
  admin_enabled       = true
}

# ACR Task to build and push the image to ACR
resource "azurerm_container_registry_task" "build-image" {
  name                  = "${var.name}buildimage"
  container_registry_id = azurerm_container_registry.acr.id
  platform {
    os           = "Linux"
    architecture = "amd64"
  }
  docker_step {
    dockerfile_path      = "Dockerfile"
    context_path         = var.public-git-repo
    context_access_token = "None"
    image_names          = ["${var.name}:latest"]
  }
}

# Run the task, it will run only once even after doing another appy
resource "azurerm_container_registry_task_schedule_run_now" "build-image" {
  container_registry_task_id = azurerm_container_registry_task.build-image.id
}

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

# update POSTGREST-URL secrete value
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
