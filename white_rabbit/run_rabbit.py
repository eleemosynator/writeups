from socket import create_connection

for c, p in zip('935', range(1337, 1340)):
    conn = create_connection(('127.0.0.1', p))
    conn.send(c)
    print conn.recv(1)
    conn.close

