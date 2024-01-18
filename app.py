import json
import os

from dotenv import load_dotenv
from flask import Flask, render_template
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker


# load json data
with open("./data/20240115data.json", "r") as f:
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


@app.route("/api/get_work_order_data")
def get_work_order_data():
    work_order_number = [data["AUFNR"] for data in jsonj_data]
    work_order_quantity = [data["QTY"] for data in jsonj_data]
    undelivered_quantity = [data["UN_QTY"] for data in jsonj_data]

    return json.dumps(
        {
            "result": {
                "work_order_number": work_order_number,
                "work_order_quantity": work_order_quantity,
                "undelivered_quantity": undelivered_quantity,
            },
            "status": 200,
            "message": "success",
        },
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
