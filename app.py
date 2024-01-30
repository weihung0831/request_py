import datetime
import json
import os
import time
import math

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    create_engine,
    desc,
    exists,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 載入 json 資料
# 獲取當前日期並轉換為 "YYYYMMDD" 格式
now = datetime.datetime.now().strftime("%Y-%m-%d").replace("-", "")
# 打開對應日期的 json 檔案並讀取資料
with open(f"./data/{now}data.json", "r") as f:
    jsonj_data = json.load(f)

# 載入環境變數
load_dotenv()
# 獲取資料庫主機、使用者名稱和資料庫名稱
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
SQLITE_DB_NAME = os.getenv("SQLITE_DB_NAME")

# 連接到 MySQL 資料庫
# 使用 pymysql 作為資料庫驅動
engine = create_engine(f"mysql+pymysql://{DB_USER}@{DB_HOST}/{DB_NAME}")

# 建立元數據物件
metadata = MetaData()
# 反映資料庫結構
metadata.reflect(bind=engine)

# 設定要操作的資料表名稱
table_name = "work_number"
# 獲取資料表物件
work_number_table = metadata.tables[table_name]

# 建立 Session 類別
Session = sessionmaker(bind=engine)
# 建立 Session 實例
session = Session()

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def test():
    return render_template("home.html")


@app.route("/work_order")
def work_order():
    return render_template("work_order.html")


@app.route("/dispatch_work_order")
def dispatch_work_order():
    return render_template("dispatch_work_order.html")


@app.route("/not_dispatch_work_order")
def not_dispatch_work_order():
    return render_template("not_dispatch_work_order.html")


@app.route("/api/get_all_work_order_data")
def get_all_work_order_data():
    """
    get_all_work_order_data 函數結合了 get_dispatch_work_order_data 和 get_no_dispatch_work_order_data 的程式碼，
    從 JSON 檔案中提取工作訂單數據，查詢數據庫以獲取額外的資訊，並返回處理後的工作訂單數據。 
    :return: 一個包含以下資訊的 JSON 字串： 
    - "dispatch_result": 代表已分派工作訂單的字典列表，
    每個字典包含以下鍵："work_order_number"、"work_order_quantity"、"undelivered_quantity"、"total_quantity" 和 "remaining_quantity"。 
    - "not_dispatch_result": 代表未分派工作訂單的字典列表，
    每個字典包含以下鍵："work_order_number"、"work_order_quantity"、"undelivered_quantity"、"total_quantity" 和 "remaining_quantity"。
    """
    # 將 get_dispatch_work_order_data 和 get_no_dispatch_work_order_data 的代碼合併
    start_time = time.time()
    # 從 json 資料中提取工單號碼
    work_order_numbers = [data["AUFNR"] for data in jsonj_data]
    # 初始化一個字典，用於存儲每個工單的相關資訊
    dispatch_work_order = {}
    not_dispatch_work_order = {}
    # 初始化一個集合，用於存儲已經在工單資料字典中的工單名稱
    work_order_names = set()

    # 迴圈處理每個工單
    for work_order_number in work_order_numbers:
        try:
            # 從資料庫中查詢工單號碼
            db_work_order_number_exists = session.query(
                session.query(work_number_table)
                .filter(work_number_table.c.name.like(f"%{work_order_number}%"))
                .exists()
            ).scalar()
            # 如果資料庫中有查詢到工單號碼，則更新工單的數量
            if db_work_order_number_exists:
                db_work_order_total = (
                    session.query(work_number_table)
                    .filter(work_number_table.c.name.like(f"%{work_order_number}%"))
                    .order_by(desc(work_number_table.c.total))
                    .all()
                )
                # 迴圈處理查詢結果，並更新工單的總數量
                for record in db_work_order_total:
                    work_order_name = record.name.split("-")[0]
                    # 如果工單名稱還未在工單名稱集合中，則將其添加到集合中，並在工單資料字典中為其初始化資訊
                    if work_order_name not in work_order_names:
                        work_order_names.add(work_order_name)
                        dispatch_work_order[work_order_name] = {
                            "work_order_number": work_order_name,
                            "work_order_quantity": 0,
                            "undelivered_quantity": 0,
                            "total_quantity": 0,
                            "remaining_quantity": 0,
                        }
                    # 如果工單名稱在記錄的名稱中，則將記錄的總數量添加到工單資料字典中對應的工單的總數量上
                    if work_order_name in record.name:
                        dispatch_work_order[work_order_name][
                            "total_quantity"
                        ] += record.total
        # 捕獲並打印異常
        except Exception as e:
            print(e)

    # 遍歷 jsonj_data 中的每一條數據
    for data in jsonj_data:
        # 從 "AUFNR" 字段中獲取工作訂單名稱
        work_order_name = data["AUFNR"].split("-")[0]

        # 如果工單名稱不在未派發工單的字典中, 則在字典中新增該工單名稱，並初始化相關數量為 0
        if work_order_name not in not_dispatch_work_order:
            not_dispatch_work_order[work_order_name] = {
                "work_order_number": work_order_name,
                "work_order_quantity": 0,
                "undelivered_quantity": 0,
            }

        # 查詢數據庫中是否存在該工作訂單號碼
        db_work_order_number_exists = session.query(
            exists().where(work_number_table.c.name.like(f"%{data['AUFNR']}%"))
        ).scalar()

        # 如果數據庫中不存在該工作訂單號碼，則更新 work_order_data 中的數據
        if not db_work_order_number_exists:
            not_dispatch_work_order[work_order_name]["work_order_quantity"] += data[
                "QTY"
            ]
            not_dispatch_work_order[work_order_name]["undelivered_quantity"] += data[
                "UN_QTY"
            ]
        # 如果存在資料庫中存在該工作訂單號碼，則刪除該工作訂單號碼
        else:
            del not_dispatch_work_order[work_order_name]

    # 關閉資料庫連接
    session.close()

    # 將 json 資料轉換為字典，以工單號碼為鍵
    jsonj_data_dict = {item["AUFNR"]: item for item in jsonj_data}
    # 迴圈處理工單資料字典，並更新工單的數量資訊
    for order_number, data in dispatch_work_order.items():
        # 從 jsonj_data_dict 字典中取出與當前工單號碼對應的項目
        json_item = jsonj_data_dict.get(order_number)
        # 如果該項目存在
        if json_item is not None:
            # 更新工單資料字典中對應的工單的工單數量
            data["work_order_quantity"] = json_item["QTY"]
            # 更新工單資料字典中對應的工單的未交付數量
            data["undelivered_quantity"] = json_item["UN_QTY"]
            # 計算並更新工單資料字典中對應的工單的剩餘數量
            data["remaining_quantity"] = (
                data["undelivered_quantity"] - data["total_quantity"]
            )

    # 迴圈處理 JSON 資料
    for data in jsonj_data:
        # 從 JSON 資料中取出工單名稱，並分割出工單號碼
        work_order_name = data["AUFNR"].split("-")[0]
        # 如果工單號碼在已派發工單的字典中, 則更新該工單的數量和未交付數量
        if work_order_name in dispatch_work_order:
            dispatch_work_order[work_order_name]["work_order_quantity"] = data["QTY"]
            dispatch_work_order[work_order_name]["undelivered_quantity"] = data[
                "UN_QTY"
            ]

    end_time = time.time()
    print("執行時間：", end_time - start_time)
    # 返回處理後的工單資料
    return json.dumps(
        {
            "dispatch_result": list(dispatch_work_order.values()),
            "not_dispatch_result": list(not_dispatch_work_order.values()),
            "status": 200,
            "message": "success",
        }
    )


# 定義 API 路由，用於獲取工單數據
@app.route("/api/get_dispatch_work_order_data")
def get_dispatch_work_order_data():
    """
    這個 get_dispatch_work_order_data 函數從 JSON 檔案中獲取工單數據，查詢資料庫以獲取額外資訊，並將處理後的工單數據以 JSON 回應的形式返回。
    :return: 包含處理後的工單數據的 JSON 字串。
    """
    start_time = time.time()
    # 從 json 資料中提取工單號碼
    work_order_numbers = [data["AUFNR"] for data in jsonj_data]
    # 初始化一個字典，用於存儲每個工單的相關資訊
    work_order_data = {}
    # 初始化一個集合，用於存儲已經在工單資料字典中的工單名稱
    work_order_names = set()

    # 迴圈處理每個工單
    for work_order_number in work_order_numbers:
        try:
            # 從資料庫中查詢工單號碼
            db_work_order_number_exists = session.query(
                session.query(work_number_table)
                .filter(work_number_table.c.name.like(f"%{work_order_number}%"))
                .exists()
            ).scalar()
            # 如果資料庫中有查詢到工單號碼，則更新工單的數量
            if db_work_order_number_exists:
                db_work_order_total = (
                    session.query(work_number_table)
                    .filter(work_number_table.c.name.like(f"%{work_order_number}%"))
                    .order_by(desc(work_number_table.c.total))
                    .all()
                )
                # 迴圈處理查詢結果，並更新工單的總數量
                for record in db_work_order_total:
                    work_order_name = record.name.split("-")[0]
                    # 如果工單名稱還未在工單名稱集合中，則將其添加到集合中，並在工單資料字典中為其初始化資訊
                    if work_order_name not in work_order_names:
                        work_order_names.add(work_order_name)
                        work_order_data[work_order_name] = {
                            "work_order_number": work_order_name,
                            "work_order_quantity": 0,
                            "undelivered_quantity": 0,
                            "total_quantity": 0,
                            "remaining_quantity": 0,
                        }
                    # 如果工單名稱在記錄的名稱中，則將記錄的總數量添加到工單資料字典中對應的工單的總數量上
                    if work_order_name in record.name:
                        work_order_data[work_order_name][
                            "total_quantity"
                        ] += record.total
        # 捕獲並打印異常
        except Exception as e:
            print(e)
    # 關閉資料庫連接
    session.close()

    # 將 json 資料轉換為字典，以工單號碼為鍵
    jsonj_data_dict = {item["AUFNR"]: item for item in jsonj_data}
    # 迴圈處理工單資料字典，並更新工單的數量資訊
    for order_number, data in work_order_data.items():
        # 從 jsonj_data_dict 字典中取出與當前工單號碼對應的項目
        json_item = jsonj_data_dict.get(order_number)
        # 如果該項目存在
        if json_item is not None:
            # 更新工單資料字典中對應的工單的工單數量
            data["work_order_quantity"] = json_item["QTY"]
            # 更新工單資料字典中對應的工單的未交付數量
            data["undelivered_quantity"] = json_item["UN_QTY"]
            # 計算並更新工單資料字典中對應的工單的剩餘數量
            data["remaining_quantity"] = (
                data["undelivered_quantity"] - data["total_quantity"]
            )
    end_time = time.time()
    print("執行時間：", end_time - start_time)
    # 返回處理後的工單資料
    return json.dumps(
        {
            "result": list(work_order_data.values()),
            "status": 200,
            "message": "success",
        }
    )


@app.route("/api/get_no_dispatch_work_order_data")
def get_no_dispatch_work_order_data():
    start_time = time.time()  # 記錄開始時間
    page = int(request.args.get('page', 1))  # 獲取頁碼，預設為1
    limit = int(request.args.get('limit', 10))  # 獲取每頁的數量限制，預設為10
    start_index = (page - 1) * limit  # 計算起始索引
    end_index = start_index + limit  # 計算結束索引
    work_order_data = {}  # 初始化工作訂單資料字典

    # 從 jsonj_data 中獲取資料
    for data in jsonj_data:
        work_order_name = data["AUFNR"].split("-")[0]  # 獲取工作訂單名稱
        # 如果工作訂單名稱不在工作訂單資料字典中，則添加到字典中
        if work_order_name not in work_order_data:
            work_order_data[work_order_name] = {
                "work_order_number": work_order_name,
                "work_order_quantity": 0,
                "undelivered_quantity": 0,
            }

        # 檢查資料庫中是否存在工作訂單號碼
        db_work_order_number_exists = session.query(
            exists().where(work_number_table.c.name.like(f"%{data['AUFNR']}%"))
        ).scalar()

        # 如果資料庫中不存在工作訂單號碼，則更新工作訂單資料字典中的數量
        if not db_work_order_number_exists:
            work_order_data[work_order_name]["work_order_quantity"] += data["QTY"]
            work_order_data[work_order_name]["undelivered_quantity"] += data["UN_QTY"]
        else:
            # 如果資料庫中存在工作訂單號碼，則從工作訂單資料字典中刪除該訂單
            del work_order_data[work_order_name]
    session.close()  # 關閉資料庫連接

    # 再次從 jsonj_data 中獲取資料，並更新工作訂單資料字典中的數量
    for data in jsonj_data:
        work_order_name = data["AUFNR"].split("-")[0]
        if work_order_name in work_order_data:
            work_order_data[work_order_name]["work_order_quantity"] = data["QTY"]
            work_order_data[work_order_name]["undelivered_quantity"] = data["UN_QTY"]

    # 從工作訂單資料字典中獲取分頁資料
    paginated_data = list(work_order_data.values())[start_index:end_index]
    total_pages = math.ceil(len(work_order_data) / limit)  # 計算總頁數

    end_time = time.time()  # 記錄結束時間
    print("執行時間：", end_time - start_time)  # 輸出執行時間
    # 返回分頁資料、總頁數、狀態碼和訊息
    return json.dumps(
        {
            "result": paginated_data,
            "total_pages": total_pages,
            "status": 200,
            "message": "success",
        }
    )

def formate_time():
    return datetime.datetime.now().replace(microsecond=0)


Base = declarative_base()


class WaterLevel(Base):
    __tablename__ = "water_level"
    id = Column(Integer, primary_key=True)
    work_number = Column(String(255))
    water_level = Column(Float)
    created_at = Column(DateTime, default=formate_time)


@app.route("/api/get_water_level_data", methods=["POST"])
def send_water_level_data():
    """
    send_water_level_data 函數接收 JSON 數據，創建一個數據庫引擎，創建一個會話，向數據庫添加一個新的 water_level，
    提交更改，並返回一個帶有成功消息的 JSON 響應。 
    :return: 一個帶有 200 狀態碼、成功消息和接收到的數據的 JSON 響應。
    """
    data = request.get_json()
    engine = create_engine(f"sqlite:///{SQLITE_DB_NAME}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    water_level = WaterLevel(
        work_number=data["work_order_number"], water_level=data["water_level"]
    )
    session.add(water_level)
    session.commit()
    return jsonify({"status": 200, "message": "success", "data": data})


@app.route("/api/get_water_level_data", methods=["GET"])
def get_water_level_data():
    """
    get_water_level_data 函數從 SQLite 數據庫中獲取每個不同 work_number 的最新水位數據，並將其作為 JSON 響應返回。
    :return: 一個帶有 200 狀態碼、"success" 消息和 "data" 字段中的水位數據的 JSON 響應。
    """
    engine = create_engine(f"sqlite:///{SQLITE_DB_NAME}")
    Session = sessionmaker(bind=engine)
    session = Session()

    work_numbers = session.query(WaterLevel.work_number).distinct().all()
    water_level_data = []
    for number in work_numbers:
        water_level = (
            session.query(WaterLevel)
            .filter(WaterLevel.work_number == number[0])
            .order_by(desc(WaterLevel.created_at))
            .first()
        )
        if water_level:
            water_level_dict = water_level.__dict__
            # 刪除字典中的 "_sa_instance_state" 鍵，因為這是 SQLAlchemy 的內部屬性，不應該被序列化
            del water_level_dict["_sa_instance_state"]
            water_level_data.append(water_level_dict)
    session.close()
    return jsonify({"status": 200, "message": "success", "data": water_level_data})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
