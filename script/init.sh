#!/bin/bash

vm_data_path="/home/cs249i-student/output"

set -e

if [[ $(basename $(pwd)) != "project1" ]]; then
	echo "Run script from project1 dir"
	exit 1
fi

mkdir -p data
scp cs249i-student@cs249i:$vm_data_path/as_names.txt cs249i-student@cs249i:$vm_data_path/table.json $(pwd)/data
