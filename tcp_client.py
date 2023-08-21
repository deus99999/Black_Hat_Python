import socket

target_host = "www.google.com"
target_port = 80


# IPv4 / TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((target_host, target_port))

# sent smth datas
client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# receive datas
response = client.recv(4096)
print(response.decode())
client.close()
