# Production Proxmox VM

This Terraform root creates one Ubuntu cloud-init VM on Proxmox.

## Prerequisites

Upload an Ubuntu cloud image to Proxmox storage as an ISO/content file. In this lab, Proxmox does not have internet egress, so upload from the control machine:

```bash
curl -L -o /tmp/noble-server-cloudimg-amd64.img \
  https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img

scp /tmp/noble-server-cloudimg-amd64.img \
  root@proxmox:/var/lib/vz/template/iso/noble-server-cloudimg-amd64.img
```

The resulting Terraform file id is:

```text
local:iso/noble-server-cloudimg-amd64.img
```

Create a Proxmox API token:

```bash
ssh root@proxmox 'pveum user add terraform@pve --comment "Terraform automation" || true'
ssh root@proxmox 'pveum aclmod / -user terraform@pve -role Administrator'
ssh root@proxmox 'pveum user token add terraform@pve zabbix --privsep 0'
```

Export the returned token:

```bash
export TF_VAR_proxmox_api_token='terraform@pve!zabbix=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
```

The provider also needs direct SSH access to the Proxmox node when importing a cloud image into a VM disk. It does not read `~/.ssh/config`, so set the node address and private key explicitly in `terraform.tfvars`:

```hcl
proxmox_ssh_node_address      = "172.30.193.18"
proxmox_ssh_private_key_file  = "~/.ssh/id_rsa"
```

## Configure

```bash
cd terraform/envs/prod
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

- `vm_id`
- `vm_name`
- `vm_ipv4_address`
- `vm_cloud_image_file_id`
- `ssh_public_key_files`

Keep `vm_qemu_guest_agent_enabled = false` for the stock Ubuntu cloud image unless you have baked `qemu-guest-agent` into the image. If it is enabled without the guest agent installed, Terraform can wait for the agent until timeout during VM creation.

## Run

```bash
terraform init
terraform plan
terraform apply
```

This root was tested against Proxmox `9.1.1` by creating VM `101` at `172.30.193.76`.

## Deploy Zabbix

After the VM is created:

```bash
cd ../../..
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-zabbix.yml
```

If the VM network does not have internet egress, use the proxy flow documented in `ansible/README.md`.
