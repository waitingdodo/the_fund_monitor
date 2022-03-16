#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time : 2022/3/14 21:23
# @Author : dodo
# @Version：V 0.1
# @desc :  定期更新净值数据

import multiprocessing as mp

import js2py
import requests

import history_total_jinzhi_db_mgr
import valid_funds_db_mgr
from dz_utils.dz_utils import get_current_time, dict_set, dict_only_get


def main():
    js_context = js2py.EvalJs()

    valid_fund_id_list: list[str] = valid_funds_db_mgr.get_all_valid_funds_id_list()

    # mp.Pool(3).map(handle_data, fund_id_list)
    for the_fund_id in valid_fund_id_list:
        handle_data(the_fund_id, js_context)


def simple():
    print(f"{get_current_time()} test")
    mp.Pool(3).map(handle_data, ["000001", "000006", "000008"])
    print(f"{get_current_time()} test2")


# http://api.fund.eastmoney.com/pinzhong/LJSYLZS?fundCode=515590&indexcode=000300&type=se&callback=jQuery18306815566419032992_1645745608238&_=1645745956632

def handle_data(the_fund_id: str, js_context=None, only_update_jinzhi_history: bool = True):
    if js_context is None:
        js_context = js2py.EvalJs()

    print(f"{get_current_time()}, {the_fund_id}")
    is_need_update: bool = history_total_jinzhi_db_mgr.is_need_update_by_time(the_fund_id)
    if not is_need_update:
        return

    url = f'https://fund.eastmoney.com/pingzhongdata/{the_fund_id}.js'
    response = requests.get(url=url)

    print(f"{get_current_time()}, {the_fund_id}, len_text:{len(response.text)}")
    js_context.execute(response.text)

    # 先记录更新时间
    update_time: str = get_current_time()

    # 累计净值的相关数据
    jinzhi_history_list: list = js_context.Data_ACWorthTrend.to_list()
    the_fund_name: str = js_context.fS_name
    history_total_jinzhi_db_mgr.update_jinzhi_history(the_fund_id, the_fund_name, update_time, jinzhi_history_list)

    if not only_update_jinzhi_history:
        # todo 数据库更新逻辑尚未完成
        detail_info_dict: dict = {}
        dict_set(detail_info_dict, "update_time", update_time)

        dict_set(detail_info_dict, "fS_name", the_fund_name)
        dict_set(detail_info_dict, "fS_code", js_context.fS_code)
        dict_set(detail_info_dict, "fund_sourceRate", js_context.fund_sourceRate)
        dict_set(detail_info_dict, "fund_Rate", js_context.fund_Rate)

        # 共计5个数据 ["选证能力", "收益率", "抗风险", "稳定性", "择时能力"],
        # ["反映基金挑选证券而实现风险调整后获得超额收益的能力", "根据阶段收益评分，反映基金的盈利能力", "反映基金投资收益的回撤情况", "反映基金投资收益的波动性", "反映基金根据对市场走势的判断，\u003cbr\u003e通过调整仓位及配置而跑赢基金业\u003cbr\u003e绩基准的能力"],
        Data_performanceEvaluation: dict = js_context.Data_performanceEvaluation.to_dict()
        dict_set(detail_info_dict, "Data_performanceEvaluation", dict_only_get(Data_performanceEvaluation, "data"))

        dict_set(detail_info_dict, "stockCodes", js_context.stockCodes.to_list())
        dict_set(detail_info_dict, "stockCodesNew", js_context.stockCodesNew.to_list())

        Data_fluctuationScale: dict = js_context.Data_fluctuationScale.to_dict()
        Data_fluctuationScale_categories: list[str] = dict_only_get(Data_fluctuationScale, "categories")
        Data_fluctuationScale_series: list[dict] = dict_only_get(Data_fluctuationScale, "series")
        if len(Data_fluctuationScale_categories) >= 1 and len(Data_fluctuationScale_series) >= 1:
            the_date: str = Data_fluctuationScale_categories[-1]
            # 资产规模
            the_money: float = dict_only_get(Data_fluctuationScale_series[-1], "y")
            dict_set(detail_info_dict, "Data_fluctuationScale", [the_date, the_money])
        else:
            print(f"error, {get_current_time()}, {the_fund_id}, Data_fluctuationScale error")

        the_asset: dict = js_context.Data_assetAllocation.to_dict()
        categories: list[str] = dict_only_get(the_asset, "categories")
        if len(categories) >= 1:

            series: list[dict] = dict_only_get(the_asset, "series")

            # 股票占净比
            gpzjb_list: list[float] = dict_only_get(series[0], "data")

            # 债券占净比
            zqzjb_list: list[float] = dict_only_get(series[1], "data")

            # 现金占净比
            xjzjb_list: list[float] = dict_only_get(series[2], "data")

            # 净资产
            jzc_list: list[float] = dict_only_get(series[3], "data")

            the_date: str = categories[-1]
            the_gpzjb: float = gpzjb_list[-1]
            the_zqzjb: float = zqzjb_list[-1]
            the_xjzjb: float = xjzjb_list[-1]
            the_jzc: float = jzc_list[-1]
            dict_set(detail_info_dict, "Data_assetAllocation", [the_date, the_gpzjb, the_zqzjb, the_xjzjb, the_jzc])
        else:
            print(f"error, {get_current_time()}, {the_fund_id}, Data_assetAllocation categories error")


if __name__ == "__main__":
    main()
    # simple()
