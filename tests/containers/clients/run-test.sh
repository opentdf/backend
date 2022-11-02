#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
npm install
pip3 install --requirement requirements.txt || true
python3 xtest.py --attrtest