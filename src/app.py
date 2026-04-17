import asyncio
import aiocoap
import aiocoap.resource as resource
# import json
import cbor2 as cbor
import pycoreconf

from common import defs

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sid_file = "./src/model/temperature.sid"
ccm = pycoreconf.CORECONFModel(sid_file, model_description_file=None)

class ExampleResource(resource.Resource):
  def exampleTask(self):
    return b"task done!"

  async def render_fetch(self, request: aiocoap.Message) -> aiocoap.Message:
    logger.info(f"FETCH request from client {request.remote}")
    logger.info(f"Payload: {request.payload}")

    if request.payload.decode() == defs.SENSOR_NAME:
      payload_object = {60002: self.exampleTask()}
      logger.info(f"FETCH payload: {payload_object}")
      payload = cbor.dumps(payload_object)
    else:
      logger.error("FETCH error: Invalid payload")
      payload = cbor.dumps({60002: "Invalid payload"})

    return aiocoap.Message(payload=payload, content_format=42)

async def main():
  root = resource.Site()

  root.add_resource([defs.SIDS["temperature:interface/sensor"]], ExampleResource())

  await aiocoap.Context.create_server_context(root, bind=(defs.HOST, defs.PORT))

  await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
  asyncio.run(main())