#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# Copyright (c) 2021, waitingdodo.
# License: MIT (see LICENSE for details)
# @Time : 2022/3/15 19:52
# @Author : dodo
# @Version：V 0.1
# @desc : 管理各基金的最新净值等相关数据
import js2py
import requests

import history_total_jinzhi_db_mgr
import valid_funds_db_mgr
from fm_utils.utils import dict_only_get, write_file, dict_set, write_json_file_breakline, read_json_file, time_int2str, time_str2int


def tool_init_newest_jinzhi_to_file():
    newest_jinzhi_dict: dict = {}
    valid_fund_id_list: list[str] = valid_funds_db_mgr.get_all_valid_funds_id_list()
    for the_fund_id in valid_fund_id_list:
        history_total_jinzhi_list: list = history_total_jinzhi_db_mgr.get_history_total_jinzhi_list(the_fund_id)
        dict_set(newest_jinzhi_dict, the_fund_id, history_total_jinzhi_list[-1])

    write_json_file_breakline("json/newest_jinzhi.json", newest_jinzhi_dict)
    return


def tool_fix_timestamp_to_file():
    """
    将文件中的int型的时间戳修改为字符串型
    :return:
    """
    ori_dict: dict = read_json_file("json/newest_jinzhi.json")
    for the_fund_id, the_jinzhi_info in ori_dict.items():
        ori_timestamp: int = the_jinzhi_info[0]
        newest_total_jinzhi: float = the_jinzhi_info[1]
        timestamp_str: str = time_int2str(ori_timestamp / 1000, '%Y%m%d_%H%M%S')
        dict_set(ori_dict, the_fund_id, [timestamp_str, newest_total_jinzhi])

    write_json_file_breakline("json/newest_jinzhi.json", ori_dict)
    return


def refresh_all_jinzhi():
    url: str = f'http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?t=1&lx=1&letter=&gsid=&text=&sort=bzdm,asc&page=1,99999&dt=1646487634712&atfc=&onlySale=0'

    response = requests.get(url=url)
    the_text: str = response.text

    js_context = js2py.EvalJs()
    js_context.execute(the_text)
    db_dict: dict = js_context.db.to_dict()
    datas_list: list = dict_only_get(db_dict, "datas")
    showday_list: list = dict_only_get(db_dict, "showday")
    yesterday_timestamp: int = time_str2int(showday_list[0], "%Y-%m-%d")
    former_timestamp: int = time_str2int(showday_list[1], "%Y-%m-%d")
    update_jinzhi(datas_list, yesterday_timestamp, former_timestamp)
    write_file("json/all_jinzhi.js", the_text)

    return


global_newest_jinzhi_dict: dict = None


def init_global_newest_jinzhi_dict():
    global global_newest_jinzhi_dict
    if global_newest_jinzhi_dict is None:
        global_newest_jinzhi_dict = read_json_file("json/newest_jinzhi.json")
    return


def update_jinzhi(datas_list: list, yesterday_timestamp: int, former_timestamp: int):
    init_global_newest_jinzhi_dict()

    for the_data in datas_list:
        fund_id: str = the_data[0]
        # yesterday_unit_jinzhi: str = the_data[3]
        yesterday_total_jinzhi: str = the_data[4]
        # former_unit_jinzhi: str = the_data[5]
        former_total_jinzhi: str = the_data[6]

        if str.isnumeric(yesterday_total_jinzhi):
            yesterday_time_str: str = time_int2str(yesterday_timestamp, '%Y%m%d_%H%M%S')
            dict_set(global_newest_jinzhi_dict, fund_id, [yesterday_time_str, float(yesterday_total_jinzhi)])
            continue

        if str.isnumeric(former_total_jinzhi):
            former_time_str: str = time_int2str(former_timestamp, '%Y%m%d_%H%M%S')
            dict_set(global_newest_jinzhi_dict, fund_id, [former_time_str, float(former_total_jinzhi)])
            continue

    write_json_file_breakline("json/newest_jinzhi.json", global_newest_jinzhi_dict)
    return


def get_newest_jinzhi(fund_id: str) -> (int, float):
    """
    获取指定基金的最新净值
    :param fund_id:
    :return:
    """
    init_global_newest_jinzhi_dict()
    the_info: list = dict_only_get(global_newest_jinzhi_dict, fund_id)
    return time_str2int(the_info[0], '%Y%m%d_%H%M%S'), the_info[1]


if __name__ == '__main__':
    # fix_timestamp_to_file()
    pass
