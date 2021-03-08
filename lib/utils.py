import hashlib
import os
import time
import logging
import zlib
import base64
import sys
from Crypto.Cipher import AES


def get_str_sha256(str_obj):
    """
    获取str_obj的sha256结果
    """
    s = hashlib.sha256()
    s.update(str_obj.encode())
    return s.hexdigest()


def get_time_str(format_str="%Y%m%d_%H%M%S"):
    """
    获取时间字符串
    """
    now = time.localtime(time.time())
    time_str = time.strftime(format_str, now)
    return time_str


def get_crc32(obj):
    return zlib.crc32(str(obj).encode("utf-8")) % 65536


# 获取当前时戳 10位数
def get_timestamp():
    return int(time.time())


def add_16(par):
    par = par.encode("utf-8")
    while len(par) % 16 != 0:
        par += b'\x00'
    return par


def aes_encrypt(msg, key) -> int:
    """
    提供aes对称加密，结果是可计算的int
    """
    key = str(key)
    aes = AES.new(add_16(key), AES.MODE_ECB)
    # 下面这个是 bs64 字符串
    # base64.encodebytes(aes.encrypt(add_16(msg))).strip().decode("utf-8")
    return int.from_bytes(base64.encodebytes(aes.encrypt(add_16(msg))).strip(), 'little', signed=True)


def aes_decrypt(msg: int, key) -> str:
    """
    提供aes对称解密，明文是可计算的int
    """
    aes = AES.new(add_16(str(key)), AES.MODE_ECB)
    en_msg = msg.to_bytes(4096, 'little', signed=True)
    return aes.decrypt(base64.decodebytes(en_msg)).strip(b"\x00").decode("utf-8")


def get_logger(name):
    log_level = "DEBUG"
    log_path = "./log/"
    file_format_str = '[%(asctime)s][%(levelname)5s][%(filename)s:%(funcName)s@%(lineno)d]# %(message)s'
    file_formatter = logging.Formatter(file_format_str)
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    log_file = "{}/{}".format(log_path, "{}.log".format(name))
    if log_file:
        if os.path.isfile(log_file):
            os.remove(log_file)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    if len(sys.argv) > 2:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(file_formatter)
        logger.addHandler(stream_handler)
    return logger


def get_reverse(x, m):
    """
    获取逆元，x^-1  *  x = 1 mod m
    获取 x^-1
    """
    def gcd_extended(x, m):
        if x == 0:
            return m, 0, 1
        gcd, x1, y1 = gcd_extended(m % x, x)
        x = y1 - (m // x) * x1
        y = x1
        return gcd, x, y
    return gcd_extended(x, m)[1] % m
