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
