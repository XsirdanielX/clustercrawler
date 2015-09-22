#!\Python27\python.exe
import zerorpc
import urllib2
import cgi
import os
import re
import sys
import time
from urllib2 import Request, urlopen, URLError, HTTPError
from lxml import etree
from io import StringIO, BytesIO

class Crawler(object):
	# --- | globals | ---------------------------------+
	bpLinearDNA = 3800000
	retMax = '100'
	retStart = '0'

	#TODO: Create python socket.io client to communicate with html view.
	#      Every print shall be a message from here via node.js server
	#      to the html view. The node.js server is already prepared.

	def crawl(self, searchString):
		elementArray = []
		# --- get all the IDs/Gis for the search string
		while True:
			url_esearch = self.esearchUrlBuilder(Crawler.retStart, Crawler.retMax, searchString)
			xmlroot = etree.XML(self.sendRequest(url_esearch)) #.XML() returns root node, .fromstring() as well
			count = int(xmlroot.find('Count').text)
			#print Crawler.retStart, Crawler.retMax, count

			for xmlchilds in xmlroot.iter('Id'):
				elementArray.append(xmlchilds.text)
			
			Crawler.retStart = int(Crawler.retStart)
			Crawler.retMax = int(Crawler.retMax)
			Crawler.retStart += Crawler.retMax
			if Crawler.retStart > count:
				Crawler.retStart = count

			print '%d datasets of %d for further processing downloaded' %(Crawler.retStart, count)

			if(Crawler.retStart == count):
				#break
				return '%d datasets of %d for further processing downloaded' %(Crawler.retStart, count)

	def esearchUrlBuilder(self, retStart, retMax, searchString):
		str(Crawler.retStart)
		url_esearch = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore&term='+searchString+'&retmax=%s&retstart=%s' %(Crawler.retMax, Crawler.retStart)
		#url_esearch = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore&term=Xanthomonas+albilineans&retmax=%s&retstart=%s' %(Crawler.retMax, Crawler.retStart)
		return url_esearch

    # --- program functions ------------------
	# --- HTTP request - response to get XML
	def sendRequest(self, url):
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












s = zerorpc.Server(Crawler())
s.bind("tcp://0.0.0.0:4242")
s.run()