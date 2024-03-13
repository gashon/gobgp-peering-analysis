#!/bin/bash

# This script is used to initialize the project directory with the data files from the VM.
# It assumes that the data files are located at the specified path on the VM.
vm_data_path="~/gobgp-peering-analysis/output"

set -e

if [[ $(basename $(pwd)) != "gobgp-peering-analysis" ]]; then
	echo "Run script from gobgp-peering-analysis dir"
	exit 1
fi

mkdir -p data
scp gashon@personal:$vm_data_path/as_names.txt gashon@personal:$vm_data_path/table.json $(pwd)/data
