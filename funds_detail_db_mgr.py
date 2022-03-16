#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time : 2022/3/14 21:23
# @Author : dodo
# @Version：V 0.1
# @desc :  对数据库funds_detail.db进行管理

import sqlite3

import json
from dz_utils.dz_utils import read_json_file, dict_only_get, dict_set


def create_table_funds_detail():
    """
    创建一个名为funds_detail.db的数据库
    :return:
    """
    conn: sqlite3.Connection = sqlite3.connect('funds_detail.db')
    print("Opened database successfully")

    c: sqlite3.Cursor = conn.cursor()
    # CODE 基金代号
    # NAME 基金名称
    c.execute('''CREATE TABLE funds_detail
               (id            INTEGER PRIMARY KEY  AUTOINCREMENT   NOT NULL,
               update_time           TEXT    NOT NULL,
               name             TEXT    NOT NULL,
               fund_id          TEXT    NOT NULL,
               detail_info_json TEXT    NOT NULL

               );''')
    print("Table created successfully")
    conn.commit()
    conn.close()


def import_funds_detail_file2db():
    """
    将数据从文件导入到数据库
    :return:
    """
    data_list_will_import_to_db: list = []

    valid_funds_dict = read_json_file("./json/valid_funds.json")
    for the_fund_id, the_base_data in valid_funds_dict.items():
        the_pingzhongdata_info: dict = read_json_file(f"./pingzhongdata/{the_fund_id}.json")

        fS_name: str = dict_only_get(the_pingzhongdata_info, "fS_name")
        update_time: str = dict_only_get(the_pingzhongdata_info, "update_time")
        # 基础信息, 不收录历史累计净值等相关数据
        dict_set(the_pingzhongdata_info, "Data_ACWorthTrend", [])
        detail_info_json: str = json.dumps(the_pingzhongdata_info, ensure_ascii=False)
        data_list_will_import_to_db.append((the_fund_id, fS_name, update_time, detail_info_json))

    conn = sqlite3.connect('funds_detail.db')
    c = conn.cursor()
    print("数据库打开成功")
    c.executemany("INSERT INTO funds_detail (fund_id, name, update_time, detail_info_json) VALUES (?,?,?,?)", data_list_will_import_to_db)
    conn.commit()
    print("数据插入成功")
    conn.close()


if __name__ == "__main__":
    # main()
    # create_table_valid_funds()
    # import_valid_funds_data_file2db()
    # export_valid_funds_list_db2file()
    # print(f"{2.2%1}")

    # 创建数据库
    # create_table_funds_detail()
    import_funds_detail_file2db()
