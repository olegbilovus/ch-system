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
