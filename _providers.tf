# Provider block to configure Google Provider 
provider "google" {
  project     = var.project_id
  region      = var.resource_region
  credentials = file("service_auth_key.json")
}