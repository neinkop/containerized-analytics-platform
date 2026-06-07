#!/bin/bash
set -e

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pandas pyarrow
echo "Venv bereit. Aktivieren mit: source venv/bin/activate"
python3 download_data.py
