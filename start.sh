#!/usr/bin/env bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo mv candy_delivery.service /etc/systemd/system/
sudo systemctl start candy_delivery
sudo systemctl enable candy_delivery
