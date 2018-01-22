# Oblique
Oblique is a simple [Python 3](https://www.python.org/downloads/) asycio-based Client/Server protocol for establishing reverse tunnel connections.


### Terminology:

#### Server
The "Server" refers to the *Oblique Server* instance. This will bind to all network interfaces on a TCP port (default: 8000) and accepts connections from an *Oblique Client*. When a client connects, it informs the server of the type of *Listener* that should be created (TCP or UDP). All traffic is tunneled over the main TCP *Client-to-Server* connection.

#### Listener
The "Listener" is a server created and bound to the initial *Server* host on a randomly generated port. It should be accessible to devices within the Server's host network. When a Listener receives a connection, a random session ID is generated and a message is sent to the *Client* with the session ID to inform it that a new session has been. **There is no bound for listener connections** outside of operating system restrictions and UINT32_MAX (for session identifiers).

#### Client
The "Client" refers to the *Oblique Client* instance. **Clients and Listeners have a 1:1 ratio** such that one *Listener* is spawned for each *Client* connection. When the *Client* is informed of a new session being created (an endpoint connected to the client's assosciated *Listener*), it establishes a connection with the destination host/server assosciated with the same session ID. This connection repeats all session data.

#### Repeater
The "Repeater" is a client connection created by the *Client* to the user-provided destination. The destination should be a network service accessible by the client (internal or external). One *Repeater* is spawned for every connection to a *Listener*. Data sent to the *Listener* will be sent via a Data packet through the *Client-to-Server* connection along with the session ID. The *Client* will extract the data and forward it out the assosciated *Repeater*.

### Example Usage:

The *Oblique Server* will run on a publicly accessible VPS server `1.1.1.1:8000`. The client, an endpoint in a LAN with an IP `192.168.1.7`, wants to allow a remote administrator to access SSH on the address `192.168.1.21:22`.

#### Server:

    #!/usr/bin/env python3
    import asyncio
    import oblique
    
    @asyncio.coroutine
    def main(loop):
        server = oblique.create_server(port=8000, loop=loop)
        yield from server
    
    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(main(loop))
            loop.run_forever()
        finally:
            loop.close()

#### Client:

    #!/usr/bin/env python3
    import asyncio
    import oblique
    
    @asyncio.coroutine
    def main(loop):
        server = oblique.client("192.168.1.21", 22, "1.1.1.1", 8000, loop=loop)
        yield from server
    
    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(main(loop))
            loop.run_forever()
        finally:
            loop.close()

