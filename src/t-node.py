import aiocoap
import socket
from scapy.all import *

from base import CoAPBase
from packet.coap_packet import *

# Ping message
message = aiocoap.Message(
  mtype=aiocoap.CON,
  mid=0x1234,
  code=aiocoap.Code.PING,
  uri_path="c",               # Should be hidden
  uri_port=CoAPBase.PORT      # Should be shown
)

message_bytes = buildPacket(message)

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

try:
  sock.sendto(message_bytes, (CoAPBase.APP_IP, CoAPBase.PORT))
finally:
  print("[+] Message sent.")

data, addr = sock.recvfrom(1024)

if data:
  print(f"[+] Response received from {addr}!")