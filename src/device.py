import sys
import os

import datetime
import random
import pprint
import json
import cbor2 as cbor
import pycoreconf
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SID_FILE = "basic-sensor.sid"
SID_PATH = os.path.join(os.path.dirname(__file__), "model", SID_FILE)

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

class CoAPClient:
  def __init__(self, config, datastore):
    logger.info("[CoAPClient] Creating CoAPClient instance...")

    self.config = config
    self.ds = datastore
    
    logger.info("[CoAPClient] CoAPClient instance created!")

  def GET(self, sid: int, keys: str):
    """
    CoAP GET operation on specified SID with keys.
    """

    # Get resource
    logger.info(f"[CoAPClient] Attempting to GET resource in SID {sid}...")
    try:
      # Get XPath from SID and keys
      logger.info(f"[CoAPClient] Creating XPath from SID and keys...")
      if keys:
        decoded_keys = cbor.loads(keys)
      else:
        decoded_keys = None
      target_path = self.ds._create_xpath(sid, keys=decoded_keys)
      
      logger.info(f"[CoAPClient] Obtained path: {target_path}")
      entry = self.ds[target_path]
      return entry
    except IndexError as e:
      logger.error("Invalid path.")
      return {"error": "invalid path"}
    except Exception as e:
      logger.error("[CoAPClient] GET error")
      logger.exception(e)
    return None

def main():

  # Title
  print("=" * 60)
  print("CORECONF implementation of basic sensor network")
  print("=" * 60)

  # Load SID file to pycoreconf model
  print("\n\tLoading SID file...")
  try:
    ccm = pycoreconf.CORECONFModel(SID_PATH)
  except Exception as e:
    logger.exception(e)
    sys.exit(1)
  print("SID file loaded!")
  input("Press Enter to continue...")

  # Generate and print data
  print("\n\tGenerating sample data...")
  config_data = generateFullData()
  print("Data generated! Shown below:")
  pprint.pprint(config_data)
  input("Press Enter to continue...")

  # Dump into JSON string
  print("\n\tDumping data into JSON string...")
  try:
    json_data = json.dumps(config_data, indent=2)
  except Exception as e:
    logger.exception(e)
    sys.exit(1)
  print("Data dumped into JSON string!")
  print(json_data)
  print(f"JSON data length: {len(json_data)} bytes")
  input("Press Enter to continue...")

  # Dump to CBOR string
  print("\n\tDumping data into CBOR format through CORECONF...")
  try:
    cbor_data = ccm.toCORECONF(json_data)
  except Exception as e:
    logger.exception(e)
    sys.exit(1)
  print("CBOR string generated!")
  print(f"CBOR data: {cbor_data.hex()}")
  print(f"CBOR data length: {len(cbor_data)} bytes")
  input("Press Enter to continue...")

  # Load datastore with CBOR data
  print("\n\tLoading CBOR data into datastore...")
  ds = ccm.create_datastore(cbor_data=cbor_data)
  print("Datastore loaded!")

  # Testing datastore using XPath address
  xpath_key = "/sensors/sensor"
  print(f"\nReading datastore keys with path {xpath_key}")
  try:
    entry = ds[xpath_key]
    print("Complete entry retrieved:")
    pprint.pprint(entry)
  except Exception as e:
    logger.exception(e)
    sys.exit(1)
  input("Press Enter to continue...")

  # Testing datastore using SID obtained from XPath address
  print("\n\tTesting SIDs...")
  for path_in in ["/characteristics/identifier", "/sensors/sensor", "/sensors/sensor[type='temperature'][id='0']/quantity/value"]:
    try:
      print(f"Getting SID from path: {path_in}")
      
      # Get SID from datastore _resolve_path method
      target_sid, keys = ds._resolve_path(path_in)
      print(f"Obtained SID {target_sid} with keys:")
      pprint.pprint(keys)

      # Get path back from datastore _create_xpath method
      path_out = ds._create_xpath(target_sid, keys=keys)
      print(f"Obtained path from SID: {path_out}")

      if path_in == path_out:
        print("Input and output paths match!")
      else:
        logger.error(f"Mismatched paths!\n\t In: {path_in}\n\tOut:{path_out}")

    except Exception as e:
      logger.exception(e)
      sys.exit(1)
  input("Press Enter to continue...")

  print("\n\tEntering CoAP test loop...")
  client = CoAPClient(ccm, ds)
  running = True
  while len((xpath_key := input("\nEnter resource path: "))) > 0:

    # Get specific SID and keys from XPath
    try:
      target_sid, keys = ds._resolve_path(xpath_key)
    except Exception as e:
      logger.exception(e)
      print("\nContinuing...")
      continue

    print(f"SID obtained from path: {target_sid}")
    print(f"Keys: {keys}")
    if len(keys):
      cbor_keys = cbor.dumps(keys)
      print(f"Keys (CBOR encoding): {cbor_keys.hex()}")
    else:
      cbor_keys = None # If no keys, use None
      print("Empty keys. No encoding necessary.")

    entry = client.GET(target_sid, cbor_keys)
    print("Complete entry retrieved:")
    pprint.pprint(entry)
  
  print("Exited loop. End program.")

if __name__=="__main__":
  main()