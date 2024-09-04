variable "docker_username" {
  description = "Docker Hub username"
  type        = string
}

variable "debug" {
  description = "Debug mode"
  type        = string
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
}

variable "base_url" {
  description = "Base URL for the application"
  type        = string
}

variable "port" {
  description = "Port for the application"
  type        = string
}

variable "redis_url" {
  description = "Redis connection URL"
  type        = string
}

variable "administrator_login" {
  description = "Administrator login for PostgreSQL server"
  type        = string
}

variable "administrator_password" {
  description = "Administrator password for PostgreSQL server"
  type        = string
  sensitive   = true
}
