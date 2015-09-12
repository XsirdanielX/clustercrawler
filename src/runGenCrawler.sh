#!/bin/bash

# --- Checking whether an argument passed
if [ $# -ne 1 ]; then
	echo ""
    echo "$0 - Usage: ./runGenCrawler <search term>"
    echo "As a whitespace please use '+' instead"
    exit 1
fi

searchString=$1 # assigns value from argv[1] in variable 'name'

echo "Starting NCBI download..."
python ncbiHttpClient.py $searchString
echo "NCBI download completed..."

fastaFiles=(../fasta/$searchString/*.fasta)
#size=$(du -c ../fasta/$searchString/)
echo "Number of fasta files downloaded: ${#fastaFiles[@]}" #with size $size"

echo "Starting Antismash..."
range=${#fastaFiles[@]}
range=$((range-1))
for i in `seq 0 $range`
do
	run_antismash ${fastaFiles[i]} ../out/ --inclusive --borderpredict --full-hmmer
	#echo "$i files found: ${fastaFiles[i]}" 
done
echo "Antismash completed"

sshpass -p "...." scp ./out.log alexander.platz@sshgate.tu-berlin.de:~/public_html/genCrawler/