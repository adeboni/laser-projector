#!/bin/bash

cd /home/pi/laser-projector/2024/software/server
sclang synthdef.scd &
source .venv/bin/activate
DISPLAY=:0 python app.py
