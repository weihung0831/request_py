import json
from datetime import datetime
import mysql.connector


# 獲取當天日期並格式化為 yyyyMMdd 格式
current_date = datetime.now().strftime("%Y%m%d")
data = []
# 打開並讀取JSON文件
with open('data/'+current_date+'data.json', 'r') as file:
    data = json.load(file)

conn = mysql.connector.connect(
        host="localhost",  # 例如 "localhost"
        user="tbi",
        password="tbi",
        database="tbi"
        )    

for index, item in enumerate(data, start=1):
    AUFNR = item['AUFNR']
    print(index)
    print(item)

    # 創建一個 cursor 對象
    cursor = conn.cursor()

    query = "SELECT * FROM work_number WHERE name LIKE %s"
    values = ("%"+AUFNR+"%",)

    # 執行查詢
    cursor.execute(query, values)

    # 獲取查詢結果
    results = cursor.fetchall()

    # 打印結果
    for row in results:
        print(row)

# 關閉 cursor 和連接
cursor.close()
conn.close()