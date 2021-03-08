import os


# 返回文件目录的所有文件 path, files
def dir_walk(some_dir, level=255):
    if level < 0:
        return
    some_dir = some_dir.rstrip(os.path.sep)
    if not os.path.isdir(some_dir):
        print("{} is not a dir".format(some_dir))
        return
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        for file in files:  # 输出文件信息
            yield root + "/", file
            num_sep_this = root.count(os.path.sep)
            if num_sep + level <= num_sep_this:
                del dirs[:]


total = 0
for d, f in dir_walk("./"):
    if f.split(".")[-1] == "py":
        with open(d+f, "r", encoding="utf-8") as f:
            total += len(f.readlines())
print(total)
