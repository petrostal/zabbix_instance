#!/usr/bin/env sh
set -eu

TRUSTED_CIDR="${TRUSTED_CIDR:-172.30.0.0/16}"
PUBLIC_IFACE="${PUBLIC_IFACE:-ens18}"
PORTS="${PORTS:-8080,8443,10051}"

iptables -N DOCKER-USER 2>/dev/null || true

while iptables -D DOCKER-USER -i "${PUBLIC_IFACE}" -p tcp -m multiport --dports "${PORTS}" -s "${TRUSTED_CIDR}" -j RETURN 2>/dev/null; do :; done
while iptables -D DOCKER-USER -i "${PUBLIC_IFACE}" -p tcp -m multiport --dports "${PORTS}" -j DROP 2>/dev/null; do :; done

iptables -I DOCKER-USER 1 -i "${PUBLIC_IFACE}" -p tcp -m multiport --dports "${PORTS}" -s "${TRUSTED_CIDR}" -j RETURN
iptables -I DOCKER-USER 2 -i "${PUBLIC_IFACE}" -p tcp -m multiport --dports "${PORTS}" -j DROP
