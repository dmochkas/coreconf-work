import os

class CoAPBase:
  """
  Container with static variables
  """

  DEV_IP = "::1" # Device IPv6
  APP_IP = "::1" # Application IPv6
  PORT = 5683 # CoAP standard port