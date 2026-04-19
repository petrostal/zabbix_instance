variable "proxmox_endpoint" {
  type        = string
  description = "Proxmox API endpoint, for example https://proxmox:8006/."
}

variable "proxmox_api_token" {
  type        = string
  description = "Proxmox API token in USER@REALM!TOKENID=SECRET format."
  sensitive   = true
  default     = null
}

variable "proxmox_insecure" {
  type    = bool
  default = true
}

variable "proxmox_ssh_username" {
  type    = string
  default = "root"
}

variable "proxmox_ssh_agent" {
  type    = bool
  default = false
}

variable "proxmox_ssh_private_key_file" {
  type      = string
  default   = null
  sensitive = true
}

variable "proxmox_ssh_node_address" {
  type        = string
  description = "Direct SSH address for the Proxmox node. The provider does not use ~/.ssh/config."
  default     = "172.30.193.18"
}

variable "proxmox_node_name" {
  type    = string
  default = "proxmox"
}

variable "ssh_public_key_files" {
  type        = list(string)
  description = "SSH public key files injected through cloud-init."
}

variable "vm_name" {
  type    = string
  default = "zabbix"
}

variable "vm_id" {
  type = number
}

variable "vm_tags" {
  type    = list(string)
  default = ["terraform", "zabbix"]
}

variable "vm_started" {
  type    = bool
  default = true
}

variable "vm_on_boot" {
  type    = bool
  default = true
}

variable "vm_qemu_guest_agent_enabled" {
  type        = bool
  description = "Enable only when qemu-guest-agent is installed in the guest image."
  default     = false
}

variable "vm_cpu_cores" {
  type    = number
  default = 4
}

variable "vm_cpu_type" {
  type    = string
  default = "x86-64-v2-AES"
}

variable "vm_memory_mb" {
  type    = number
  default = 8192
}

variable "vm_disk_datastore_id" {
  type    = string
  default = "local-lvm"
}

variable "vm_cloudinit_datastore_id" {
  type    = string
  default = "local-lvm"
}

variable "vm_cloud_image_file_id" {
  type        = string
  description = "Cloud image file id in Proxmox storage, for example local:iso/noble-server-cloudimg-amd64.img."
}

variable "vm_disk_size_gb" {
  type    = number
  default = 64
}

variable "vm_network_bridge" {
  type    = string
  default = "vmbr193"
}

variable "vm_ipv4_address" {
  type        = string
  description = "Cloud-init IPv4 address in CIDR format or dhcp."
}

variable "vm_ipv4_gateway" {
  type    = string
  default = "172.30.193.1"
}

variable "vm_dns_domain" {
  type    = string
  default = "work.work"
}

variable "vm_dns_servers" {
  type    = list(string)
  default = ["172.30.193.1"]
}

variable "vm_cloud_init_username" {
  type    = string
  default = "ubuntu"
}
