import socket
from scapy.all import *

from base import CoAPBase
from packet.coap_packet import *

# Ping message
message = raw(createCORECONFMessage(CoAPMsg.Reliability.ACK, CoAPMsg.MessageType.PING))

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
sock.bind((CoAPBase.APP_IP, CoAPBase.PORT))

print(f"Listening for CoAP packets on [{CoAPBase.APP_IP}]:{CoAPBase.PORT}...")

while True:
  data, addr = sock.recvfrom(1024)

  print(f"[+] Received packet from {addr}: {data}")
  print(f"[+]   Length: {len(data)}")

  if data:
    print(f"[+] Sending response ping to {addr}...")
    sock.sendto(message, addr)