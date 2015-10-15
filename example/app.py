from gevent import monkey
monkey.patch_all()

import time
from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, \
    close_room, disconnect

# imports genCrawler --->
import urllib2
import os
import re
import sys
import time
import glob
import subprocess
from urllib2 import Request, urlopen, URLError, HTTPError
from lxml import etree
from io import StringIO, BytesIO
# <--- imports genCrawler


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        time.sleep(10)
        count += 1
        #socketio.emit('my response',
                     #{'data': 'Server generated event', 'count': count},
                      #namespace='/test')


@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.start()
    return render_template('index.html')


@socketio.on('my event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          'count': session['receive_count']})


@socketio.on('close room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my room event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


@socketio.on('crawling', namespace='/test')
def crawl(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Your search term: '+message['searchString']+', bp: '+message['bp'],
         'count': session['receive_count']})

    if message['searchString'] == '':
        print 'empty string'
        emit('my response',
         {'data': 'Your search term is empty. Job aborted.',
         'count': session['receive_count']})
        return

    # --- | globals | ---------------------------------+
    defaultBP = 3800000
    retMax = '100'
    retStart = '0'
    searchString = str(message['searchString'])
    searchString = re.sub(r"[^\w\s]", '', searchString) # remove all non-word characters (everything except numbers and letters)
    searchString = re.sub(r"\s+", '+', searchString) # replace all runs of whitespace with a plus
    path = createFolder(searchString)

    if message['bp'] != '':
        defaultBP = checkBP(int(message['bp']), defaultBP)

    elementArray = []
    # --- get all the IDs/Gis for the search string
    while True:
        url_esearch = esearchUrlBuilder(retStart, retMax, searchString)
        xmlroot = etree.XML(sendRequest(url_esearch)) #.XML() returns root node, .fromstring() as well
        count = int(xmlroot.find('Count').text)
        retStart = int(retStart)
        retMax = int(retMax)

        if retMax > count:
            retMax = count

        #print retStart, retMax, count

        for xmlchilds in xmlroot.iter('Id'):
            elementArray.append(xmlchilds.text)
        
        retStart += retMax
        if retStart > count:
            retStart = count

        print '%d datasets of %d for preprocessing downloaded' %(retStart, count)
        emit('my response',
            {'data': str(retStart)+ ' datasets of ' +str(count)+ ' downloaded',
            'count': session['receive_count']})

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
                if int(xmlchilds.text) < defaultBP:
                    fragmentedArray.pop()

        if len(fragmentedArray) > 0:
            # --- fetching fasta data
            url_efetch = efetchUrlBuilder(fragmentedArray)
            print 'url fetch: %s' %url_efetch
            emit('my response',
            {'data': 'url fetch: ' +url_efetch,
            'count': session['receive_count']})

            del fragmentedArray[:]

            if os.path.exists(path+searchString+'.fasta'):
                if os.path.getsize(path+searchString+'.fasta') > 10000000000:
                    tmpFiller = str(begin)
                    with open(path+searchString+'_'+tmpFiller+'.fasta', 'ab') as f:
                        f.write(sendRequest(url_efetch))
                else:
                    with open(path+searchString+'.fasta', 'ab') as f:
                        f.write(sendRequest(url_efetch))
            else:
                with open(path+searchString+'.fasta', 'w') as f:
                    f.write(sendRequest(url_efetch))
        #else:
            #print 'preprocessing finished, No datasets. A reason could be a too high bp or a wrong search term.'
            #emit('my response',
            #{'data': 'preprocessing finished, No datasets. A reason could be a too high bp or a wrong search term.',
            #'count': session['receive_count']})
            #return

        if begin > len(elementArray):
            print 'Fasta file downloaded.'
            emit('my response',
            {'data': 'Fasta file downloaded - starting antiSMASH.',
            'count': session['receive_count']})
            break

    runAntismash(path, searchString)


def checkBP(userBP, defaultBP):
    print 'local bp: %d, global bp: %d' %(userBP, defaultBP)
    if userBP != defaultBP:
        defaultBP = userBP
    return defaultBP
             
def esearchUrlBuilder(retStart, retMax, searchString):
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
        time.sleep(0.2)
    page = response.read()
    return page

def waiting(retries):
    print "%s. retry attempt..." %retries
    wait = retries * 2
    if wait > 60:
        wait = 60
    time.sleep(wait)

def createFolder(searchString):
    timestamp = time.strftime("%Y%m%d-%H_%M_%S")
    path = '../fasta/'+searchString+'_'+timestamp+'/'
    #path = '../fasta/'+searchString+'/'
    print 'Fasta files downloading to: %s' %(path)
    try: 
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

    # --- remove existing fasta files
    filelist = glob.glob(path+'*.fasta')
    for f in filelist:
        os.remove(f)
    return path

def runAntismash(path, searchString):
    print 'run_antismash %s%s.fasta ../out' %(path, searchString)
    emit('my response',
    {'data': 'antiSMASH running...',
    'count': session['receive_count']})

    # --- http://www.cyberciti.biz/faq/python-run-external-command-and-get-output/
    cmd = 'run_antismash '+path+''+searchString+'.fasta ../out --inclusive --full-hmmer --borderpredict'
    #cmd = 'ls -al'
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    print "Command output : ", output
    print "Command exit status/return code : ", p_status

    if p_status != 0:
        emit('my response',
        {'data': 'antiSMASH run not successful.',
        'count': session['receive_count']})
    else:
        emit('my response',
        {'data': 'antiSMASH run successfully completed.',
        'count': session['receive_count']})





if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3333)
