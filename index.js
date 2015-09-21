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



	var c = new zerorpc.Client();
	c.connect("tcp://127.0.0.1:4242");

	c.invoke("hello", "RPC", function(error, res, more) {
    	console.log(res);
	});







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
		console.log('Message from client: ' +data);
		client.emit('msg', 'Echo: ' +data);
		
	});
});
