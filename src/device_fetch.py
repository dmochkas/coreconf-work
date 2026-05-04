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
  print("CoAP FETCH request")
  print("="*100)

  # Initialize client instance
  client = CoAPClient(CoAPBase.host, CoAPBase.port)
  await client.init()

  print()
  print("="*100)
  print("Local datastore fetched!")
  input("Press Enter to continue...")
  print("="*100)

  # DECIDE ON FETCH URI BELOW
  FETCH_PATH = "/basic-sensor:sensors/sensor[type='temperature'][id='0']/enabled"

  print(f"Data note path: {FETCH_PATH}")
  print("Resolving path, getting SID and keys...")

  target_sid, keys = client.ds._resolve_path(FETCH_PATH)
  if keys:
    instance = tuple([target_sid] + keys)
  else:
    instance = target_sid

  print(f"FETCH request payload: {instance}")
  input("Press Enter to continue...")

  print(f"\nAttempting to send FETCH with payload {instance}")

  try:
    response = await client.FETCH("c", [instance])
  except Exception as e:
    logger.exception(e)
    raise e

  print("Response obtained successfully! Raw response below...\n")

  print(response.payload)

  print("\nLoading response to JSON structure...\n")

  cbor_payload = json.loads(client.model.toJSON(response.payload))
  pprint.pprint(cbor_payload)

  print("\nEnd program.\n")

if __name__=="__main__":
  asyncio.run(main())