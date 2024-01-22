import datetime
import json
import os

from dotenv import load_dotenv
from flask import Flask, render_template
from sqlalchemy import MetaData, create_engine, desc
from sqlalchemy.orm import sessionmaker

# load json data
now = datetime.datetime.now().strftime("%Y-%m-%d").replace("-", "")
with open(f"./data/{now}data.json", "r") as f:
    jsonj_data = json.load(f)

# load env
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")

# connect to mysql
engine = create_engine(f"mysql+pymysql://{DB_USER}@{DB_HOST}/{DB_NAME}")

metadata = MetaData()
metadata.reflect(bind=engine)

table_name = "work_number"
work_number_table = metadata.tables[table_name]

Session = sessionmaker(bind=engine)
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




# 定義 API 路由，用於獲取工單數據
@app.route("/api/get_dispatch_work_order_data")
def get_dispatch_work_order_data():
    """
    這個 get_dispatch_work_order_data 函數從 JSON 檔案中獲取工單數據，查詢資料庫以獲取額外資訊，並將處理後的工單數據以 JSON 回應的形式返回。
    :return: 包含處理後的工單數據的 JSON 字串。
    """
    # 從 json 資料中提取工單號碼
    work_order_number = [data["AUFNR"] for data in jsonj_data]
    # 初始化一個字典，用於存儲每個工單的相關資訊
    work_order_data = {}

    # 迴圈處理每個工單
    for i in range(len(jsonj_data)):
        try:
            # 從資料庫中查詢工單號碼
            db_work_order_number = (
                session.query(work_number_table)
                .filter(work_number_table.c.name.like(f"%{work_order_number[i]}%"))
                .order_by(desc(work_number_table.c.time))
                .first()
            )

            # 如果查詢到工單號碼
            if db_work_order_number:
                # 將查詢結果轉換為字典
                db_work_order_number_dict = dict(
                    zip(work_number_table.c.keys(), db_work_order_number)
                )
                # 獲取工單名稱
                work_order_name = db_work_order_number_dict["name"].split("-")[0]

                # 如果工單名稱還未在工單資料字典中，則初始化該工單的資訊
                if work_order_name not in work_order_data:
                    work_order_data[work_order_name] = {
                        "work_order_number": work_order_name,
                        "work_order_quantity": 0,
                        "undelivered_quantity": 0,
                        "total_quantity": 0,
                        "remaining_quantity": 0,
                    }

                # 從資料庫中查詢工單的總數量
                db_work_order_total = (
                    session.query(work_number_table)
                    .filter(work_number_table.c.name.like(f"%{work_order_number[i]}%"))
                    .order_by(desc(work_number_table.c.total))
                    .all()
                )

                # 迴圈處理查詢結果，並更新工單的總數量
                for record in db_work_order_total:
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
        json_item = jsonj_data_dict.get(order_number)
        if json_item is not None:
            data["work_order_quantity"] = json_item["QTY"]
            data["undelivered_quantity"] = json_item["UN_QTY"]
            data["remaining_quantity"] = (
                data["undelivered_quantity"] - data["total_quantity"]
            )

    # 返回處理後的工單資料
    return json.dumps(
        {
            "result": list(work_order_data.values()),
            "status": 200,
            "message": "success",
        }
    )


# TODO: add not_dispatch_work_order_data api
# @app.route("/api/get_no_dispatch_work_order_data")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
