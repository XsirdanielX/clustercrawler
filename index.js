var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var zerorpc = require("zerorpc")

var connectionCount = 0;

http.listen(3333, function(){
	console.log('genCrawler web interface listening on port :3333');
});

app.get('/', function(req, res){
	res.sendFile(__dirname + '/index.html');
});

app.get('/test', function(req, res){
	res.send('<h1>TEST Hello world TEST</h1>');
});

io.on('connect', function(client) {
	connectionCount++;
	console.log('new job, '+connectionCount+' jobs are running.');
	client.on('disconnect', function() {
		connectionCount--;
		console.log('Job aborted, '+connectionCount+' remaining jobs are running');
	});

	// --- join
	client.on('join', function(data) {
		client.emit('msg', 'Hello from genCrawler server');
	});
	
	// --- Message from client
	client.on('msg', function(data) {
		var rpcClient = new zerorpc.Client({timeout: 60, heartbeatInterval: 60000});
        rpcClient.connect("tcp://127.0.0.1:4242");
        rpcClient.on("error", function(error) {
        	console.error("RPC client error:", error);
        });

        // --- create a zerorpc server
        /*var rpcServer = new zerorpc.Server ({
        	sendReply: function(msg, reply) {
        		reply(null, "node zerorpc: from RPC backend: ", msg);
        		//console.log(msg);
        		client.emit('From Backend: ' +msg);
        	}
        })
        rpcServer.bind("tcp://0.0.0.0:4243");*/

        rpcClient.invoke("crawl", data, function(error, res, more) {
        	if(error) {
        		console.error("RPC invoke error:", error);
        		client.emit('RPC invoke error: ' +error);
        	}
        	else {
	        	console.log(res);
		        console.log('Message from client: ' +data);
		        client.emit('msg', 'Node.js: ' +res);
		    }
		});
    });

    // --- Message from server
    client.on('srvMsg', function(data) {
    	console.log('Message from server: ' +data);
    	client.emit('msg', 'Server message: ' +data);
    });
});
