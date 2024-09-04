output "container_app_url" {
  description = "The URL to access the container app"
  value       = azurerm_container_group.app.ip_address
}
