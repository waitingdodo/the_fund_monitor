import json
import time

import chardet


def is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def time_str2struct(ori_time_str: str, format: str):
    time_struct = time.strptime(ori_time_str, format)
    return time_struct


def time_struct2str(ori_time_struct, format: str) -> str:
    time_str: str = time.strftime(format, ori_time_struct)
    return time_str


def time_str2str(ori_time_str: str, ori_format: str, new_format) -> str:
    time_struct = time_str2struct(ori_time_str, ori_format)
    otherStyleTime: str = time_struct2str(time_struct, new_format)
    return otherStyleTime


def time_struct2int(ori_time_struct) -> int:
    timeStamp: int = int(time.mktime(ori_time_struct))
    return timeStamp


def time_int2struct(ori_time_stamp: float):
    return time.localtime(ori_time_stamp)


def time_str2int(ori_time_str: str, ori_format: str) -> int:
    time_struct = time_str2struct(ori_time_str, ori_format)
    return time_struct2int(time_struct)


def time_int2str(ori_time_stamp: float, format: str):
    time_struct = time_int2struct(ori_time_stamp)
    time_str: str = time_struct2str(time_struct, format)
    return time_str


def time_date2timestamp(the_date: str) -> int:
    return time_str2int(the_date, "%Y-%m-%d")


def get_current_time() -> str:
    # 计算当前时间
    # '%Y-%m-%d %H:%M:%S'
    return time_int2str(time.time(), '%Y%m%d_%H%M%S')


def minmax(the_value: float, the_min: float, the_max: float) -> float:
    # 在给定[the_min,the_max]范围内, 获取该值
    return min(max(the_min, the_value), the_max)


def get_timestamp() -> int:
    return int(time.time() * 1000)


# 字典元素的设置操作
def dict_set(the_dict: dict, key: str, value) -> None:
    # 如果the_dict为空, 会抛异常
    # TypeError: 'NoneType' object does not support item assignment
    the_dict[key] = value


# 字典元素的取值操作
def dict_get(the_dict: dict, key: str, default_value):
    # 如果the_dict为空, 会抛异常
    # TypeError: descriptor 'setdefault' for 'dict' objects doesn't apply to a 'NoneType' object
    return dict.setdefault(the_dict, key, default_value)


# 不需要写默认值, 一旦不存在, 则返回None
def dict_only_get(the_dict: dict, key: str):
    # 如果the_dict为空, 会抛异常
    # TypeError: descriptor 'get' for 'dict' objects doesn't apply to a 'NoneType' object
    return dict.get(the_dict, key)


def write_json_file(file_name: str, obj):
    with open(file_name, "w", encoding="utf-8") as f2:
        # ensure_ascii=True会将中文字符转写成ascii代码, 所以不应该使用该参数
        json.dump(obj, f2, ensure_ascii=False)


def write_json_file_breakline(file_name: str, obj):
    json_str: str = json.dumps(obj, ensure_ascii=False)
    json_str = json_str.replace("],", "],\n").replace("},", "},\n")
    with open(file_name, "w", encoding="utf-8") as f2:
        result = f2.write(json_str)
        f2.flush()


def read_json_file(file_name: str):
    # 当文件不存在, 此处会抛异常
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)


# 将日志写入文件中
def print_2_file(file_name: str, log_obj):
    with open(file_name, "a+") as f2:
        print(log_obj, file=f2)


# 将浮点数list转为字符串list, 并且保留小数点后两位
def trans_list_percent_2(values: list[float]) -> list[str]:
    result: list[str] = []
    for the_value in values:
        result.append(get_percent_2(the_value))

    return result


# 将小数转为带有小数点后两位的百分比字符串 服从四舍五入
# 自作多情了, 原来"%.2f"天生支持四舍五入
def get_percent_2(num_float: float) -> str:
    return "%.2f" % (num_float * 100)


# 将小数转为带有小数点后1位的百分比字符串 服从四舍五入
def get_percent_1(num_float: float) -> str:
    return "%.1f" % (num_float * 100)


# 将小数转为带有小数点后4位的字符串, 服从四舍五入
def get_float_4(num_float: float) -> str:
    return "%.4f" % (num_float)


def safe_float(param: str) -> float:
    try:
        return float(param)
    except Exception as e:
        log_str: str = f"ERROR!, {get_current_time()}, param:{param} {e}"
        print(log_str)
        print_2_file("./error_safe_float.log", log_str)
        return None


def safe_int(param: str) -> int:
    try:
        return int(param)
    except Exception as e:
        log_str: str = f"ERROR!, {get_current_time()}, param:{param} {e}"
        print(log_str)
        print_2_file("./error_safe_float.log", log_str)
        return None


def calc_avg(values: list[float]) -> float:
    the_len: int = len(values)
    if the_len <= 0:
        raise Exception

    return sum(values) / the_len


def get_custom_member_list(values: list[tuple], index: int) -> list:
    result: list = []
    for the_tuple in values:
        result.append(the_tuple[index])

    return result


def read_bytes_from_file(file_name: str) -> bytes:
    with open(file_name, "rb") as f:
        content: bytes = f.read()
        return content


def read_str_from_file(file_name: str) -> str:
    with open(file_name, "r", encoding="utf-8") as f:
        content: str = f.read()
        return content


def write_file(file_name: str, content: str):
    with open(file_name, "w", encoding="utf-8", newline="") as f2:
        result = f2.write(content)
        f2.flush()


def fix_unicode_file(file_name: str):
    content_bytes: bytes = read_bytes_from_file(file_name)
    result: dict = chardet.detect(content_bytes)
    if dict_only_get(result, 'encoding') != 'ascii':
        print(f"{file_name}, no need fix")
        return
    content_fix: str = content_bytes.decode("unicode_escape")
    write_file(file_name, content_fix)

    print(f"{file_name}, fix")
    return


# def fix_unicode_file2(file_name: str):
#     content_str: str = read_str_from_file(file_name)
#     result: dict = chardet.detect(content_str.encode("utf-8"))
#     if dict_only_get(result, 'encoding') != 'ascii':
#         print(f"{file_name}, no need fix")
#         return
#     content_fix: str = content_str.encode("utf-8").decode("unicode_escape")
#     write_file(file_name, content_fix)
#
#     print(f"{file_name}, fix")
#     return


def str2bytes(ori_str: str, the_encoding: str = 'utf-8') -> bytes:
    return str.encode(ori_str, encoding=the_encoding)


def bytes2str(ori_bytes: bytes, the_encoding: str = 'utf-8') -> str:
    return str(ori_bytes, encoding=the_encoding)


def bytes2str_2(ori_bytes: bytes, the_encoding: str = 'utf-8') -> str:
    return bytes.decode(ori_bytes, encoding=the_encoding)


def pro_int(a: float):
    if a % 1 == 0:
        return int(a)

    return a
