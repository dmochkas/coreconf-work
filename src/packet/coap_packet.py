from scapy.all import *
from enum import Enum

class CoAPMsg:
  class Reliability(Enum):
    CON = (0b00 << 4)
    NON = (0b01 << 4)
    ACK = (0b10 << 4)
    RST = (0b11 << 4)

  class MessageType(Enum):
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
    DS_RESOURCE = [0xb1, 0x63] # URI-Path of length 1, "c"

def createCORECONFMessage(reliability: CoAPMsg.Reliability, mtype: CoAPMsg.MessageType, mid=0x1234, options=None, payload: bytes|None=None):
  
  coap_header = Raw(bytes([
    0b01_00_0000 | reliability.value,
    mtype.value,
    mid >> 8, mid & 0xff
  ]))

  packet = coap_header

  # If options were given, append options to message
  if options:
    coap_options = Raw(bytes(options))
    packet = packet / coap_options

  if payload:
    # Add payload to end of packet here.
    packet = packet / Raw(b"\xff") / Raw(payload)

  return packet

if __name__=="__main__":
  example_payload = bytes(b"sensors/01/t")

  print("\n" + "=" * 72)
  print("1. CoAP 0.05 FETCH Message")
  packet = createCORECONFMessage(CoAPMsg.Reliability.CON, CoAPMsg.MessageType.FETCH, options=CoAPMsg.ResourceSelect.DS_RESOURCE.value, payload=example_payload)
  print("\tFull Packet Hexdump")
  print("      0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F   0123456789ABCDEF")
  hexdump(packet)
  print("=" * 72)

  print("\n" + "=" * 72)
  print("2. CoAP 0.07 iPATCH Message")
  packet = createCORECONFMessage(CoAPMsg.Reliability.NON, CoAPMsg.MessageType.IPATCH, options=CoAPMsg.ResourceSelect.DS_RESOURCE.value, payload=example_payload)
  print("\tFull Packet Hexdump")
  print("      0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F   0123456789ABCDEF")
  hexdump(packet)
  print("=" * 72)

  print("\n" + "=" * 72)
  print("3. CoAP 2.05 Content Message")
  packet = createCORECONFMessage(CoAPMsg.Reliability.ACK, CoAPMsg.MessageType.CONTENT, options=CoAPMsg.ResourceSelect.DS_RESOURCE.value, payload=example_payload)
  print("\tFull Packet Hexdump")
  print("      0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F   0123456789ABCDEF")
  hexdump(packet)
  print("=" * 72)