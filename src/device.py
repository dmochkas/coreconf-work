import sys
import os

import aiocoap
import asyncio
import json
import cbor2 as cbor
import pprint
import pycoreconf

from base import CoAPBase

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CoAPClient(CoAPBase):
  def __init__(self, host: str, port: str|None=None):
    self.host = host
    self.port = port
    self.protocol = None

  async def init(self):
    logger.debug(f"[CoAPClient.init] Initializing CoAP client instance...")

    # Attempt to create CORECONF model
    try:
      self.model = pycoreconf.CORECONFModel(self.sid_file)
    except Exception as e:
      logger.exception(e)
      sys.exit(1)
    logger.debug(f"[CoAPClient.init] Created CORECONF model for SID file {self.sid_file}")

    # Create client context for requests
    self.protocol = await aiocoap.Context.create_client_context()

    # Get module SID for module-wide datastore request
    target_sid_1 = self.model.sids[f"/{self.module_name}:sensors/sensor"]
    target_sid_2 = self.model.sids[f"/{self.module_name}:characteristics"]
    target_sids = [target_sid_1, target_sid_2]

    # Request full datastore
    logger.debug(f"[CoAPClient.init] FETCHing all sub-leafs from SIDs {target_sids}")
    try:
      response = await self.FETCH("c?d=0", target_sids)
    except TimeoutError as e:
      logger.error("[CoAPClient.init] Failed to obtain datamodel response.")
      logger.exception(e)

    # Printing response data
    logger.debug(f"[CoAPClient.init] Datamodel response obtained!")
    logger.debug(f"[CoAPClient.init] Payload: {response.payload.hex()}")
    logger.debug(f"[CoAPClient.init] Payload size: {len(response.payload)} bytes")

    # Concatenating response into a single dict
    full_response = {}
    cbor_instance_list = cbor.loads(response.payload) # Loading full response into CBOR string
    # Response SHOULD be list of yang-instances, as per draft-ietf-core-comi-21
    for i, cbor_instance in enumerate(cbor_instance_list):
      logger.debug(f"[CoAPClient.init] Decoding payload instance {i}!")
      # pprint.pprint(instance)
      full_response |= cbor_instance # Concatenating to full_response dict

    logger.debug(f"[CoAPClient.init] Full datamodel response obtained. Printing.")
    pprint.pprint(full_response)

    # Attempt to load datastore with CORECONF string from response
    try:
      self.ds = self.model.create_datastore(full_response)
    except Exception as e:
      logger.error("[CoAPClient.init] Failed to create datastore from response. Possible bad response!")
      logger.exception(e)
      sys.exit(1)

    logger.info("[CoAPClient.init] Initialized client with datastore!")
    logger.info("[CoAPClient.init] Printing full datastore for verification...")
    pprint.pprint(json.loads(self.ds.to_json()))
    logger.debug("[CoAPClient.init] Client fully initialized!")

  def _remote(self) -> str:
    """
    Resolve remote name.
    """
    return f"{self.host}:{self.port}" if self.port else self.host

  def _request(self, path: str, payload: bytes) -> aiocoap.Message:
    # Create initial aiocoap request message
    req = aiocoap.Message(transport_tuning=aiocoap.Unreliable, code=aiocoap.FETCH, payload=payload)
    
    # Parse path and query, if query exists
    if '?' in path:
      p, q = path.split('?')
      req.opt.uri_path = p
      req.opt.uri_query = tuple(q.split('&'))
    else:
      req.opt.uri_path = path

    # Set remaining parameters
    req.opt.content_format = 141 # application/yang-identifier+cbor-seq
    req.opt.accept = 142 # application/yang-instances+cbor-seq
    req.unresolved_remote = self._remote()
    
    return req

  async def FETCH(self, xpath: str, payload: int|tuple):
    """
    Performs a CORECONF FETCH operation on specified XPath with specified payload object.
    Converts payload to CBOR encoded SID string before sending request.

    FETCH operation will get the data nodes corresponding to one or more SIDs, which are present in the payload.
    """

    logger.debug(f"[CoAPClient.FETCH] Attempting to FETCH path {payload} in resource </{xpath}>")

    # Dumps payload into CBOR string
    cbor_payload = cbor.dumps(payload)
    logger.debug(f"[CoAPClient.FETCH] Payload: {cbor_payload.hex()}")
    logger.debug(f"[CoAPClient.FETCH] Payload size: {len(cbor_payload)} bytes")

    # Create request from XPath and CBOR payload
    request = self._request(xpath, cbor_payload)
    try:
      response = await asyncio.wait_for(self.protocol.request(request).response, timeout=5.0)
    except TimeoutError as e:
      logger.error("[CoAPClient.FETCH] Failed to obtain FETCH response.")
      raise e

    # Return response
    if response:
      logger.debug("[CoAPClient.FETCH] Response obtained!")
    return response

  async def iPATCH(self, xpath: str, payload):
    """
    Performs a CORECONF iPATCH operation on specified XPath with specified payload object.
    Converts payload to CBOR encoded SID string before sending request.

    iPATCH operation will change, create or delete data corresponding to one or more SIDs, which are present in the payload.
    """
    
    logger.debug(f"[CoAPClient.iPATCH] Attempting to iPATCH content in resousrce </{xpath}>")
    pprint.pprint(payload, indent=4)

    # Dumps payload into CBOR string
    cbor_payload = cbor.dumps(payload)
    logger.debug(f"CoAPClient.iPATCH] Payload: {cbor_payload.hex()}")
    logger.debug(f"CoAPClient.iPATCH] Payload size: {len(cbor_payload)} bytes")

    # Create iPATCH (Code 7) request from XPath and CBOR payload
    request = self._request(xpath, cbor_payload)
    request.code = aiocoap.iPATCH
    try:
      response = await asyncio.wait_for(self.protocol.request(request).response, timeout=5.0)
    except TimeoutError as e:
      logger.error("CoAPClient.iPATCH Failed to obtain iPATCH response.")
      raise e
    
    if response:
      logger.debug("[CoAPClient.iPATCH] Response obtained!")
    return response