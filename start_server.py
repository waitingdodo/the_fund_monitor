#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time : 2022/3/14 21:23
# @Author : dodo
# @Version：V 0.1
# @desc :  入口脚本
from gevent import monkey

monkey.patch_all()

import os
import newest_jinzhi_mgr
import peak_valley_mgr

import threading
import requests
import json
import bottle

import valid_funds_db_mgr
from fm_utils.utils import dict_set, write_json_file_breakline, dict_only_get, get_current_time, dict_get, print_2_file, time_str2int, time_int2str, read_json_file

global_funds_gz_infos: dict = {}
global_valid_funds_base_info_dict: dict = {}

# 包含成交量和成交额的场内基金数据
global_inner_funds_advance_info_dict: dict = {}


def jsonpgz(the_fund_gz_info=None):
    if not isinstance(the_fund_gz_info, dict):
        log_str: str = f"{get_current_time()} jsonpgz_error! the_fund_gz_info:{the_fund_gz_info}"
        print_2_file("./log/start_server.log", log_str)
        return

    the_fund_id: str = the_fund_gz_info.get("fundcode")
    base_jsonpgz(the_fund_id, the_fund_gz_info)


def base_jsonpgz(the_fund_id: str, the_fund_gz_info: dict = None):
    the_base_info: list = dict_only_get(global_valid_funds_base_info_dict, the_fund_id)

    the_fund_name: str = the_base_info[0]
    the_fund_type: str = the_base_info[1]
    the_fund_stock_rate: float = the_base_info[2]
    the_fund_money: float = the_base_info[3]

    zcgm = the_base_info[4]
    tags_str = the_base_info[5]
    select_stock = the_base_info[6]
    yield_rate = the_base_info[7]
    anti_risk = the_base_info[8]
    stability = the_base_info[9]
    select_time = the_base_info[10]
    hold_share = the_base_info[11]

    # the_pingzhongdata_info: dict = read_json_file(f"./pingzhongdata/{the_fund_id}.json")
    # Data_ACWorthTrend_list: list = dict_only_get(the_pingzhongdata_info, "Data_ACWorthTrend")
    # history_total_jinzhi_list: list = history_total_jinzhi_db_mgr.get_history_total_jinzhi_list(the_fund_id)

    if the_fund_gz_info is None:
        the_fund_gz_info: dict = {}
        dict_set(the_fund_gz_info, "fundcode", the_fund_id)
        dict_set(the_fund_gz_info, "name", the_fund_name)

        # 没有估值增长率
        dict_set(the_fund_gz_info, "gszzl", "0")
        dict_set(the_fund_gz_info, "gztime", "~~无即时估值")

    dict_set(the_fund_gz_info, "type", the_fund_type)
    dict_set(the_fund_gz_info, "stock_rate", the_fund_stock_rate)
    dict_set(the_fund_gz_info, "money", the_fund_money)
    dict_set(the_fund_gz_info, "tags", tags_str)

    dict_set(the_fund_gz_info, "select_stock", select_stock)
    dict_set(the_fund_gz_info, "yield_rate", yield_rate)
    dict_set(the_fund_gz_info, "anti_risk", anti_risk)
    dict_set(the_fund_gz_info, "stability", stability)
    dict_set(the_fund_gz_info, "select_time", select_time)
    dict_set(the_fund_gz_info, "zcgm", zcgm)

    gszzl_str: str = dict_get(the_fund_gz_info, "gszzl", "0")
    gszzl_float: float = float(gszzl_str) / 100
    # 今日单位净值的增长差额
    guzhi_delta: float = 0
    dwjz_str: str = dict_only_get(the_fund_gz_info, "dwjz")
    if gszzl_float != 0 and (dwjz_str is not None):
        dwjz_float: float = float(dwjz_str)
        guzhi_delta = dwjz_float * gszzl_float

    time_int, total_jingzhi = newest_jinzhi_mgr.get_newest_jinzhi(the_fund_id)
    # 20:00-次日9:30 当日净值更新,
    # 9:30-20:00 估值更新, 净值未更新

    jzrq: str = dict_only_get(the_fund_gz_info, "jzrq")
    if jzrq is None:
        # 净值日期数据不存在
        vp_rate_200, vp_rate_100 = peak_valley_mgr.calc_peak_valley_rate(the_fund_id, float(total_jingzhi) + guzhi_delta)
        dict_set(the_fund_gz_info, "vp_rate_200", vp_rate_200)
        dict_set(the_fund_gz_info, "vp_rate_100", vp_rate_100)

        dict_set(global_funds_gz_infos, the_fund_id, the_fund_gz_info)
        return

    jzrq_int: int = time_str2int(jzrq, "%Y-%m-%d")
    if time_int - jzrq_int > 40000:
        vp_rate_200, vp_rate_100 = peak_valley_mgr.calc_peak_valley_rate(the_fund_id, float(total_jingzhi))

        log_str: str = f"{get_current_time()} calc_vp {the_fund_id}, time_int:{time_int2str(time_int, '%Y%m%d_%H%M%S')}, total_jingzhi:{total_jingzhi}, the_fund_gz_info:{the_fund_gz_info}"
        print_2_file("./log/calc_vp.log", log_str)
    else:
        vp_rate_200, vp_rate_100 = peak_valley_mgr.calc_peak_valley_rate(the_fund_id, float(total_jingzhi) + guzhi_delta)

    dict_set(the_fund_gz_info, "vp_rate_200", vp_rate_200)
    dict_set(the_fund_gz_info, "vp_rate_100", vp_rate_100)

    dict_set(global_funds_gz_infos, the_fund_id, the_fund_gz_info)


def start_monitor():
    global global_valid_funds_base_info_dict
    global global_funds_gz_infos
    global global_inner_funds_advance_info_dict

    global_valid_funds_base_info_dict = valid_funds_db_mgr.get_all_valid_funds_info_dict()
    print(f"len(global_valid_funds_dict):{len(global_valid_funds_base_info_dict)}")

    # 对global_funds_gz_infos, global_inner_funds_advance_info_dict进行初始化
    file_path: str = "json/global_funds_gz_infos.json"
    if os.access(file_path, os.F_OK):
        global_funds_gz_infos = read_json_file(file_path)

    file_path: str = "json/global_inner_funds_advance_info_dict.json"
    if os.access(file_path, os.F_OK):
        global_inner_funds_advance_info_dict = read_json_file(file_path)

    while True:
        monitor_once()
        write_json_file_breakline("json/global_funds_gz_infos.json", global_funds_gz_infos)
        write_json_file_breakline("./json/global_inner_funds_advance_info_dict.json", global_inner_funds_advance_info_dict)
        log_str: str = f"{get_current_time()} monitor_once finish"
        print_2_file("./log/start_server.log", log_str)
        # time.sleep(60 * 60 * 24)
        # time.sleep(60)


def refresh_inner_funds_advance_info():
    # 使用便捷方法一次性刷新场内基金的数据
    url: str = f'http://17.push2.eastmoney.com/api/qt/clist/get?cb=inner_funds_callback&pn=1&pz=160&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f5&fs=b:MK0404,b:MK0405,b:MK0406,b:MK0407&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152&_=1646113137838.js'

    response = requests.get(url=url)
    the_text: str = response.text
    exec(the_text)
    print(f"{get_current_time()},  refresh inner_funds_lof, len_text:{len(the_text)}")

    for the_page in [1, 2, 3, 4]:
        url: str = f"http://40.push2.eastmoney.com/api/qt/clist/get?cb=inner_funds_callback&pn={the_page}&pz=200&po=0&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f12&fs=b:MK0021,b:MK0022,b:MK0023,b:MK0024&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152&_=1646634598896"
        response = requests.get(url=url)
        the_text: str = response.text
        exec(the_text)
        print(f"{get_current_time()},  refresh inner_funds_etf, page_no:{the_page} len_text:{len(the_text)}")


def inner_funds_callback(the_dict: dict):
    """
    处理场内基金的相关数据
    :param the_dict: the_dict
    :return:
    """
    the_data: dict = dict_only_get(the_dict, "data")
    the_diff_list: list[dict] = dict_only_get(the_data, "diff")
    print(f"{get_current_time()}, inner_funds_callback, len_the_diff_list:{len(the_diff_list)}")
    for the_info in the_diff_list:
        the_fund_id: str = dict_only_get(the_info, "f12")
        dict_set(global_inner_funds_advance_info_dict, the_fund_id, the_info)


def refresh_base_time() -> tuple[str, str]:
    monitor_the_fund("000001")
    monitor_the_fund("000006")
    monitor_the_fund("000008")
    # 1. 首先确定最新估值日期, 前日日期
    the_gz_info_1: dict = dict_only_get(global_funds_gz_infos, "000001")
    the_gz_info_6: dict = dict_only_get(global_funds_gz_infos, "000006")
    the_gz_info_8: dict = dict_only_get(global_funds_gz_infos, "000008")

    jzrq_1: str = dict_only_get(the_gz_info_1, "jzrq")
    jzrq_6: str = dict_only_get(the_gz_info_6, "jzrq")
    jzrq_8: str = dict_only_get(the_gz_info_8, "jzrq")
    jzrq_timestamp_1: int = time_str2int(jzrq_1, "%Y-%m-%d")
    jzrq_timestamp_6: int = time_str2int(jzrq_6, "%Y-%m-%d")
    jzrq_timestamp_8: int = time_str2int(jzrq_8, "%Y-%m-%d")
    max_jzrq_timestamp: int = max(jzrq_timestamp_1, jzrq_timestamp_6, jzrq_timestamp_8)
    max_jzrq: str = time_int2str(max_jzrq_timestamp, "%Y-%m-%d")

    gztime_1: str = dict_only_get(the_gz_info_1, "gztime")
    gztime_6: str = dict_only_get(the_gz_info_6, "gztime")
    gztime_8: str = dict_only_get(the_gz_info_8, "gztime")
    gztime_timestamp_1: int = time_str2int(gztime_1, "%Y-%m-%d %H:%M")
    gztime_timestamp_6: int = time_str2int(gztime_6, "%Y-%m-%d %H:%M")
    gztime_timestamp_8: int = time_str2int(gztime_8, "%Y-%m-%d %H:%M")
    max_gztime_timestamp: int = max(gztime_timestamp_1, gztime_timestamp_6, gztime_timestamp_8)
    max_gztime: str = time_int2str(max_gztime_timestamp, "%Y-%m-%d %H:%M")
    return max_jzrq, max_gztime


def monitor_once():
    newest_jinzhi_mgr.refresh_all_jinzhi()

    max_jzrq, max_gztime = refresh_base_time()
    refresh_inner_funds_advance_info()
    inner_funds_id_list = global_inner_funds_advance_info_dict.keys()
    valid_funds_id_list = global_valid_funds_base_info_dict.keys()
    # 优先处理场内基金的相关数据
    for inner_fund_id in inner_funds_id_list:
        if inner_fund_id in valid_funds_id_list:
            jsonpgz_inner_fund(inner_fund_id, max_jzrq, max_gztime)
            continue

    for the_fund_id in global_valid_funds_base_info_dict:
        if the_fund_id in inner_funds_id_list:
            continue
        try:
            monitor_the_fund(the_fund_id)
        except Exception as e:
            log_str: str = f"{get_current_time()} exception! cur_fund_id:{the_fund_id}, e:{e}"
            print_2_file("./log/start_server_exception.log", log_str)


def jsonpgz_inner_fund(the_fund_id: str, max_jzrq: str, max_gztime: str):
    # todo 需要给场内基金添加标签
    the_fund_base_info_list: list = dict_only_get(global_valid_funds_base_info_dict, the_fund_id)
    the_inner_fund_advance_info: dict = dict_only_get(global_inner_funds_advance_info_dict, the_fund_id)

    the_name: str = the_fund_base_info_list[0]
    # 昨收单位净值
    yesterday_jinzhi: float = dict_only_get(the_inner_fund_advance_info, "f18")
    # 当前最新价
    cur_gz: float = dict_only_get(the_inner_fund_advance_info, "f2")
    cur_gz_rate: float = dict_only_get(the_inner_fund_advance_info, "f3")
    if cur_gz_rate == "-":
        cur_gz_rate = 0

    the_fund_gz_info: dict = {}
    dict_set(the_fund_gz_info, "fundcode", the_fund_id)
    dict_set(the_fund_gz_info, "name", the_name)
    dict_set(the_fund_gz_info, "jzrq", max_jzrq)
    dict_set(the_fund_gz_info, "dwjz", yesterday_jinzhi)
    dict_set(the_fund_gz_info, "gsz", cur_gz)
    dict_set(the_fund_gz_info, "gszzl", cur_gz_rate)
    dict_set(the_fund_gz_info, "gztime", max_gztime)

    base_jsonpgz(the_fund_id, the_fund_gz_info)
    # log_str: str = f"{get_current_time()} jsonpgz_inner_fund! cur_fund_id:{the_fund_id}, the_fund_gz_info:{the_fund_gz_info}"
    # print_2_file("./log/start_server.log", log_str)


def monitor_the_fund(the_fund_id):
    url = f'http://fundgz.1234567.com.cn/js/{the_fund_id}.js'
    response = requests.get(url=url)
    the_text: str = response.text

    if "fundcode" not in the_text:
        log_str: str = f"{get_current_time()} jsonpgz_error! cur_fund_id:{the_fund_id}, the_fund_gz_info:{the_text}"
        print_2_file("./log/start_server.log", log_str)
        base_jsonpgz(the_fund_id)
        return

    if str.startswith(the_text, "jsonpgz("):
        log_str: str = the_text
        print_2_file("./log/start_server.log", log_str)
        # 该方法过于危险, 应当改用为正则表达式的方法
        exec(the_text)
        # jsonpgz({"fundcode": "013081", "name": "淇¤瘹涓瘉800鏈夎壊鎸囨暟(LOF)C", "jzrq": "2021-09-14", "dwjz": "2.2340", "gsz": "2.2480", "gszzl": "0.63", "gztime": "2021-09-15 15:00"});


@bottle.route('/getFund', method='GET')
def get_fund():
    return json.dumps(global_funds_gz_infos, ensure_ascii=False)


@bottle.route('/editTags', method='GET')
def edit_tags():
    # 修改标签
    # todo 制作忽略功能, 还有合并功能
    fund_id: str = bottle.request.query.fund_id
    new_tags_str: str = bottle.request.query.new_tags

    the_base_info: list = dict_only_get(global_valid_funds_base_info_dict, fund_id)
    if the_base_info is None or new_tags_str is None:
        # 参数检验
        return f"edit_tags failed, {fund_id}, {new_tags_str}"

    old_tags_str: str = the_base_info[5]
    the_base_info[5] = new_tags_str

    the_fund_gz_info: dict = dict_only_get(global_funds_gz_infos, fund_id)
    dict_set(the_fund_gz_info, "tags", new_tags_str)

    print(f"{get_current_time()} edit_tags {fund_id} old_tags:{old_tags_str}, new_tags:{new_tags_str}")
    valid_funds_db_mgr.update_tags(fund_id, new_tags_str)

    return f"edit_tags ok, {fund_id} old_tags:{old_tags_str}, new_tags:{new_tags_str}"


@bottle.route('/static/<filename>')
def server_static(filename):
    return bottle.static_file(filename, root="./static/")


def start_server():
    # 阻塞方法
    bottle.run(host='0.0.0.0', port=8080, debug=True, server='gevent')


if __name__ == "__main__":
    threading.Thread(target=start_monitor).start()
    start_server()


########################################################################################################################################################
########################################################################################################################################################
def read_fenzu_list(the_id: str):
    with open("./json/fenzu.json", "r", encoding="utf-8") as f:
        fenzu_data: dict = json.load(f)
        zu_obj: dict = fenzu_data.get(the_id)

        # 分组暂时通过后台json分组, 前台直接分组的功能暂缓
        # 重要的量化指标 最高点与最低点之间指数, 以最低点为0, 最高点为100, 计算当前指数, N天以来最高, M天以来最低, 连续X天上涨/下跌
