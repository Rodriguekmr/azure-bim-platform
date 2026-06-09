terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = "35fd14af-3794-437d-a3ec-dc9f1f6d892c"
}
resource "azurerm_resource_group" "bim_rg" {
  name     = var.resource_group_name
  location = var.location
}
resource "azurerm_storage_account" "bim_storage" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.bim_rg.name
  location                 = azurerm_resource_group.bim_rg.location

  account_tier             = "Standard"
  account_replication_type = "LRS"
}
resource "azurerm_service_plan" "bim_plan" {
  name                = "bim-function-plan"
  resource_group_name = azurerm_resource_group.bim_rg.name
  location            = azurerm_resource_group.bim_rg.location

  os_type  = "Linux"
  sku_name = "Y1"
}
resource "azurerm_linux_function_app" "bim_function" {
  name                = var.function_app_name
  resource_group_name = azurerm_resource_group.bim_rg.name
  location            = azurerm_resource_group.bim_rg.location

  storage_account_name       = azurerm_storage_account.bim_storage.name
  storage_account_access_key = azurerm_storage_account.bim_storage.primary_access_key

  service_plan_id = azurerm_service_plan.bim_plan.id

  site_config {}
}