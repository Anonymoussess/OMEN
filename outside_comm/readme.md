# What we did 

In this project, we have two JavaScript files: `websocket-server.js` and `websocket-client.js`, which demonstrate communication between a WebSocket server and client using the `ws` library.

The `websocket-server.js` file represents the server-side code. It utilizes the `ws` library to create a WebSocket server and handle incoming connections. The server performs the following tasks:


1. Defines an object `too_many_status` that contains the most duplicate tcp func call unuseful. 
2. Defines a function `getNginxPid` to retrieve the Nginx process ID using the `ps` command. 
3. Run system tap to obtain all CC information
4. For each client connected,filter the CC information by its ip+port, and the video server PID.
6. For the filtered CC information, convert it to readable format and send it. Also supply clock synchronization signal.

On the other hand, the `websocket-client.js` file represents the client-side code. It establishes a WebSocket connection to the server and handles various events. The client performs the following tasks:

1. Declares an object `TCPStatusInfo` and initializes its properties——it contains all the useful CC state information that the abr will used.
2. sets up a WebSocket connection to the server.
3. Implements the clock synchronization process with the server.
5. Defines functions to handle different types of messages received from the server and performs actions based on the received message type.
   - func_call: just save to queue (Automaton shift will be done in the abr)
   - cwnd_info: update cwnd, Wmax, rtt value.
   - ca_state: forcefully set the automaton state
## How to use

To run the WebSocket server and client, follow these steps:

1. Install Node.js on your system if it is not already installed.
2. Install the required dependencies (in files) .
3. Start the WebSocket server by running the command: `sudo node websocket-server.js`.(sudo because its calls stap will need root)
4. copy the code in `websocket-client.js` to the `dash-if-reference-player`'s index.html (put in a \<script\> label).
5. access web by video server (like apache——nginx will get few CC func_call info, so lead to performance degradation )

## Additional Notes

- Ensure that the WebSocket server address and port specified in the client code (`websocket-client.js`) match the actual server address and port where the WebSocket server is running.
- The server code (`websocket-server.js`) assumes the presence of an Nginx(or apache, same as below) process and includes functionality to retrieve the Nginx process ID. Adjust the command in the `getNginxPid` function if you are using a different process or remove that functionality if not needed.

That's all! You are now ready to run the WebSocket server and client and observe the communication between them. Feel free to explore and modify the code to suit your requirements.