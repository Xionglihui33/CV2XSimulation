from multiprocessing import Semaphore
from lib.common_logic import *
from obu import OBU
from gl import GL
from amf import AMF
import requests
import sys

"""
参数说明：
python3 main.py num_of_obu print_log_flag
num_of_obu: 需要为整数，代表仿真的OBU数量
print_log_flag: 任意值均可，可以不传。如果不传，则不打印日志。否则将日志打印在终端上
"""


IP = "192.168.0.106"
# IP = None

def get_prime_nums(digits, num_of_prime_nums):
    prime_nums = list()
    for _ in range(num_of_prime_nums // 20 + 1):
        if not IP:
            prime_nums += list(map(int, json.loads(requests.get("https://big-primes.ue.r.appspot.com/primes?digits={}&numPrimes={}".format(digits, 20)).text)["Primes"]))
        else:
            prime_nums += list(map(int, json.loads(requests.get("https://big-primes.ue.r.appspot.com/primes?digits={}&numPrimes={}".format(digits, 20), proxies={"https":"{}:10800".format(IP)}).text)["Primes"]))
            
    return prime_nums


def start():
    GLOBAL_ID_OBU_i_PK_i_map = dict()
    # OBU Node
    total_obu = 5
    if len(sys.argv) > 1:
        total_obu = int(sys.argv[1])
    total_gl = 1
    total_amf = 1
    prime_nums = get_prime_nums(5, total_obu + 1)
    if len(prime_nums) <= total_obu + 1:
        print("Get primes error, now exit")
        return
    obu_list = list()
    for i in range(total_obu):
        obu_list.append(OBU(i + 1, total_obu, GLOBAL_ID_OBU_i_PK_i_map))

    sem_end = Semaphore(0)
    sem_start = Semaphore(0)
    father_process = False
    for obu_obj in obu_list:
        ret_obu = os.fork()
        if ret_obu == 0:
            # 子进程
            print("OBU Sub process pid = %d, Sub process ppid = %d" % (os.getpid(), os.getppid()))
            obu_obj.main_process(sem_start, sem_end)
            father_process = False
            break
        else:
            # 父进程
            father_process = True

    # 确保只有父进程触发创建 GL 子进程
    if father_process:
        gl = GL(total_obu)
        ret_gl = os.fork()
        if ret_gl == 0:
            # 子进程
            print("GL Sub process pid = %d, Sub process ppid = %d" % (os.getpid(), os.getppid()))
            gl.main_process(sem_end)
            # sem_end.release()
            father_process = False
        else:
            father_process = True

    # 确保只有父进程触发创建 AMF 子进程
    if father_process:
        amf = AMF(GLOBAL_ID_OBU_i_PK_i_map, prime_nums)
        ret_gl = os.fork()
        if ret_gl == 0:
            # 子进程
            print("AMF Sub process pid = %d, Sub process ppid = %d" % (os.getpid(), os.getppid()))
            amf.main_process(sem_end)
            # sem_end.release()
            father_process = False
        else:
            father_process = True
    
    # 确保只有父进程等待，其他进程结束直接退出
    if father_process:
        start_time = 0
        end_time = 0
        for i in range(total_obu):
            sem_start.acquire()
        start_time = time.time()
        for i in range(total_obu + total_gl + total_amf):
            sem_end.acquire()
        end_time = time.time()
        return end_time - start_time
    return None


def main():
    if not os.path.isdir("./log"):
        os.mkdir("./log")
    print("3秒后运行")
    time.sleep(3)
    duration = start()
    if duration:
        with open("duration.txt", "a+", encoding="utf-8") as f:
            f.write(str(duration*1000) + "\n")
        print("Duration: {:.3f} ms".format(duration*1000))


if __name__ == "__main__":
    # Wireshark 抓包：udp.port==23333
    main()
    # python main.py
