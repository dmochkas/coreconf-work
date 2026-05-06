import socket
from scapy.all import *

from base import CoAPBase
from packet.coap_packet import *

# Ping message
message = raw(createCORECONFMessage(CoAPMsg.Reliability.CON, CoAPMsg.MessageType.PING))

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

try:
  sock.sendto(message, (CoAPBase.APP_IP, CoAPBase.PORT))
finally:
  print("[+] Message sent.")

data, addr = sock.recvfrom(1024)

if data:
  print(f"[+] Response received from {addr}!")