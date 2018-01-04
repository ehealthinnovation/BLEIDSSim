#!/bin/bash
 
while getopts ":a" opt; do
  case $opt in
    a)
        if [ -e history ]
	then
    	  echo "Clearing history file"
	  eval "truncate -s 0 history"
	else
   	  echo "Creating empty history file"
	  eval "touch history"
	fi
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done

#if history file does not exist, create it
if [ ! -e history ]; then
  echo "Creating empty history file"
  eval "touch history"
fi

sudo /etc/init.d/bluetooth restart
rm -rf *.pyc
rm -rf __pycache__/
python app.py


