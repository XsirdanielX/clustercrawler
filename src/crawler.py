#!\Python27\python.exe
import urllib2
import cgi
import os
import re
import sys
import time
from urllib2 import Request, urlopen, URLError, HTTPError
from lxml import etree
from io import StringIO, BytesIO

# --- | globals | ---------------------------------+
bpLinearDNA = 3800000
retMax = '100'
retStart = '0'
# -------------------------------------------------+
# --- | html form | -------------------------------+
form = cgi.FieldStorage() # instantiate only once!
searchString = form.getvalue('name')

# --- Avoid script injection escaping the user input
searchString = cgi.escape(searchString)

# --- program functions ------------------
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
		time.sleep(2)
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

print """\
Content-Type: text/html\n
<html>
<body>
	<p>The submitted search term was: "%s"</p>
""" % searchString

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

	print """\
	<p>%d datasets of %d for further processing downloaded</p>
	""" %(retStart, count)

	#print '%d datasets of %d for further processing downloaded' %(retStart, count)

	if(retStart == count):
		break



print """\
</body>
</html>
"""

#os.system("ncbiHttpClient.py %s" %name)

