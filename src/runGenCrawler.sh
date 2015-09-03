#!/bin/bash

# --- Checking whether an argument passed
if [ $# -ne 1 ]; then
	echo ""
    echo "$0 - Usage: ./runGenCrawler <search term>"
    echo "As a whitespace please use '+'"
    exit 1
fi

name=$1 # assigns value from argv[1] in variable 'name'

echo "Starting NCBI download..."
python ncbiHttpClient.py $name
echo "NCBI download completed..."

fastaFiles=(Xant*.fasta)
echo "Number of fasta files found: ${#fastaFiles[@]}"

echo "Starting Antismash..."
for i in `seq 0 ${#fastaFiles[@]}`
do
	run_antismash ${fastaFiles[i]} ../out/ --inclusive --borderpredict --full-hmmer
done
echo "Antismash completed"
