import asyncio
from base import CoAPBase
from device import CoAPClient
import json
import pprint

import logging

logging.basicConfig(level=logging.INFO)
logging.disable(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
  print("="*100)
  print("CoAP iPATCH request")
  print("="*100)

  # Initialize client instance
  client = CoAPClient(CoAPBase.host, CoAPBase.port)
  await client.init()

  print()
  print("="*100)
  print("Local datastore fetched!")
  input("Press Enter to continue...")
  print("="*100)

  # DECIDE ON iPATCH URI BELOW
  IPATCH_PATH = "/basic-sensor:sensors/sensor[type='temperature'][id='0']"
  IPATCH_CONTENT = None

  print(f"Data note path: {IPATCH_PATH}")
  print(f"Data node modification: {IPATCH_CONTENT}")
  print("Resolving path, getting SID and keys...")

  target_sid, keys = client.ds._resolve_path(IPATCH_PATH)
  if keys:
    instance = [target_sid] + keys
  else:
    instance = target_sid

  payload = {
    tuple(instance): IPATCH_CONTENT
  }

  print(f"iPATCH request payload: {payload}")
  input("Press Enter to continue...")

  print(f"\nAttempting to send FETCH with payload {payload}")

  try:
    response = await client.iPATCH("c", [payload])
  except Exception as e:
    logger.exception(e)
    raise e

  print("Response obtained successfully! Raw response below...\n")

  print(response)

  print("\nEnd program.\n")

if __name__=="__main__":
  asyncio.run(main())