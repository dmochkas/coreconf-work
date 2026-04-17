import asyncio
import aiocoap
# import json
import cbor2 as cbor
import struct

from common import defs

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoAPClient:
  def __init__(self, host, port=defs.PORT):
    self.host = host
    self.port = port
    self.protocol = None

  async def connect(self):
    self.protocol = await aiocoap.Context.create_client_context()
    logger.info(f"CoAP client ready for {self.host}:{self.port}")

  async def fetch(self, path: str|None = None, request: aiocoap.Message|None = None):
    if path is None and request is None:
      logger.error("FETCH error: No path or request given!")
      return {"error": "No path or request"}
    
    if request is None:
      uri = f"coap://{self.host}:{self.port}/{path}"
      request = aiocoap.Message(code=aiocoap.FETCH, uri=uri)

    try:
      response = await self.protocol.request(request).response
      logger.info(f"FETCH {path}: {response.code}")

      if response.code.is_successful():
        return cbor.loads(response.payload)
      else:
        return {"error": str(response.code)}

    except Exception as e:
      logger.error(f"FETCH error: {e}")
      return {"error": str(e)}

async def main():
  client = CoAPClient(defs.HOST, defs.PORT)
  await client.connect()

  uri = f"coap://{defs.HOST}:{defs.PORT}/{defs.SIDS['temperature:interface/sensor']}"
  request = aiocoap.Message(
    code=aiocoap.FETCH,
    uri=uri,
    payload=defs.SENSOR_NAME.encode()
  )
  print(f"Getting resource {uri.encode()}")
  resources = await client.fetch(request=request)
  print(f"Resource response: {resources}")

if __name__ == "__main__":
  asyncio.run(main())