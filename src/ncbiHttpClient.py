import urllib2
import re
import sys
import time
import os
import glob
from urllib2 import Request, urlopen, URLError, HTTPError
from lxml import etree
from io import StringIO, BytesIO

bpLinearDNA = 3800000
retMax = '100'
retStart = '0'

# --- HTTP request - response to get XML
def sendRequest(url):
	req = urllib2.Request(url)
	retries = 1
	established = False
	while not established:
		try:
			response = urllib2.urlopen(req)
			established = True
		except HTTPError as e:
			print 'The server couldn\'t handle the request.'
			print 'Error code: ', e.code
			waiting(retries)
			retries += 1
		except URLError as e:
			print 'Failed to reach a server.'
			print 'Reason: ', e.reason
			waiting(retries)
			retries += 1
		time.sleep(1)
	page = response.read()
	return page

def waiting(retries):
	print "%s. retry attempt..." %retries
	wait = retries * 2
	if wait > 60:
		wait = 60
	time.sleep(wait)

def esearchUrlBuilder(retStart, searchString):
	str(retStart)
	url_esearch = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore&term='+searchString+'&retmax=%s&retstart=%s' %(retMax, retStart)
	#url_esearch = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore&term=Xanthomonas+albilineans&retmax=%s&retstart=%s' %(retMax, retStart)
	return url_esearch

def esummaryUrlBuilder(fragmentedArray):
	url_esummary = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=nuccore&id='
	url_esummary += ','.join(fragmentedArray) #appending transformed string to url
	return url_esummary

def efetchUrlBuilder(fragmentedArray):
	url_efetch = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&rettype=fasta&retmode=text&id='
	url_efetch += ','.join(fragmentedArray)
	return url_efetch

def processStdInput():
	if len(sys.argv) == 0:
		print 'Usage: >python ncbiHttpClient.py <search string>'
	else:
		searchString = str(sys.argv[1])
		#searchString = re.sub(r"[^\w\s]", '', searchString) #Remove all non-word characters (everything except numbers and letters)
		#searchString = re.sub(r"\s+", '+', searchString) #Replace all runs of whitespace with a plus
		print 'Search term: %s' %searchString
		return searchString

def createFolder(searchString):
	#timestamp = time.strftime("%Y%m%d-%H:%M:%S")
	#path = '../fasta/'+searchString+'_'+timestamp+'/'
	
	path = '../fasta/'+searchString+'/'
	
	print 'Fasta files downloading to: %s' %(path)
	try: 
	    os.makedirs(path)
	except OSError:
	    if not os.path.isdir(path):
	    	raise
	return path

searchString = processStdInput()
path = createFolder(searchString)

# --- clear output files in folder
# TODO: ?ask user whether he wants to delete all files?
filelist = glob.glob(path+'*.fasta')
for f in filelist:
    os.remove(f)

elementArray = []
# --- get all the IDs/Gis for the search string
while True:
	url_esearch = esearchUrlBuilder(retStart, searchString)
	xmlroot = etree.XML(sendRequest(url_esearch)) #.XML() returns root node, .fromstring() as well
	count = int(xmlroot.find('Count').text)
	#print retStart, retMax, count

	for xmlchilds in xmlroot.iter('Id'):
		elementArray.append(xmlchilds.text)
	
	retStart = int(retStart)
	retMax = int(retMax)
	retStart += retMax
	if retStart > count:
		retStart = count

	print '%d datasets of %d for further processing downloaded' %(retStart, count)

	if(retStart == count):
		break

begin = 0
until = retMax
fragmentedArray = []
while True:
	#print 'range: %d' %(len(elementArray))
	for i in range(begin, until):
		#print 'iter inner loop %d: %s' %(i, elementArray[i])
		fragmentedArray.append(elementArray[i])
	begin += retMax
	until += retMax
	if until >= len(elementArray):
		until = len(elementArray)

	# --- build the ncbi esummary url request with the ids and send it
	url_esummary = esummaryUrlBuilder(fragmentedArray)
	xmlroot = etree.XML(sendRequest(url_esummary))

	# --- searching for 'bp linear DNA' values
	# --- in xml output it's attribute 'Length'
	del fragmentedArray[:]
	for xmlchilds in xmlroot.iter('Item'):
		if xmlchilds.get('Name') == 'Gi':
			fragmentedArray.append(xmlchilds.text)
		if xmlchilds.get('Name') == 'Length':
			if int(xmlchilds.text) < bpLinearDNA:
				fragmentedArray.pop()

	if len(fragmentedArray) > 0:
		# --- fetching fasta data
		url_efetch = efetchUrlBuilder(fragmentedArray)
		print 'url fetch: %s' %url_efetch
		del fragmentedArray[:]

		if os.path.exists(path+searchString+'.fasta'):
			if os.path.getsize(path+searchString+'.fasta') > 100000000000:
				tmpFiller = str(begin)
				with open(path+searchString+'_'+tmpFiller+'.fasta', 'ab') as f:
					f.write(sendRequest(url_efetch))
			else:
				with open(path+searchString+'.fasta', 'ab') as f:
					f.write(sendRequest(url_efetch))
		else:
			with open(path+searchString+'.fasta', 'w') as f:
				f.write(sendRequest(url_efetch))

	if begin > len(elementArray):
		break
