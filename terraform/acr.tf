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
