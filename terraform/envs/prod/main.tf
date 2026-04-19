data "local_file" "ssh_public_keys" {
  for_each = toset(var.ssh_public_key_files)
  filename = pathexpand(each.value)
}

module "zabbix_vm" {
  source = "../../modules/proxmox-cloudinit-vm"

  name                     = var.vm_name
  description              = "Zabbix server managed by Terraform"
  node_name                = var.proxmox_node_name
  vm_id                    = var.vm_id
  tags                     = var.vm_tags
  started                  = var.vm_started
  on_boot                  = var.vm_on_boot
  qemu_guest_agent_enabled = var.vm_qemu_guest_agent_enabled
  cpu_cores                = var.vm_cpu_cores
  cpu_type                 = var.vm_cpu_type
  memory_mb                = var.vm_memory_mb
  disk_datastore_id        = var.vm_disk_datastore_id
  cloudinit_datastore_id   = var.vm_cloudinit_datastore_id
  cloud_image_file_id      = var.vm_cloud_image_file_id
  disk_size_gb             = var.vm_disk_size_gb
  network_bridge           = var.vm_network_bridge
  ipv4_address             = var.vm_ipv4_address
  ipv4_gateway             = var.vm_ipv4_gateway
  dns_domain               = var.vm_dns_domain
  dns_servers              = var.vm_dns_servers
  cloud_init_username      = var.vm_cloud_init_username
  ssh_public_keys          = [for key in data.local_file.ssh_public_keys : trimspace(key.content)]
}
