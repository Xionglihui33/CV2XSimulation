# C-V2X中车辆群组通信系统的仿真

## 简介

本工程为毕业论文C-V2X中车辆群组通信系统的仿真，使用`Python3`语言编写。使用多进程模拟不同的终端，多线程模拟某一终端的广播监听。发送和接收数据包均采用`UDP`协议发送广播数据包以模拟不安全的公共信道，因此运行时的广播可以被`tcpdump`等抓包工具实际捕获。在这些条件下最终模拟出整套方案一与方案二的全部流程（不包括注册流程）。

## 运行环境

`*nux`系统，`Windows`系统不支持。

依赖库安装：
``` shell
pip3 install -r requirements.txt
```
或
```shell
pip3 install requests
pip3 install pycryptodome
```

## 运行方法
可以直接运行
```shell
python3 main.py num_of_obu print_log_flag
```

### 参数说明：

`num_of_obu`: 需要为整数，代表仿真的OBU数量

`print_log_flag`: 任意值均可，可以不传。如果不传，则不打印日志。否则将日志打印在终端上

或运行：

``` shell
test_duration.sh num_of_obu test_count print_log_flag
```

### 参数说明：

`num_of_obu`: 需要为整数，代表仿真的OBU数量

`test_count`: 运行测试的次数。最终耗时为每次运行结果的均值。

`print_log_flag`: 任意值均可，可以不传。如果不传，则不打印日志。否则将日志打印在终端上

运行结果会输出在`log`目录下。
