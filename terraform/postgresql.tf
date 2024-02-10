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
