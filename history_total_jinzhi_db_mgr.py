import sqlite3
import time

import json
from fm_utils.utils import read_json_file, dict_only_get, time_str2int, get_current_time

db_name: str = 'history_total_jinzhi.db'
table_name: str = 'history_total_jinzhi'


def create_table_history_total_jinzhi():
    # 创建一个名为history_total_jinzhi.db的数据库
    conn: sqlite3.Connection = sqlite3.connect('history_total_jinzhi.db')
    print("Opened database successfully")

    c: sqlite3.Cursor = conn.cursor()
    # CODE 基金代号
    # NAME 基金名称
    c.execute('''CREATE TABLE history_total_jinzhi
               (id                          INTEGER PRIMARY KEY  AUTOINCREMENT   NOT NULL,
               update_time                  TEXT    NOT NULL,
               name                         TEXT    NOT NULL,
               fund_id                      TEXT    NOT NULL,
               history_total_jinzhi_json    TEXT    NOT NULL

               );''')
    print("Table created successfully")
    conn.commit()
    conn.close()


def import_history_total_jinzhi_file2db():
    # 将数据从文件导入到数据库
    data_list_will_import_to_db: list = []

    valid_funds_dict = read_json_file("./json/valid_funds.json")
    for the_fund_id, the_base_data in valid_funds_dict.items():
        the_pingzhongdata_info: dict = read_json_file(f"./pingzhongdata/{the_fund_id}.json")

        fS_name: str = dict_only_get(the_pingzhongdata_info, "fS_name")
        update_time: str = dict_only_get(the_pingzhongdata_info, "update_time")
        # 基础信息, 不收录历史累计净值等相关数据
        Data_ACWorthTrend: list = dict_only_get(the_pingzhongdata_info, "Data_ACWorthTrend")
        history_total_jinzhi_json: str = json.dumps(Data_ACWorthTrend, ensure_ascii=False)
        data_list_will_import_to_db.append((the_fund_id, fS_name, update_time, history_total_jinzhi_json))

    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    print("数据库打开成功")
    c.executemany("INSERT INTO history_total_jinzhi (fund_id, name, update_time, history_total_jinzhi_json) VALUES (?,?,?,?)", data_list_will_import_to_db)
    conn.commit()
    print("数据插入成功")
    conn.close()


def get_history_total_jinzhi_list(fund_id) -> list:
    # 从数据库中获取净值数据列表
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    new_cursor = cursor.execute(f"SELECT history_total_jinzhi_json FROM {table_name} WHERE fund_id = '{fund_id}' ")

    history_total_jinzhi_list: list = []
    for row in new_cursor:
        history_total_jinzhi_json: str = row[0]
        history_total_jinzhi_list = json.loads(history_total_jinzhi_json)

    conn.close()
    return history_total_jinzhi_list


def get_update_time(fund_id) -> str:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    new_cursor = cursor.execute(f"SELECT update_time FROM {table_name} WHERE fund_id = '{fund_id}' ")

    # 如果当前需要查询的数据不存在, 则返回none
    update_time: str = None
    for row in new_cursor:
        update_time: str = row[0]

    conn.close()
    return update_time


def is_need_update_by_time(fund_id) -> bool:
    the_update_time: str = get_update_time(fund_id)
    if the_update_time is None or len(the_update_time) < 3:
        print(f"update_time error, the_update_time:{the_update_time}")
        return True

    the_update_time_int: int = time_str2int(the_update_time, '%Y%m%d_%H%M%S')
    # print(f"{time.time()} {the_update_time_int} {the_update_time} {time.time() - the_update_time_int}")
    if time.time() - the_update_time_int < 70000:
        # 不需要更新
        return False

    return True


def insert_info(fund_id: str, fund_name: str, update_time: str, jinzhi_history_list: list):
    jinzhi_history_list_json: str = json.dumps(jinzhi_history_list)
    print(f"{get_current_time()} will insert_info_to_db, {fund_id}, {update_time}, len:{len(jinzhi_history_list_json)} \n")

    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    the_data: tuple = (fund_id, fund_name, update_time, jinzhi_history_list_json)
    c.execute("INSERT INTO history_total_jinzhi (fund_id, name, update_time, history_total_jinzhi_json) VALUES (?,?,?,?)", the_data)
    conn.commit()
    conn.close()


def update_jinzhi_history(fund_id: str, fund_name: str, update_time: str, jinzhi_history_list: list):
    # 先查询是否存在当前词条
    the_update_time: str = get_update_time(fund_id)
    if the_update_time is None:
        # 当前数据库中没有该词条, 需要直接插入
        insert_info(fund_id, fund_name, update_time, jinzhi_history_list)
        return

    jinzhi_history_list_json: str = json.dumps(jinzhi_history_list)
    print(f"{get_current_time()} will update jingzhi_history, {fund_id}, {update_time}, len:{len(jinzhi_history_list_json)} \n")

    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute(f"UPDATE {table_name} SET update_time = '{update_time}' , history_total_jinzhi_json = '{jinzhi_history_list_json}' where fund_id = '{fund_id}'")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # 创建数据库
    # create_table_history_total_jinzhi()
    # import_history_total_jinzhi_file2db()
    pass
