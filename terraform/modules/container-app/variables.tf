variable "name" {
  type = string
}

variable "resource-id" {
  type = string
}

variable "location" {
  type = string
}

variable "environmentId" {
  type = string
}

variable "identity-id" {
  type = string
}

variable "acr-login_server" {
  type = string
}

variable "secrets" {
  type = list(object({
    name        = string
    keyVaultUrl = string
    identity    = string
  }))

  default = []
}

variable "container" {
  type = object({
    image   = string
    cpu     = number
    memory  = string
    command = list(string)
  })
}

variable "env" {
  type = list(object({
    name      = string
    secretRef = string
  }))

  default = []
}

variable "scale" {
  type = object({
    minReplicas = optional(number, 0)
    maxReplicas = optional(number, 1)
  })
  default = {}
}

variable "workload_profile_name" {
  default = "Consumption"
}

variable "ignore_missing_property" {
  type    = bool
  default = true
}

variable "response_export_values" {
  type    = list(string)
  default = ["properties.configuration.ingress.fqdn"]
}
