import aiocoap
import aiocoap.oscore
from scapy.all import *

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oscore_algorithm = aiocoap.oscore.AES_CCM_16_64_128()
oscore_hashfun = aiocoap.oscore.hashfunctions["sha256"]

C1_KEY = bytes.fromhex("0102030405060708090a0b0c0d0e0f10")
C1_SALT = bytes.fromhex("9e7ca92223786340")

def buildPacket(
      security_ctx: aiocoap.oscore.FilesystemSecurityContext, 
      message: aiocoap.Message, 
      sender_id=None, 
      request_id: aiocoap.oscore.RequestIdentifiers|None=None
    ) -> bytes:
  """
  `request_id` consists of additional data required to unprotect a protected message.
  """

  # if not message.opt.get_option(aiocoap.OptionNumber.OSCORE):
  #   logger.error("No OSCORE. Returning message bytes.")
  #   return message.encode()

  if sender_id is None:
    sender_id = security_ctx.sender_id

  # Split messages
  outer_msg, inner_msg = security_ctx._split_message(message, request_id)

  outer_msg.code = message.code
  outer_msg.mid = message.mid
  outer_msg.mtype = message.mtype

  # Prepare parameters
  partial_iv_short = None
  partial_iv_source = None
  nonce = None

  protected = {}
  unprotected = {}

  # Get partial IV from associated data if present
  if request_id is not None:
    partial_iv_source, partial_iv_short = request_id.get_reusable_kid_and_piv()
  
  # If no associated data, generate partial IV. Else, reconstruct nonce from partial IV with AES_CCM
  if partial_iv_source is None:
    nonce, partial_iv_short = security_ctx._build_new_nonce(oscore_algorithm)
    partial_iv_source = sender_id
    unprotected[6] = partial_iv_short
  else:
    nonce = security_ctx._construct_nonce(
      partial_iv_short, partial_iv_source, oscore_algorithm
    )
  
  # Get unprotected parameters
  unprotected[4] = sender_id
  if message.code.is_request():
    request_id = aiocoap.oscore.RequestIdentifiers(
      sender_id,
      partial_iv_short,
      can_reuse_nonce=None,
      request_code=outer_msg.code
    )
  
  # Extract option data
  option_data, _ = security_ctx._compress(protected, unprotected, b"")
  outer_msg.opt.oscore = option_data

  # TODO Compress inner message using SCHC
  compressed_inner_msg = inner_msg

  # Encrypt compressed inner message
  external_aad = security_ctx._extract_external_aad(
    outer_msg, request_id, local_is_sender=True
  )

  aad = aiocoap.oscore.SymmetricEncryptionAlgorithm._build_encrypt0_structure(
    protected, external_aad
  )

  key = security_ctx._get_sender_key(outer_msg, external_aad, compressed_inner_msg, request_id)

  ciphertext = security_ctx.algorithm.encrypt(compressed_inner_msg, aad, key, nonce)
  _, protected_inner_msg = security_ctx._compress(protected, unprotected, ciphertext)

  # 
  outer_msg.payload = protected_inner_msg

  # Return scapy packet
  return outer_msg.encode(), request_id