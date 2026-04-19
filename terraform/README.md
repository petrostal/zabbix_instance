# Terraform

Terraform manages Proxmox VM infrastructure. Application deployment remains in Ansible.

Current layout:

- `envs/prod/` - runnable Terraform root module for Proxmox.
- `modules/proxmox-cloudinit-vm/` - reusable cloud-init VM module.

## Workflow

1. Create or upload an Ubuntu cloud image into Proxmox storage.
2. Run Terraform to create the VM.
3. Run Ansible to deploy Zabbix into the VM.

For the current lab network, Proxmox does not have direct internet egress. Prefer pre-uploading the image and passing its file id to Terraform.

Example image id:

```text
local:iso/noble-server-cloudimg-amd64.img
```

## API Token

Terraform uses the Proxmox API. Create a token on Proxmox:

```bash
pveum user add terraform@pve --comment "Terraform automation"
pveum aclmod / -user terraform@pve -role Administrator
pveum user token add terraform@pve zabbix --privsep 0
```

Store the returned token as an environment variable on the control machine:

```bash
export PROXMOX_VE_API_TOKEN='terraform@pve!zabbix=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
```

For production, use a narrower custom role instead of `Administrator`.

## Apply

```bash
cd terraform/envs/prod
terraform init
terraform plan
terraform apply
```

Then deploy Zabbix:

```bash
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-zabbix.yml
```
