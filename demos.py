# -*- coding:utf-8 -*-

from socket import *
import time
import sys
import multiprocessing
import os

"""
可以开多个终端，一个终端调用 xxx.py send
其他终端调用  xxx.py
"""


class Broadcast:
    def __init__(self, send_flag=False):
        # 全局参数配置
        self.encoding = "utf-8"  # 使用的编码方式
        self.broadcastPort = 7789   # 广播端口
        self.send_flag = send_flag

        if not send_flag:
            # 创建广播接收器
            self.recvSocket = socket(AF_INET, SOCK_DGRAM)
            # SO_REUSEPORT 设置多个进程可以绑定同一个端口！！！！
            self.recvSocket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            # SO_REUSEADDR 没用。。再去研究一下
            # self.recvSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.recvSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            self.recvSocket.bind(('', self.broadcastPort))
        else:
            # 创建广播发送器
            self.sendSocket = socket(AF_INET, SOCK_DGRAM)
            self.sendSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    def send(self):
        """发送广播"""

        print("UDP广播发送器启动成功...")
        while True:
            time_str = time.strftime("现在时间：%Y年%m月%d日 %H:%M:%S", time.localtime(time.time()))
            self.sendSocket.sendto(time_str.encode(self.encoding), ('255.255.255.255', self.broadcastPort))
            time.sleep(1)

    def recv(self, recv_id):
        """接收广播"""
        print("UDP接收器启动成功...")
        while True:
            # 接收数据格式：(data, (ip, port))
            recvData = self.recvSocket.recvfrom(1024)
            print("[%d][来自%s:%s的广播]:%s" % (recv_id, recvData[1][0], recvData[1][1], recvData[0].decode(self.encoding)))

    def start(self, obj_id=0):
        if self.send_flag:
            self.send()
        else:
            self.recv(obj_id)


def broadcast_main_1():
    """
    广播，手动运行脚本版本
    :return:
    """
    if len(sys.argv) != 2:
        print("后面加参数 send 或 recv")
        return
    if sys.argv[1] == "send":
        sender = Broadcast(True)
        sender.start()
    else:
        recver = Broadcast()
        recver.start()


def broadcast_main_2():
    """
    广播，多进程运行版本（但是和手动运行不同，手动一个生产者，多个消费者是可以同时消费的，但是多进程时只会有一个子进程收到广播消息）
    :return:
    """
    sender = Broadcast(True).start
    recver = Broadcast().start
    threads = list()
    threads.append(multiprocessing.Process(target=sender))
    for i in range(10):
        threads.append(multiprocessing.Process(target=recver, args=(i, )))
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def fork_sender(count):
    if count > 0:
        ret = os.fork()
        if ret == 0:
            # 子进程
            fork_sender(count-1)
        else:
            Broadcast().start(count)


def broadcast_main_3():
    """
    广播，多进程运行版本，使用fork会实际创建进程，这样就会使得多消费者同时收到一个广播
    :return:
    """
    ret = os.fork()
    if ret == 0:
        # 子进程
        print("Sub process pid = %d, Sub process ppid = %d" % (os.getpid(), os.getppid()))
        fork_sender(5)
    else:
        # 父进程
        print("Parent Process ret = %d" % ret)
        print("Parent Process pid = %d" % os.getpid())
        Broadcast(True).start()


def crc():
    import zlib
    post_id = "65fe4882de661f4a6e25391c790b6b86"
    post_id_crc32 = zlib.crc32(post_id.encode("utf-8"))
    print(post_id_crc32)


def get_reverse(x, m):
    def gcd_extended(x, m):
        if x == 0:
            return m, 0, 1
        gcd, x1, y1 = gcd_extended(m % x, x)
        x = y1 - (m // x) * x1
        y = x1
        return gcd, x, y
    return gcd_extended(x, m)[1] % m


if __name__ == "__main__":
    try:
        # broadcast_main_3()
        # crc()
        print(get_reverse(7, 90))
    except KeyboardInterrupt:
        pass
