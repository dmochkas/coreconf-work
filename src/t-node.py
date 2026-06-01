import aiocoap
import aiocoap.oscore as oscore
import socket
from scapy.all import *

from base import CoAPBase
from packet.coap_packet import *

security_ctx = oscore.FilesystemSecurityContext(
  "./src/context_device/"
)

# Ping message
message = aiocoap.Message(
  mtype=aiocoap.CON,
  mid=0x1234,
  code=aiocoap.Code.POST,
  uri_path="c",               # Should be hidden
  uri_port=CoAPBase.PORT      # Should be shown
)
message.payload = b"Hello, World!"

message_bytes, request_id = buildPacket(security_ctx, message, b"\x01")

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

try:
  sock.sendto(message_bytes, (CoAPBase.APP_IP, CoAPBase.PORT))
finally:
  print("[+] Message sent.")

data, addr = sock.recvfrom(1024)

if data:
  print(f"[+] Response received from {addr}!")
  print(f"[+] Decoding response...")

  message_in = aiocoap.Message.decode(
    data
  )
  message_unprotected, _ = security_ctx.unprotect(message_in, request_id)
  
  print(f"[+] Payload: {message_unprotected.payload}")

security_ctx._destroy()