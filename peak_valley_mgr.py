#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# Copyright (c) 2021, waitingdodo.
# License: MIT (see LICENSE for details)
# @Time : 2022/3/15 7:45
# @Author : dodo
# @Version：V 0.1
# @desc : 用于管理计算峰谷值时所需要的参数, 每隔10天更新一次
import history_total_jinzhi_db_mgr
import valid_funds_db_mgr
from fm_utils.utils import get_current_time, dict_set, write_json_file_breakline, read_json_file, dict_only_get, print_2_file


def tool_init_params_to_file():
    peak_valley_params_dict: dict = {}
    valid_fund_id_list: list[str] = valid_funds_db_mgr.get_all_valid_funds_id_list()
    for the_fund_id in valid_fund_id_list:
        history_total_jinzhi_list: list = history_total_jinzhi_db_mgr.get_history_total_jinzhi_list(the_fund_id)
        peak_200, valley_200, peak_100, valley_100 = calc_peak_valley_value(the_fund_id, history_total_jinzhi_list)
        dict_set(peak_valley_params_dict, the_fund_id, [peak_200, valley_200, peak_100, valley_100])

    the_dict: dict = {}
    # 先记录更新时间
    update_time: str = get_current_time()
    dict_set(the_dict, "update_time", update_time)
    dict_set(the_dict, "params", peak_valley_params_dict)
    write_json_file_breakline("json/peak_valley_params_dict.json", the_dict)
    return


def tool_fix_file():
    """
    修复原先的文件, 添加update_time, params两个参数
    :return:
    """
    ori_dict: dict = read_json_file("json/peak_valley_params_dict.json")
    if dict_only_get(ori_dict, "update_time") is None:
        the_dict: dict = {}
        # 先记录更新时间
        update_time: str = get_current_time()
        dict_set(the_dict, "update_time", update_time)
        dict_set(the_dict, "params", ori_dict)
        write_json_file_breakline("json/peak_valley_params_dict.json", the_dict)
    return


def calc_peak_valley_value(fund_id: str, history_total_jinzhi_list: list) -> (float, float, float, float):
    if len(history_total_jinzhi_list) < 100:
        flag: int = -10000 - len(history_total_jinzhi_list)
        # 净值历史记录不足100日, 则无法计算峰谷值
        return flag, flag, flag, flag

    last_100_list: list = history_total_jinzhi_list[-100:]
    trim_data(fund_id, last_100_list)
    last_100_list.sort(key=sort_key)
    valley_100: float = last_100_list[10][1]
    peak_100: float = last_100_list[90][1]

    if len(history_total_jinzhi_list) < 200:
        flag: int = -10000 - len(history_total_jinzhi_list)
        # 净值历史记录介入100日与200日之间, 只能计算100日的峰谷值
        return flag, flag, peak_100, valley_100

    last_200_list: list = history_total_jinzhi_list[-200:]
    trim_data(fund_id, last_200_list)
    last_200_list.sort(key=sort_key)
    valley_200: float = last_200_list[20][1]
    peak_200: float = last_200_list[180][1]

    return peak_200, valley_200, peak_100, valley_100


def trim_data(fund_id: str, last_slice_list: list):
    """
    将200日累计净值中的空数据擦除
    :param fund_id:
    :param last_slice_list:
    :return:
    """
    last_jz: float = 1
    for i, _ in enumerate(last_slice_list):
        if last_slice_list[i][1] is None:
            print(f"{get_current_time()} trim_data! the_fund_id:{fund_id}, the_info:{last_slice_list[i]}")
            last_slice_list[i][1] = last_jz
        else:
            last_jz = last_slice_list[i][1]


def sort_key(elem: list):
    return elem[1]


global_peak_valley_params_dict: dict = None


def calc_peak_valley_rate(fund_id: str, total_guzhi: float) -> (int, int):
    # 取近200条数据, 从低到高排列, 90%位置定义为100, 10%位置定义为0, 计算净值所处位置和估值所处位置
    global global_peak_valley_params_dict
    if global_peak_valley_params_dict is None:
        ori_dict: dict = read_json_file("./json/peak_valley_params_dict.json")
        global_peak_valley_params_dict = dict_only_get(ori_dict, "params")
        # todo 按照时间, 每10天更新一次
        update_time: str = dict_only_get(ori_dict, "update_time")

    params: list[float] = dict_only_get(global_peak_valley_params_dict, fund_id)
    peak_200 = params[0]
    valley_200 = params[1]
    peak_100 = params[2]
    valley_100 = params[3]
    if peak_100 < -1:
        # 历史记录不足100日, 不需计算
        return peak_200, peak_100

    vp_100: int = -20001
    unit_100: float = (peak_100 - valley_100) / 100
    if unit_100 <= 0:
        log_str: str = f"{get_current_time()} unit_error! the_fund_id:{fund_id}, peak_100:{peak_100}, valley_100:{valley_100}"
        print_2_file("./log/start_server.log", log_str)
        vp_100 = -20000
    else:
        vp_100 = int((total_guzhi - valley_100) / unit_100)

    if peak_200 < -1:
        return peak_200, vp_100

    vp_200: int = -20001
    unit_200: float = (peak_200 - valley_200) / 100
    if unit_200 <= 0:
        log_str: str = f"{get_current_time()} unit_error! the_fund_id:{fund_id}, peak_200:{peak_200}, valley_200:{valley_200}"
        print_2_file("./log/start_server.log", log_str)
        vp_200 = -20000
    else:
        vp_200 = int((total_guzhi - valley_200) / unit_200)

    return vp_200, vp_100


if __name__ == '__main__':
    # tool_init_params_to_file()
    tool_fix_file()
