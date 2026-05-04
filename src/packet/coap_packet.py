from scapy.all import *
from enum import Enum

src_ip = "2001:db10::10"
dst_ip = "2001:db8:1::10"
# dst_ip = "2001:db8:2::10"
src_port = 12345
dst_port = 5683

class MsgRel:
  CON = 0b00
  NON = 0b01
  ACK = 0b10
  RST = 0b11

class MType:
  PING   = 0b000_00000 # 0.00
  GET    = 0b000_00001 # 0.01
  POST   = 0b000_00010 # 0.02
  PUT    = 0b000_00011 # 0.03
  DELETE = 0b000_00100 # 0.04
  FETCH  = 0b000_00101 # 0.05
  PATCH  = 0b000_00110 # 0.06
  IPATCH = 0b000_00111 # 0.07

  CONTENT = 0b010_00101 # 2.05

class ResourceSelect(Enum):
  DS_RESOURCE = [0xb1, 0x63]

def createCORECONFMessage(reliability: int, mtype: int, options=[0xb1, 0x63], payload: bytes|None=None, mid=0x1234):
  
  coap_header = Raw(bytes([
    0b01_00_0000 | (reliability << 4),
    mtype,
    mid >> 8, mid & 0xff
  ]))

  coap_options = Raw(bytes(options))

  # Hexdump header and options
  print("=" * 72)
  print("\tCoAP Header Hexdump")
  print("      0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F   0123456789ABCDEF")
  hexdump(coap_header)
  print("-" * 72)
  print("\tCoAP Options Hexdump")
  print("      0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F   0123456789ABCDEF")
  hexdump(coap_options)

  CoAP_Message = coap_header / coap_options

  print("=" * 72)
  print("\tFull CoAP Message Hexdump")
  print("      0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F   0123456789ABCDEF")
  hexdump(CoAP_Message)
  print("=" * 72)

  packet = IPv6(src=src_ip, dst=dst_ip) / UDP(sport=src_port, dport=dst_port) / CoAP_Message

  if payload:
    # Add payload to end of packet here.
    packet = packet / Raw(b"\xff") / Raw(payload)

  print("\tFull Packet Hexdump")
  print("      0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F   0123456789ABCDEF")
  hexdump(packet)
  print("=" * 72)

  return packet

if __name__=="__main__":
  example_payload = bytes(b"sensors/01/t")

  print("1. CoAP 0.05 FETCH Message")
  createCORECONFMessage(MsgRel.CON, MType.FETCH, payload=example_payload)

  print("\n2. CoAP 0.07 iPATCH Message")
  createCORECONFMessage(MsgRel.NON, MType.IPATCH, payload=example_payload)

  print("\n3. CoAP 2.05 Content Message")
  createCORECONFMessage(MsgRel.ACK, MType.CONTENT, payload=example_payload)