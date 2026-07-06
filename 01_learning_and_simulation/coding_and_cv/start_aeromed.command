#!/bin/bash
# Double-click this in Finder to launch the AeroMed demo hub — no typing.
cd "$(dirname "$0")"
.venv/bin/python hub.py &
sleep 1
open http://localhost:8080
wait
