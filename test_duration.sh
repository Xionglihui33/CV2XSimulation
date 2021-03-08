#!/bin/bash

# 参数1：OBU数量
# 参数2：测试次数
# 参数3：如果有，任意值均可，就打印日志

if [[ -f duration.txt ]]; then
    rm duration.txt
fi

if [[ $# < 1 ]]; then
    echo "need more args"
    exit 1
fi

TOTAL_OBU=5
RUN_TIMES=1
LOG_FLAG=false

if [[ $# -ge 1 ]]; then
    TOTAL_OBU=$1
fi

if [[ $# -ge 2 ]]; then
    RUN_TIMES=$2
    
fi

if [[ $# -ge 3 ]]; then
    LOG_FLAG=true
    
fi

echo TOTAL_OBU = $TOTAL_OBU
echo RUN_TIMES = $RUN_TIMES
echo LOG_FLAG = $LOG_FLAG

for i in $( seq 1 $RUN_TIMES)
do
    echo 准备运行第 $i/$RUN_TIMES 次
    if [[ $LOG_FLAG == true ]]; then
        python3 main.py $TOTAL_OBU true
    else
        python3 main.py $TOTAL_OBU
    fi
done
echo ""
echo $TOTAL_OBU 个 OBU 测量 $RUN_TIMES 次耗时结果:
cat duration.txt | awk '{sum+=$1} END {print "平均耗时 =", sum/NR, "ms"}'
