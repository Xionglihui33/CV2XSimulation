import random
from lib.common_logic import *
import requests


class AfterRegister:
    def __init__(self):
        self.broadcast_port = 23334
        self.P = 24823693247
        self.s = hash_0(self.P)
        self.P_pub = self.s * self.P
        self.ID_AMF = get_ID_amf(self.s)
        self.K_AMF = get_K_amf(self.s)
        self.prims = list()

    def __str__(self):
        res = ""
        res += "broadcast_port: {}\n".format(self.broadcast_port)
        res += "P: {}\n".format(self.P)
        res += "s: {}\n".format(self.s)
        res += "P_pub: {}\n".format(self.P_pub)
        res += "ID_AMF: {}\n".format(self.ID_AMF)
        res += "K_AMF: {}\n".format(self.K_AMF)
        return res

