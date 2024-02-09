variable "name" {
  default = "chsystem"
}

variable "location" {
  default = "francecentral"
}

variable "vm_user" {
  default = "azureuser"
}

variable "AZ_ObjectID" {
  type        = string
  description = "The ObjectID of the user to which the higher permissions/roles will be assigned"
}

variable "PG_USER" {
  type        = string
  description = "PostgreSQL user"
  sensitive   = true
}

variable "PG_PASS" {
  type        = string
  description = "PostgreSQL password"
  sensitive   = true
}

variable "PG_INIT_SCRIPT" {
  default = "postgresql_ch.sql"
}

variable "PG_CH_USER" {
  type        = string
  description = "PostgreSQL user"
  sensitive   = true
}

variable "PG_CH_PASS" {
  type        = string
  description = "PostgreSQL password"
  sensitive   = true
}

variable "myip" {
  type      = string
  sensitive = true
}

variable "web" {
  default = "web"
}

variable "postgrest" {
  default = "postgrest"
}

variable "discord" {
  default = "discord"
}

variable "notify" {
  default = "notify"
}

variable "RBAC_SECRET_USER" {
  default = "Key Vault Secrets User"
}

variable "s_DB-URI" {
  default = "DB-URI"
}

variable "s_PG-PASS" {
  default = "PG-PASS"
}

variable "s_PG-CH-USER" {
  default = "PG-CH-USER"
}

variable "s_POSTGREST-URL" {
  default = "POSTGREST-URL"
}

variable "s_HOST" {
  default = "HOST"
}

variable "s_PWL-URL" {
  default = "PWL-URL"
}

variable "PWL-URL" {
  type        = string
  description = "The Passwordless URL"
  sensitive   = true
}

variable "s_PWL-PRIVATE-KEY" {
  default = "PWL-PRIVATE-KEY"
}

variable "PWL-PRIVATE-KEY" {
  type        = string
  description = "The Passwordless Private Key"
  sensitive   = true
}

variable "s_PWL-PUBLIC-KEY" {
  default = "PWL-PUBLIC-KEY"
}

variable "PWL-PUBLIC-KEY" {
  type        = string
  description = "The Passwordless Public Key"
  sensitive   = true
}

variable "s_DISCORD-TOKEN" {
  default = "DISCORD-TOKEN"
}

variable "DISCORD-TOKEN" {
  type        = string
  description = "The Discord Token"
  sensitive   = true
}

variable "s_LOGTAIL-DISCORD" {
  default = "LOGTAIL-DISCORD"
}

variable "LOGTAIL-DISCORD" {
  type        = string
  description = "The Logtail DISCORD Token"
  sensitive   = true
}

variable "s_LOGTAIL-DATABASE" {
  default = "LOGTAIL-DATABASE"
}

variable "LOGTAIL-DATABASE" {
  type        = string
  description = "The Logtail DATABASE Token"
  sensitive   = true
}

variable "s_LOGTAIL-NOTIFY" {
  default = "LOGTAIL-NOTIFY"
}

variable "LOGTAIL-NOTIFY" {
  type        = string
  description = "The Logtail NOTIFY Token"
  sensitive   = true
}

variable "s_LOGTAIL-WEB" {
  default = "LOGTAIL-WEB"
}

variable "LOGTAIL-WEB" {
  type        = string
  description = "The Logtail WEB Token"
  sensitive   = true
}

variable "public-git-repo" {
  type        = string
  description = "The URL to a public chsystem git repo"
  default     = "https://github.com/OB-UNISA/ch-system"
}

variable "workload_profile_name" {
  default = "Consumption"
}

variable "container-app_identity-type" {
  default = "UserAssigned"
}

variable "azapi_container-app-type" {
  default = "Microsoft.App/containerApps@2023-05-01"
}
