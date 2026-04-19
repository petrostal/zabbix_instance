variable "name" {
  type = string
}

variable "description" {
  type    = string
  default = "Managed by Terraform"
}

variable "node_name" {
  type = string
}

variable "vm_id" {
  type = number
}

variable "tags" {
  type    = list(string)
  default = ["terraform"]
}

variable "started" {
  type    = bool
  default = true
}

variable "on_boot" {
  type    = bool
  default = true
}

variable "qemu_guest_agent_enabled" {
  type    = bool
  default = false
}

variable "cpu_cores" {
  type    = number
  default = 4
}

variable "cpu_type" {
  type    = string
  default = "x86-64-v2-AES"
}

variable "memory_mb" {
  type    = number
  default = 8192
}

variable "disk_datastore_id" {
  type    = string
  default = "local-lvm"
}

variable "cloudinit_datastore_id" {
  type    = string
  default = "local-lvm"
}

variable "cloud_image_file_id" {
  type        = string
  description = "Proxmox storage file id for a cloud image, for example local:iso/noble-server-cloudimg-amd64.img."
}

variable "disk_size_gb" {
  type    = number
  default = 64
}

variable "network_bridge" {
  type = string
}

variable "ipv4_address" {
  type        = string
  description = "Cloud-init IPv4 address. Use CIDR format, for example 172.30.193.76/24, or dhcp."
}

variable "ipv4_gateway" {
  type    = string
  default = null
}

variable "dns_domain" {
  type    = string
  default = null
}

variable "dns_servers" {
  type    = list(string)
  default = []
}

variable "cloud_init_username" {
  type    = string
  default = "ubuntu"
}

variable "ssh_public_keys" {
  type = list(string)
}
