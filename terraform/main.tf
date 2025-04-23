terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.90.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "4.1.0"
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
