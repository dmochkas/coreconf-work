import aiocoap
from scapy.all import *
from enum import Enum

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# oscore_algorithm = aiocoap.oscore.AES_CCM_16_64_128()
# oscore_hashfun = aiocoap.oscore.hashfuncions["sha256"]

INNER_OPTIONS = [
  aiocoap.OptionNumber.IF_MATCH,
  aiocoap.OptionNumber.ETAG,
  aiocoap.OptionNumber.IF_NONE_MATCH,
  aiocoap.OptionNumber.OBSERVE,
  aiocoap.OptionNumber.LOCATION_PATH,
  aiocoap.OptionNumber.URI_PATH,
  aiocoap.OptionNumber.CONTENT_FORMAT,
  aiocoap.OptionNumber.MAX_AGE,
  aiocoap.OptionNumber.URI_QUERY,
  aiocoap.OptionNumber.ACCEPT,
  aiocoap.OptionNumber.LOCATION_QUERY,
  aiocoap.OptionNumber.BLOCK2,
  aiocoap.OptionNumber.BLOCK1,
  aiocoap.OptionNumber.SIZE2,
  aiocoap.OptionNumber.SIZE1,
  aiocoap.OptionNumber.NO_RESPONSE,
]
OUTER_OPTIONS = [
  aiocoap.OptionNumber.URI_HOST,
  aiocoap.OptionNumber.OBSERVE,
  aiocoap.OptionNumber.URI_PORT,
  aiocoap.OptionNumber.OSCORE,
  aiocoap.OptionNumber.MAX_AGE,
  aiocoap.OptionNumber.BLOCK2,
  aiocoap.OptionNumber.BLOCK1,
  aiocoap.OptionNumber.SIZE2,
  aiocoap.OptionNumber.PROXY_URI,
  aiocoap.OptionNumber.PROXY_SCHEME,
  aiocoap.OptionNumber.SIZE1,
  aiocoap.OptionNumber.NO_RESPONSE,
]

def buildPacket(message: aiocoap.Message) -> bytes:
  # if not message.opt.get_option(aiocoap.OptionNumber.OSCORE):
  #   logger.error("No OSCORE. Returning message bytes.")
  #   return message.encode()

  real_code = message.code

  if message.code.is_request(): # If request, POST w/o Observe and FETCH w/ Observe
    dummy_code = aiocoap.Code.FETCH if message.opt.get_option(aiocoap.OptionNumber.OBSERVE) else aiocoap.Code.POST
  elif message.code.is_response(): # If response, CHANGED w/o Observe and CONTENT w/ Observe
    dummy_code = aiocoap.Code.CONTENT if message.opt.get_option(aiocoap.OptionNumber.OBSERVE) else aiocoap.Code.CHANGED
  else: # If neither, use original
    dummy_code = message.code

  # Create messages
  outer_msg = aiocoap.Message(
    mtype=message.mtype, 
    mid=message.mid, 
    code=dummy_code, 
    token=message.token,

    # Options
    uri_port=message.opt.uri_port,
    oscore=message.opt.oscore
  )
  inner_msg = aiocoap.Message(
    mtype=message.mtype, 
    mid=0x0000, 
    code=real_code, 
    token=b"", 
    payload=message.payload,

    # Options
    uri_path="c"
  )

  # Check options
  # logger.info("Checking message options...")

  # outer_msg.opt.uri_host = message.opt.get_option(aiocoap.OptionNumber.URI_HOST)
  # outer_msg.opt.observe = message.opt.get_option(aiocoap.OptionNumber.OBSERVE)
  # outer_msg.opt.uri_port = message.opt.uri_port
  # outer_msg.opt.oscore = message.opt.oscore
  # outer_msg.opt.max_age = message.opt.get_option(aiocoap.OptionNumber.MAX_AGE)
  # outer_msg.opt.block2 = message.opt.get_option(aiocoap.OptionNumber.BLOCK2)
  # outer_msg.opt.block1 = message.opt.get_option(aiocoap.OptionNumber.BLOCK1)
  # outer_msg.opt.size2 = message.opt.get_option(aiocoap.OptionNumber.SIZE2)
  # outer_msg.opt.proxy_uri = message.opt.get_option(aiocoap.OptionNumber.PROXY_URI)
  # outer_msg.opt.proxy_scheme = message.opt.get_option(aiocoap.OptionNumber.PROXY_SCHEME)
  # outer_msg.opt.size1 = message.opt.get_option(aiocoap.OptionNumber.SIZE1)
  # outer_msg.opt.no_response = message.opt.get_option(aiocoap.OptionNumber.NO_RESPONSE)

  # inner_msg.opt.if_match = message.opt.get_option(aiocoap.OptionNumber.IF_MATCH)
  # inner_msg.opt.etag = message.opt.get_option(aiocoap.OptionNumber.ETAG)
  # inner_msg.opt.if_none_match = message.opt.get_option(aiocoap.OptionNumber.IF_NONE_MATCH)
  # inner_msg.opt.observe = message.opt.get_option(aiocoap.OptionNumber.OBSERVE)
  # inner_msg.opt.location_path = message.opt.get_option(aiocoap.OptionNumber.LOCATION_PATH)
  # inner_msg.opt.uri_path = message.opt.uri_path
  # inner_msg.opt.content_format = message.opt.get_option(aiocoap.OptionNumber.CONTENT_FORMAT)
  # inner_msg.opt.max_age = message.opt.get_option(aiocoap.OptionNumber.MAX_AGE)
  # inner_msg.opt.uri_query = message.opt.get_option(aiocoap.OptionNumber.URI_QUERY)
  # inner_msg.opt.accept = message.opt.get_option(aiocoap.OptionNumber.ACCEPT)
  # inner_msg.opt.location_query = message.opt.get_option(aiocoap.OptionNumber.LOCATION_QUERY)
  # inner_msg.opt.block2 = message.opt.get_option(aiocoap.OptionNumber.BLOCK2)
  # inner_msg.opt.block1 = message.opt.get_option(aiocoap.OptionNumber.BLOCK1)
  # inner_msg.opt.size2 = message.opt.get_option(aiocoap.OptionNumber.SIZE2)
  # inner_msg.opt.size1 = message.opt.get_option(aiocoap.OptionNumber.SIZE1)
  # inner_msg.opt.no_response = message.opt.get_option(aiocoap.OptionNumber.NO_RESPONSE)

  # logger.info("Finished options.")

  # Trim inner message
  inner_msg_bytes = inner_msg.encode()
  inner_msg_bytes = bytes([inner_msg_bytes[1]]) + inner_msg_bytes[4:] # Trim inner message (remove first byte and MID)
  logger.info(f"Inner message bytes: {inner_msg_bytes}")

  # security_ctx = aiocoap.oscore.CanProtect()

  outer_msg.payload = inner_msg_bytes

  # Return scapy packet
  return outer_msg.encode()