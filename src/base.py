import os

MODULE_NAME = "basic-sensor"
SID_FILE = MODULE_NAME + ".sid"
SID_PATH = os.path.join(os.path.dirname(__file__), "model", SID_FILE)

class CoAPBase:
  """
  Container with inherited static variables.
  """

  host = "localhost"
  port = 5863
  module_name = MODULE_NAME
  sid_file = SID_PATH