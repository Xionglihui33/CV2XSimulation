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


class GL(AfterRegister):
    def __init__(self, total_obu_num):
        super().__init__()
        self.ID_GL = get_ID_gl(time.time())
        self.total_num = total_obu_num

        self.logger = get_logger("GL")

        # ========= 生成属性 =========
        self.delta_i_list = list()
        self.R = 0
        self.W = 0

        # ========= 信号量定义 =======
        self.sem_delta_i_receive = Semaphore(0)
        self.sem_msg_rsp_receive = Semaphore(0)

        # ========= 网络设置 ========
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # ========= 回包 =========
        self.rsp_msg = None

    def broadcast_sender(self, msg):
        self.send_socket.sendto(msg.encode("utf-8"), ('255.255.255.255', self.broadcast_port))

    def broadcast_receiver(self):
        def recv_handler_recv_delta(json_obj):
            self.delta_i_list.append(json_obj["body"]["delta"])
            self.logger.debug("recv delta_i: {} from OBU".format(json_obj["body"]["delta"]))
            self.W += json_obj["body"]["delta"]["w_i"]
            self.R += json_obj["body"]["delta"]["R_i"]
            self.sem_delta_i_receive.release()

        def recv_rsp_msg_data(json_obj):
            self.logger.debug("recv rsp msg: {} from AMF".format(json_obj))
            self.rsp_msg = json_obj
            self.sem_msg_rsp_receive.release()

        self.send_socket.bind(('', self.broadcast_port))
        handler_func = dict()
        # 注册回调函数
        handler_func[MSG_TYPE_SEND_DELTA_TO_GL] = recv_handler_recv_delta
        handler_func[MSG_TYPE_SEND_RSP_MSG_TO_GL] = recv_rsp_msg_data
        while True:
            # 接收数据格式：(data, (ip, port))
            recv_data = self.send_socket.recvfrom(65535)
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
    def broadcast_qm_msg(self, qm_msg):
        json_obj = dict()
        header_obj = dict()
        header_obj["msg_type"] = MSG_TYPE_SEND_QM_MSG_TO_AMF
        json_obj["header"] = header_obj
        body_obj = dict()
        body_obj["qm_msg"] = qm_msg
        json_obj["body"] = body_obj
        self.logger.debug("GL send qm msg to AMF")
        self.broadcast_sender(json.dumps(json_obj))

    def broadcast_rsp_msg(self, json_obj):
        self.logger.debug("GL broadcast_rsp_msg to OBU")
        json_obj["header"]["msg_type"] = MSG_TYPE_SEND_RSP_MSG_TO_OBU
        self.broadcast_sender(json.dumps(json_obj))

    # ======= 主步骤 ========
    def main_process(self, sem_end):
        def wait_delta_i():
            for _ in range(self.total_num):
                self.sem_delta_i_receive.acquire()

        def wait_rsp_msg():
            self.sem_msg_rsp_receive.acquire()
        # time.sleep(0.1*self.total_num)
        self.start_receiver()
        self.logger.info("Receiver started")
        self.logger.info(super().__str__())
        self.logger.info("start simulation")
        self.logger.debug("waitting for delta_i")
        # ====== 收取δ_i ======
        wait_delta_i()
        # ====== 检查 R的情况 ======
        self.logger.debug("R: {}".format(self.R))
        for delta_i in self.delta_i_list:
            if delta_i["R"] != self.R:
                self.logger.error("R check failed!")
                exit(0)

        self.logger.debug("R check all passed!")
        self.logger.debug("W: {}".format(self.W))
        # ====== 计算 =======
        qm_msg = get_qm_msg(self.delta_i_list, self.W)
        self.logger.debug(qm_msg)
        self.broadcast_qm_msg(qm_msg)
        # 等待回包
        self.logger.debug("waitting for AMF rsp msg")
        wait_rsp_msg()
        # 广播回包给OBU
        self.broadcast_rsp_msg(self.rsp_msg)
        sem_end.release()
        time.sleep(1)
        exit(0)
