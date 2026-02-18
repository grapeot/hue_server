#!/bin/bash
# Scan Rinnai heater ports

IP="192.168.180.177"

echo "=== Fast scan common ports ==="
sudo nmap -sS -Pn -T4 --top-ports 1000 "$IP"

echo ""
echo "=== Scan all ports (this may take a while) ==="
sudo nmap -sS -Pn -p- -T4 "$IP"
