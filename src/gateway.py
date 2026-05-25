import aiocoap
import socket
from scapy.all import *

from base import CoAPBase
from packet.coap_packet import *

# Ping message
message = aiocoap.Message(
  mtype=aiocoap.ACK,
  mid=0x1234,
  code=aiocoap.Code.PONG
)

message_bytes = buildPacket(message)

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

try:
  sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
except OSError:
  pass

sock.bind(('::', CoAPBase.PORT))

print(f"Listening for CoAP packets on [{CoAPBase.APP_IP}]:{CoAPBase.PORT}...")

while True:
  data, addr = sock.recvfrom(1024)

  print(f"[+] Received packet from {addr}: {data}")
  print(f"[+]   Length: {len(data)}")

  if data:
    print(f"[+] Sending response ping to {addr}...")
    sock.sendto(message_bytes, addr)