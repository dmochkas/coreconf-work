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

  def extractDataNode(self, instance: int|tuple) -> dict:
    logger.info(f"[DatastoreResource.extractDataNode] Instance is of type {type(instance)}")

    # If instance is only SID, simply get XPath
    if isinstance(instance, int):
      sid = instance
      xpath = CoAPServer.module_name + ':' + CoAPServer.datastore._create_xpath(sid)[1:]
      return_xpath = xpath
    elif isinstance(instance, tuple) or isinstance(instance, list):
      sid = instance[0]
      xpath = CoAPServer.module_name + ':' + CoAPServer.datastore._create_xpath(sid, keys=instance[1:])[1:]
      return_xpath = CoAPServer.module_name + ':' + CoAPServer.datastore._create_xpath(sid)[1:]
    else:
      logger.error("[DatastoreResource.extractDataNode] Instance is bad type!")
      raise TypeError("Bad instance type: ", type(instance).__name__)

    logger.info(f"[DatastoreResource.extractDataNode] Payload instance has keyless XPath {return_xpath}")
    logger.info(f"[DatastoreResource.extractDataNode] Payload instance has XPath {xpath}")

    instance_response = CoAPServer.datastore[xpath]
    logger.info(f"[DatastoreResource.extractDataNode] Obtained response for instance. Printing.")
    pprint.pprint(instance_response, indent=4)

    json_instance_response = {return_xpath: instance_response}
    logger.info(f"[DatastoreResource.extractDataNode] Generated JSON object instance response for instance. Printing.")
    pprint.pprint(json_instance_response, indent=4)
    
    cbor_instance_response = CoAPServer.model.toCORECONF(json_instance_response)
    logger.info(f"[DatastoreResource.extractDataNode] Created CORECONF string from JSON object. Printing.")
    pprint.pprint(cbor.loads(cbor_instance_response), indent=4)
    
    return cbor_instance_response

  def insertDataNode(self, patch: dict):

    logger.info(f"[DatastoreResource.insertDataNode] Inserting data node!")
    pprint.pprint(patch)

    instance, data = list(patch.items())[0] # Get patch key (SID and keys) and data

    logger.info(f"[DatastoreResource.insertDataNode] Instance is of type {type(instance)}")

    # If instance is only SID, simply get XPath
    if isinstance(instance, int):
      sid = instance
      xpath = CoAPServer.module_name + ':' + CoAPServer.datastore._create_xpath(sid)[1:]
    elif isinstance(instance, tuple):
      sid = instance[0]
      xpath = CoAPServer.module_name + ':' + CoAPServer.datastore._create_xpath(sid, keys=instance[1:])[1:]
    else:
      logger.error("[DatastoreResource.insertDataNode] Instance is bad type!")
      raise TypeError("Bad instance type: ", type(instance).__name__)

    logger.info(f"[DatastoreResource.insertDataNode] Payload instance has XPath {xpath}")

    if data is None:
      logging.info("[DatastoreResource.insertDataNode] Payload patch data is None. Deleting data node.")
      del CoAPServer.datastore[xpath]
    else:
      try:
        CoAPServer.datastore[xpath] = data
      except TypeError as e:
        logger.error("[DatastoreResource.insertDataNode] Payload patch data has bad type!")
        raise e
      except Exception as e:
        logger.error("[DatastoreResource.insertDataNode] Unknown payload patch data error!")
        raise e

  async def render_fetch(self, request: aiocoap.Message) -> aiocoap.Message:
    logger.info(f"[DatastoreResource.render_fetch] FETCH request from client {request.remote}")
    payload = cbor.loads(request.payload)
    logger.info(f"[DatastoreResource.render_fetch] Payload: {payload}")

    response = []
    for i, instance in enumerate(payload):
      logger.info(f"[DatastoreResource.render_fetch] Extracting instance {i}.")
      cbor_instance_response = self.extractDataNode(instance)
      response.append(cbor.loads(cbor_instance_response))

    cbor_response = cbor.dumps(response)
    logger.info(f"[DatastoreResource.render_fetch] Full response obtained. Printing.")
    logger.info(f"[DatastoreResource.render_fetch] Response: {cbor_response.hex()}")
    logger.info(f"[DatastoreResource.render_fetch] Response size: {len(cbor_response)} bytes")

    return aiocoap.Message(payload=cbor_response, content_format=142)

  async def render_ipatch(self, request: aiocoap.Message) -> aiocoap.Message:
    logger.info(f"[DatastoreResource.render_ipatch] iPATCH request from client {request.remote}")
    payload = cbor.loads(request.payload)
    logger.info(f"[DatastoreResource.render_ipatch] Payload:")
    pprint.pprint(payload, indent=4)

    for i, patch in enumerate(payload):
      logger.info(f"[DatastoreResource.render_ipatch] Inserting instance {i}.")
      self.insertDataNode(patch)
    
    return aiocoap.Message(transport_tuning=aiocoap.Unreliable)

async def main():
  CoAPServer.init()

  root = resource.Site()

  root.add_resource(["c"], DatastoreResource())

  await aiocoap.Context.create_server_context(root, bind=(CoAPServer.host, CoAPServer.port))

  await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
  asyncio.run(main())