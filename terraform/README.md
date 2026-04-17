# Terraform

Placeholder for future infrastructure provisioning.

Recommended scope:

- server instance
- firewall/security group rules for `22`, `8080` or `443`, and `10051` if required externally
- DNS records
- backup storage

Keep application deployment in Ansible or Docker Compose unless infrastructure and application lifecycle are intentionally coupled.
