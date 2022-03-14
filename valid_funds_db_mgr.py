import os
import sqlite3

from fm_utils.utils import read_json_file, get_current_time, dict_only_get, write_json_file_breakline, dict_set, pro_int

db_name: str = 'funds.db'


def update_tags(fund_id: str, new_tags_str: str):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    print(f"UPDATE valid_funds SET tags = '{new_tags_str}' where fund_id = '{fund_id}'")

    c.execute(f"UPDATE valid_funds SET tags = '{new_tags_str}' where fund_id = '{fund_id}'")
    conn.commit()
    conn.close()


def get_all_valid_funds_dict() -> dict:
    valid_funds_list: list = get_all_valid_funds_info_list()
    # 字典必须保证顺序
    valid_funds_list.sort(key=sort_key)
    print(f"len(valid_funds_list): {len(valid_funds_list)}")

    valid_funds_dict: dict = {}
    for the_info in valid_funds_list:
        fund_id = the_info[0]
        name = the_info[1]
        type = the_info[2]
        stock_rate = the_info[3]
        money = the_info[4]
        zcgm = the_info[5]
        tags = the_info[6]
        select_stock = the_info[7]
        yield_rate = the_info[8]
        anti_risk = the_info[9]
        stability = the_info[10]
        select_time = the_info[11]
        # 当前持有份额, 用户自行标记
        hold_share = the_info[12]

        # 股票占比
        stock_rate = pro_int(stock_rate)

        base_info: list = [name, type, stock_rate, money, zcgm, tags, select_stock, yield_rate, anti_risk, stability, select_time, hold_share]
        dict_set(valid_funds_dict, fund_id, base_info)

    return valid_funds_dict


def get_all_valid_funds_id_list() -> list[str]:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    new_cursor = cursor.execute(f"SELECT fund_id FROM valid_funds")

    valid_funds_list: list[str] = []
    for row in new_cursor:
        fund_id = row[0]
        valid_funds_list.append(fund_id)

    conn.close()
    return valid_funds_list


def get_all_valid_funds_info_list() -> list[dict]:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    new_cursor = cursor.execute(f"SELECT fund_id, name, type, stock_rate, money, zcgm, tags, select_stock, yield_rate, anti_risk, stability, select_time, hold_share FROM valid_funds")

    valid_funds_list: list = []
    for row in new_cursor:
        fund_id = row[0]
        name = row[1]
        type = row[2]
        stock_rate = row[3]
        money = row[4]
        zcgm = row[5]
        tags = row[6]
        select_stock = row[7]
        yield_rate = row[8]
        anti_risk = row[9]
        stability = row[10]
        select_time = row[11]
        hold_share = row[12]
        valid_funds_list.append((fund_id, name, type, stock_rate, money, zcgm, tags, select_stock, yield_rate, anti_risk, stability, select_time, hold_share))

    conn.close()
    return valid_funds_list


def export_valid_funds_list_db2file():
    # 从数据库中导出类似于valid_funds.json结构的文件, 按照fund_id排序

    valid_funds_list: list = get_all_valid_funds_info_list()
    valid_funds_list.sort(key=sort_key)

    valid_funds_dict: dict = {}
    for the_info in valid_funds_list:
        fund_id = the_info[0]
        name = the_info[1]
        type = the_info[2]
        stock_rate = the_info[3]
        money = the_info[4]
        zcgm = the_info[5]
        tags = the_info[6]
        select_stock = the_info[7]
        yield_rate = the_info[8]
        anti_risk = the_info[9]
        stability = the_info[10]
        select_time = the_info[11]
        hold_share = the_info[12]

        tag_list: list[str] = str.split(tags)

        stock_rate = pro_int(stock_rate)

        base_info: list = [name, type, stock_rate, money, tag_list]
        if money < 0:
            base_info: list = [name, type, tag_list]
        dict_set(valid_funds_dict, fund_id, base_info)

    write_json_file_breakline("json/valid_funds_exprot_from_db.json", valid_funds_dict)


def sort_key(elem: list):
    return elem[0]


def import_valid_funds_data_file2db():
    # 将数据从文件导入到数据库
    valid_funds_dict = read_json_file("./json/valid_funds.json")
    data_list_will_import_to_db: list = []
    for the_fund_id, the_base_data in valid_funds_dict.items():

        the_fund_name: str = the_base_data[0]
        the_fund_type: str = the_base_data[1]
        the_fund_stock_rate: float = -1000
        the_fund_money: float = -1000
        tags_str = ""

        if len(the_base_data) < 4:
            print(f"{get_current_time()} base_data_error! fund_id:{the_fund_id}, the_base_data:{the_base_data}")
        else:
            the_fund_stock_rate: float = the_base_data[2]
            the_fund_money: float = the_base_data[3]
            tags: list[str] = the_base_data[4]
            tags_str = str.join(" ", tags)

        zcgm: float = -10
        select_stock = -1
        yield_rate = -1
        anti_risk = -1
        stability = -1
        select_time = -1
        # todo pingzhongdata目录已删除, 该段逻辑需要修改
        if os.access(f"./pingzhongdata/{the_fund_id}.json", os.F_OK):
            the_pingzhongdata_info: dict = read_json_file(f"./pingzhongdata/{the_fund_id}.json")
            # 共计5个数据 ["选证能力", "收益率", "抗风险", "稳定性", "择时能力"]
            p_list: list[float] = dict_only_get(the_pingzhongdata_info, "Data_performanceEvaluation")
            if len(p_list) >= 5:
                if (type(p_list[0]) is int) or (type(p_list[0]) is float):
                    select_stock = p_list[0]

                if (type(p_list[0]) is int) or (type(p_list[0]) is float):
                    yield_rate = p_list[1]

                if (type(p_list[0]) is int) or (type(p_list[0]) is float):
                    anti_risk = p_list[2]

                if (type(p_list[0]) is int) or (type(p_list[0]) is float):
                    stability = p_list[3]

                if (type(p_list[0]) is int) or (type(p_list[0]) is float):
                    select_time = p_list[4]

            else:
                print(f"{get_current_time()} Data_performanceEvaluation_list_error! the_fund_id:{the_fund_id}, {p_list}")

            # 资产规模
            Data_fluctuationScale_list: list = dict_only_get(the_pingzhongdata_info, "Data_fluctuationScale")
            if type(Data_fluctuationScale_list) is list and len(Data_fluctuationScale_list) >= 2:
                zcgm: float = Data_fluctuationScale_list[1]
            else:
                print(f"{get_current_time()} Data_fluctuationScale_list_error! the_fund_id:{the_fund_id}, {Data_fluctuationScale_list}")

        # c.execute(f"INSERT INTO valid_funds (fund_id, name, type, stock_rate, money, zcgm, tags, select_stock, yield_rate, anti_risk, stability, select_time, hold_share)  \
        #                             VALUES ({the_fund_id}, {the_fund_name}, {the_fund_type}, {the_fund_stock_rate}, {the_fund_money}, {zcgm}, {tags_str} , {select_stock}, {yield_rate}, {anti_risk}, {stability}, {select_time}, 0)")

        data_list_will_import_to_db.append((the_fund_id, the_fund_name, the_fund_type, the_fund_stock_rate, the_fund_money, zcgm, tags_str, select_stock, yield_rate, anti_risk, stability, select_time, 0))

    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    print("数据库打开成功")
    c.executemany("INSERT INTO valid_funds (fund_id, name, type, stock_rate, money, zcgm, tags, select_stock, yield_rate, anti_risk, stability, select_time, hold_share) VALUES (?,?,?,?,?, ?,?,?,?,?, ?,?,?)",
                  data_list_will_import_to_db)
    conn.commit()
    print("数据插入成功")
    conn.close()


def create_table_valid_funds():
    # 创建数据库
    conn: sqlite3.Connection = sqlite3.connect(db_name)
    print("Opened database successfully")

    c: sqlite3.Cursor = conn.cursor()
    # CODE 基金代号
    # NAME 基金名称
    c.execute('''CREATE TABLE valid_funds
               (id            INTEGER PRIMARY KEY  AUTOINCREMENT   NOT NULL,
               fund_id           TEXT    NOT NULL,
               name           TEXT    NOT NULL,
               type           TEXT    NOT NULL,
               stock_rate   REAL    NOT NULL,
               money        REAL    NOT NULL,
               zcgm         REAL    NOT NULL,
               tags         TEXT    NOT NULL,
               

               select_stock     REAL NOT NULL,
               yield_rate       REAL NOT NULL,
               anti_risk        REAL NOT NULL,
               stability        REAL NOT NULL,
               select_time      REAL NOT NULL,
               
               hold_share  REAL NOT NULL
               );''')
    print("Table created successfully")
    conn.commit()
    conn.close()


def create_table_funds_detail():
    # 创建一个名为funds_detail.db的数据库
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


if __name__ == "__main__":
    # main()
    # create_table_valid_funds()
    # import_valid_funds_data_file2db()
    export_valid_funds_list_db2file()
    # print(f"{2.2%1}")

    # 创建数据库
    # create_table_funds_detail()
