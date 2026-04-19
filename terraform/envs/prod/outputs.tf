output "vm_id" {
  value = module.zabbix_vm.vm_id
}

output "vm_name" {
  value = module.zabbix_vm.name
}

output "vm_ipv4_addresses" {
  value = module.zabbix_vm.ipv4_addresses
}

output "ansible_inventory_hint" {
  value = <<EOT
all:
  children:
    zabbix_servers:
      hosts:
        ${var.vm_name}:
          ansible_host: ${split("/", var.vm_ipv4_address)[0]}
          ansible_user: ${var.vm_cloud_init_username}
EOT
}
