#!/bin/bash
 
cmd="clear"
$cmd
sudo /etc/init.d/bluetooth restart
rm -rf *.pyc
rm -rf __pycache__/
python3 app.py
