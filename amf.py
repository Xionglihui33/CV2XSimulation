import random
import threading
import socket
import json
import os
import time
from lib.utils import get_logger
from multiprocessing import Semaphore
from lib.common_obj import AfterRegister
from lib.common_logic import *
from msg_define import *


class AMF(AfterRegister):
    def __init__(self, GLOBAL_ID_OBU_i_PK_i_map, prime_nums):
        super().__init__()
        self.logger = get_logger("AMF")
        self.prime_nums = prime_nums

        # ========= 生成属性 =========
        self.delta_i_list = list()
        self.R = 0
        self.R_AMF = 0
        self.X_AMF = 0
        self.W = 0
        self.ID_OBU_i_V_i_map = dict()
        self.GLOBAL_ID_OBU_i_PK_i_map = GLOBAL_ID_OBU_i_PK_i_map
        self.R_i_msg_map = dict()
        self.r_AMF = 0
        self.GK = 0

        self.x_amf, self.y_amf, self.PK_AMF = get_x_i_y_i_PK_i(self.P, self.ID_AMF, self.s)
        # ========= 信号量定义 =======
        self.sem_qm_msg_receive = Semaphore(0)

        # ========= 网络设置 ========
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def broadcast_sender(self, msg):
        # print("======= ", len(msg.encode("utf-8")))
        self.send_socket.sendto(msg.encode("utf-8"), ('255.255.255.255', self.broadcast_port))

    def broadcast_receiver(self):
        def recv_handler_recv_qm_msg(json_obj):
            self.logger.debug("recv qm msg: {} from GL".format(json_obj))
            self.ID_OBU_i_V_i_map, self.R, self.R_i_msg_map, self.r_AMF, self.GK = \
                get_ID_OBU_i_V_i_map(json_obj["body"]["qm_msg"], self.ID_AMF, self.P, self.K_AMF, self.P_pub,
                                     self.prime_nums)
            self.W = json_obj["body"]["qm_msg"]["W"]
            self.sem_qm_msg_receive.release()

        self.send_socket.bind(('', self.broadcast_port))
        handler_func = dict()
        # 注册回调函数
        handler_func[MSG_TYPE_SEND_QM_MSG_TO_AMF] = recv_handler_recv_qm_msg
        while True:
            # 接收数据格式：(data, (ip, port))
            recv_data = self.send_socket.recvfrom(65535*1024)
            json_obj = json.loads(recv_data[0].decode("utf-8"))
            msg_type = json_obj["header"]["msg_type"]
            handler = handler_func.get(msg_type, None)
            if not handler:
                continue
            handler(json_obj)

    def start_receiver(self):
        t = threading.Thread(target=self.broadcast_receiver)
        t.setDaemon(True)
        t.start()

    # ====== 步骤实现 =======
    def broadcast_rsp_msg(self, rsp_msg):
        json_obj = dict()
        header_obj = dict()
        header_obj["msg_type"] = MSG_TYPE_SEND_RSP_MSG_TO_GL
        json_obj["header"] = header_obj
        body_obj = dict()
        body_obj["ID_AMF"] = self.ID_AMF
        body_obj["suss"] = "suss"
        body_obj["R_AMF"] = self.R_AMF
        body_obj["X_AMF"] = self.X_AMF
        body_obj["rsp_msg"] = rsp_msg
        body_obj["PK_AMF"] = self.PK_AMF
        json_obj["body"] = body_obj
        self.logger.debug("AMF send rsp msg to GL")
        self.broadcast_sender(json.dumps(json_obj))

    # ======= 主步骤 ========
    def main_process(self, sem_end):
        def wait_qm_msg_i():
            self.sem_qm_msg_receive.acquire()
        self.start_receiver()
        self.logger.info("Receiver started")
        self.logger.info(super().__str__())
        self.logger.info("start simulation")
        # ====== 收取签密消息 ======
        self.logger.debug("waiting for qm msg from GL")
        wait_qm_msg_i()
        # ====== 验签 =======
        sum_res = 0
        for ID_OBU_i, V_i in self.ID_OBU_i_V_i_map.items():
            PK_i = self.GLOBAL_ID_OBU_i_PK_i_map[ID_OBU_i]
            sum_res += V_i * hash_1(ID_OBU_i + PK_i) * (PK_i + self.P_pub)
            self.logger.debug("ID_OBU_i: {}, PK_i: {}, V_i: {}".format(ID_OBU_i, PK_i, V_i))
        right_hand = self.R + sum_res
        left_hand = self.W * self.P
        if left_hand != right_hand:
            self.logger.error("qm msg check failed!")
            exit(0)
        self.logger.debug("qm msg check passed!")
        self.R_AMF = self.r_AMF * self.P
        h_AMF = get_h_AMF(self.R, self.R_AMF)
        self.X_AMF = get_X_AMF(self.r_AMF, self.x_amf, self.y_amf, h_AMF)
        self.broadcast_rsp_msg(self.R_i_msg_map)
        sem_end.release()
        time.sleep(1)
        exit(0)
