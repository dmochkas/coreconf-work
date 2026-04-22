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

  def GET(self, path: str):
    """
    CoAP GET operation on specified path path.
    """

    # Get resource
    logger.info(f"[CoAPClient] Attempting to GET resource in path {path}...")
    try:
      entry = self.ds[path]
      return entry
    except Exception as e:
      logger.error("[CoAPClient] GET error")
      logger.exception(e)
      return None

def main():

  # Title
  print("=" * 60)
  print("CORECONF implementation of RPN calculator")
  print("=" * 60)

  # Load SID file to pycoreconf model
  print("\nLoading SID file...")
  try:
    ccm = pycoreconf.CORECONFModel(SID_PATH)
  except Exception as e:
    logger.exception(e)
    sys.exit(1)
  print("SID file loaded!")
  input("Press Enter to continue...")

  # Generate and print data
  print("\nGenerating sample data...")
  config_data = generateFullData()
  print("Data generated! Shown below:")
  pprint.pprint(config_data)
  input("Press Enter to continue...")

  # Dump into JSON string
  print("\nDumping data into JSON string...")
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
  print("\nDumping data into CBOR format through CORECONF...")
  try:
    cbor_data = ccm.toCORECONF(json_data)
  except Exception as e:
    logger.exception(e)
    sys.exit(1)
  print("CBOR string generated!")
  print(f"CBOR data: {cbor_data.hex()}")
  print(f"CBOR data length: {len(cbor_data)} bytes")
  input("Press Enter to continue...")

  print("\nLoading CBOR data into datastore...")
  ds = ccm.create_datastore(cbor_data=cbor_data)
  print("Datastore loaded!")

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

  print("Entering CoAP test loop...")
  client = CoAPClient(ccm, ds)
  running = True
  while len((xpath_key := input("\nEnter resource path: "))) > 0:
    entry = client.GET(xpath_key)
    print("Complete entry retrieved:")
    pprint.pprint(entry)
  
  print("Exited loop. End program.")

if __name__=="__main__":
  main()