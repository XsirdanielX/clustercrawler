#!\Python27\python.exe

import zerorpc
import time

class HelloRPC(object):
    def hello(self, name):
    	time.sleep(5)
        return "RPC Backend: Echo: %s" % name

s = zerorpc.Server(HelloRPC())
s.bind("tcp://0.0.0.0:4242")
s.run()