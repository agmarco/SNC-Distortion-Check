provider "azurerm" {
  features {}

  subscription_id = "722e68bd-c817-42c1-81a5-3aa6d677e76a"
  client_id       = "8b285dac-02e1-40ab-b39d-1b51998c02f3"
  client_secret   = "pBv8Q~cWZTTjHaolurfw8D-yE3Xf0~zAhXhPidpe"
  tenant_id       = "09ab1730-e4d7-4fc7-873f-3b7386a0249c"
}


resource "azurerm_resource_group" "main" {
  name     = "distortioncheck_group"
  location = "eastus"
}

resource "azurerm_container_group" "app" {
  name                = "distortioncheck-container"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  container {
    name   = "app-container"
    image  = "mohhamedsamu/distortion_check:latest"
    cpu    = "1"
    memory = "1.5"
    ports {
      port     = 8000
      protocol = "TCP"
    }
    environment_variables = {
      DEBUG        = "${var.debug}"
      DATABASE_URL = "${var.database_url}"
      BASE_URL     = "${var.base_url}"
      PORT         = "${var.port}"
      REDIS_URL    = "${var.redis_url}"
    }
    commands = ["./post-backend.sh", "prod"]
  }
  tags = {
    environment = "production"
  }
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                         = "new-distortioncheckdb"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = "East US 2"
  administrator_login          = var.administrator_login
  administrator_password       = var.administrator_password
  sku_name                     = "B_Standard_B1ms"
  version                      = "12"
  storage_mb                   = 32768
  backup_retention_days        = 7
  geo_redundant_backup_enabled = false
  tags = {
    environment = "production"
  }
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "cirs"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
}

output "container_fqdn" {
  value = azurerm_container_group.app.ip_address
}
