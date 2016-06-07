Cluster Crawler
==============

Short description
-----------------
This command line based script queries the NCBI nucleotide database with user
search terms and downloads a sequence in fasta format.
To limit the filesize and less useful information these downloaded sequences are 
within a base pair range (bpa).

Usage
-----
    python ncbiHttpClient_stdin.py
Then enter your search term for the NCBI database. E.g. "xanthomonas albilineans"

Further Development
-----------
This is still a command line script. In the "web-extension" branch, the first
steps of the transormation to a web-application were done. Any contribution in
further developments is very appreciated.
The goal then is to integrate a locally installed antismash and feed it with
the downloaded fasta-files for for the bioanalytics.
