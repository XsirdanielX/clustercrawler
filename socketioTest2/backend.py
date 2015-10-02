import zerorpc

class HelloRPC(object):
    def hello(self, name, cObject):

    	print "Client object: %s" %cObject
        return "Hello, %s. Client object:" %name

s = zerorpc.Server(HelloRPC())
s.bind("tcp://0.0.0.0:4242")
s.run()