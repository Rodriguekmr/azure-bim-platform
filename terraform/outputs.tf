output "resource_group" {
  value = azurerm_resource_group.bim_rg.name
}

output "storage_account" {
  value = azurerm_storage_account.bim_storage.name
}

output "function_app" {
  value = azurerm_linux_function_app.bim_function.name
}