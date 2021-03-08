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


class OBU(AfterRegister):
    def __init__(self, obu_idx, total_obu_num, GLOBAL_ID_OBU_i_PK_i_map):
        super().__init__()
        self.ID_OBU_i = get_ID_obu_i(obu_idx)
        self.total_num = total_obu_num
        self.idx = str(obu_idx)

        self.logger = get_logger("OBU_" + self.idx)

        # ========= 生成属性 =========
        self.r_i = random.randint(1, self.P)
        self.x_i, self.y_i, self.PK_i = get_x_i_y_i_PK_i(self.P, self.ID_OBU_i, self.s)
        GLOBAL_ID_OBU_i_PK_i_map[self.ID_OBU_i] = self.PK_i
        self.GLOBAL_ID_OBU_i_PK_i_map = GLOBAL_ID_OBU_i_PK_i_map
        self.R_i = self.r_i * self.P
        self.Ri_map = dict()
        self.R = 0
        self.logger.debug("x_i: {}, y_i: {}, PK_i: {}, R_i: {}".format(self.x_i, self.y_i, self.PK_i, self.R_i))

        # ========= 信号量定义 =======
        self.sem_r_receive = Semaphore(0)
        self.sem_rsp_msg = Semaphore(0)

        # ========= 网络设置 ========
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # ========= 回包 =========
        self.rsp_msg = None

    def broadcast_sender(self, msg):
        self.send_socket.sendto(msg.encode("utf-8"), ('255.255.255.255', self.broadcast_port))

    def broadcast_receiver(self):
        def recv_handler_recv_Ri(json_obj):
            self.logger.debug("recv Ri: {} from OBU".format(json_obj["body"]["Ri"]))
            self.R += json_obj["body"]["Ri"]
            self.sem_r_receive.release()

        def recv_handler_recv_rsp_msg(json_obj):
            self.rsp_msg = json_obj
            self.sem_rsp_msg.release()

        self.send_socket.bind(('', self.broadcast_port))
        handler_func = dict()
        # 注册回调函数
        handler_func[MSG_TYPE_R_BROADCAST] = recv_handler_recv_Ri
        handler_func[MSG_TYPE_SEND_RSP_MSG_TO_OBU] = recv_handler_recv_rsp_msg
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
    def broadcast_R_i(self):
        json_obj = dict()
        header_obj = dict()
        body_obj = dict()
        header_obj["msg_type"] = MSG_TYPE_R_BROADCAST
        body_obj["Ri"] = self.R_i
        json_obj["header"] = header_obj
        json_obj["body"] = body_obj
        msg = json.dumps(json_obj)
        self.broadcast_sender(msg)
        self.logger.debug("send Ri: {}".format(msg))

    def broadcast_delta_i(self, delta_i):
        json_obj = dict()
        header_obj = dict()
        body_obj = dict()
        header_obj["msg_type"] = MSG_TYPE_SEND_DELTA_TO_GL
        body_obj["delta"] = delta_i
        json_obj["header"] = header_obj
        json_obj["body"] = body_obj
        msg = json.dumps(json_obj)
        self.broadcast_sender(msg)
        self.logger.debug("send delta: {}".format(msg))

    # ======= 主步骤 ========
    def main_process(self, sem_start, sem_end):
        def wait_ri():
            for _ in range(self.total_num):
                self.sem_r_receive.acquire()
        def wait_rsp_msg():
            self.sem_rsp_msg.acquire()
        self.start_receiver()
        self.logger.info("Receiver started")
        self.logger.info(super().__str__())
        time.sleep(0.04*self.total_num)
        # ====== 广播r_i ======
        sem_start.release()
        self.logger.info("start simulation")
        self.broadcast_R_i()
        wait_ri()
        self.logger.debug("R: {}".format(self.R))
        # ====== 计算 ======
        K_i = get_K_i(self.r_i, self.ID_AMF, self.P, self.K_AMF, self.P_pub)
        theta_i = get_theta_i()
        alpha_i = get_alpha_i(self.ID_AMF, K_i, self.R_i)
        c_i = get_c_i(alpha_i, theta_i)
        beta_i = get_beta_i(theta_i)
        V_i = get_V_i(beta_i, "TEST MSG from obu " + self.idx, self.ID_OBU_i)
        w_i = get_w_i(self.x_i, self.y_i, V_i, self.r_i)
        self.logger.debug("======= w_i * P: {}".format(w_i * self.P))
        delta_i = get_delta_i(c_i, self.R_i, V_i, w_i, self.R)
        self.logger.debug("\nK_i: {}\nθ_i: {}\nc_i: {}\nbeta_i:{}\nV_i:{}\nw_i:{}\ndelta_i{}"
                          .format(K_i, theta_i, c_i, beta_i, V_i, w_i, delta_i))
        self.broadcast_delta_i(delta_i)
        # 等待回包
        self.logger.info("waitting for rsp msg")
        wait_rsp_msg()
        self.logger.info("get rsp msg: {}".format(self.rsp_msg))
        X_AMF = self.rsp_msg["body"]["X_AMF"]
        R_AMF = self.rsp_msg["body"]["R_AMF"]
        PK_AMF = self.rsp_msg["body"]["PK_AMF"]
        H_1 = hash_1(self.ID_AMF + PK_AMF)

        h_AMF = get_h_AMF(self.R, R_AMF)
        left_hand = X_AMF * self.P
        right_hand = R_AMF + H_1 * (PK_AMF + self.P_pub) * h_AMF
        if left_hand != right_hand:
            self.logger.error("RSP msg check failed!")
            return
        self.logger.debug("RSP msg check passed!")
        SK_i = get_SK_i(self.r_i, R_AMF)
        encrypt_msg = self.rsp_msg["body"]["rsp_msg"][str(self.R_i)]  # json字段必须是字符串
        rsp_msg = aes_decrypt(encrypt_msg, SK_i)
        self.logger.debug("Get rsp encrypt msg: {}, plant text: {}".format(encrypt_msg, rsp_msg))
        json_obj = json.loads(rsp_msg)
        GK_lambda = json_obj["GK_lambda"]
        nonce = json_obj["nonce"]
        GK = GK_lambda % nonce
        self.logger.debug("get GK: {}".format(GK))
        sem_end.release()
        time.sleep(1)
        exit(0)
