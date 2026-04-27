import asyncio
import aiocoap
import aiocoap.resource as resource
import json
import cbor2 as cbor
import pprint
import pycoreconf

from base import CoAPBase

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generateFullData():
  sensors = [
    {
      "type": "temperature",
      "id": 0,
      "enabled": False,
      "unit": "°C",
      "quantity": {
        "value": 0
      },
      "timestamp": 0
    },
    {
      "type": "pressure",
      "id": 1,
      "enabled": False,
      "unit": "kPa",
      "quantity": {
        "value": 0
      },
      "timestamp": 0
    },
    {
      "type": "light",
      "id": 2,
      "enabled": False,
      "unit": "lux",
      "quantity": {
        "value": 0
      },
      "timestamp": 0
    }
  ]

  config = {
    "basic-sensor:characteristics": {
      "name": "Basic Sensor",
      "version": "1.0",
      "identifier": "basicsensor0"
    },
    "basic-sensor:sensors": {
      "sensor": sensors
    }
  }

  return config

class CoAPServer(CoAPBase):
  model = None
  datastore = None
  
  @classmethod
  def init(cls):
    cls.model = pycoreconf.CORECONFModel(cls.sid_file)

    config_data = generateFullData()
    cbor_data = cls.model.toCORECONF(config_data)

    cls.datastore = cls.model.create_datastore(cbor_data=cbor_data)

class DatastoreResource(resource.Resource):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  async def render_fetch(self, request: aiocoap.Message) -> aiocoap.Message:
    logger.info(f"[DatastoreResource.render_fetch] FETCH request from client {request.remote}")
    payload = cbor.loads(request.payload)
    logger.info(f"[DatastoreResource.render_fetch] Payload: {payload}")

    response = []
    for i, instance in enumerate(payload):
      # If instance is only SID
      if not isinstance(instance, (list, tuple)):
        xpath = CoAPServer.datastore._create_xpath(instance)
      # If instance is SID and keys
      elif len(instance) > 1:
        xpath = CoAPServer.datastore._create_xpath(instance[0], keys=instance[1:])
      
      full_xpath = f"{CoAPServer.module_name}:{xpath[1:]}"
      logger.info(f"[DatastoreResource.render_fetch] Payload instance {i} has XPath {full_xpath}")

      instance_response = CoAPServer.datastore[xpath]
      logger.info(f"[DatastoreResource.render_fetch] Obtained response for instance {i}. Printing.")
      pprint.pprint(instance_response)

      json_instance_response = json.dumps({full_xpath: instance_response})
      logger.info(f"[DatastoreResource.render_fetch] Generated JSON instance response for instance {i}. Printing.")
      pprint.pprint(json_instance_response)
      
      cbor_instance_response = CoAPServer.model.toCORECONF(json_instance_response)
      response.append(cbor_instance_response)

    cbor_response = cbor.dumps(response)
    logger.info(f"[DatastoreResource.render_fetch] Full response obtained. Printing.")
    logger.info(f"[DatastoreResource.render_fetch] Response: {cbor_response.hex()}")
    logger.info(f"[DatastoreResource.render_fetch] Response size: {len(cbor_response)} bytes")

    return aiocoap.Message(payload=cbor_response, content_format=142)

async def main():
  CoAPServer.init()

  root = resource.Site()

  root.add_resource(["c"], DatastoreResource())

  await aiocoap.Context.create_server_context(root, bind=(CoAPServer.host, CoAPServer.port))

  await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
  asyncio.run(main())