import os

class CoAPBase:
  """
  Container with static variables
  """

  DEV_IP = "fe80::d840:c892:34a2:42dc" # Device IPv6
  APP_IP = "fe80::cc16:c368:933b:b8dc" # Application IPv6
  PORT = 5683 # CoAP standard port