import requests
import pandas as pd
import json
import base64
from datetime import datetime


# 獲取當天日期並格式化為 yyyyMMdd 格式
current_date = datetime.now().strftime("%Y%m%d")

# 要轉換的字符串
string_to_encode = "TBISCM@" + current_date

# 將字符串轉換為 Base64
encoded_string = base64.b64encode(string_to_encode.encode()).decode()
# print(encoded_string)

# API URL
url = "https://scm.tbimotion.com.tw/api/PO/Get"

# Headers
headers = {
    'apitoken': encoded_string
}

# 發送GET請求
response = requests.get(url, headers=headers)

# 確保響應狀態碼為200，表示成功獲得響應
if response.status_code == 200:
    # 使用response.json()直接獲取JSON格式的數據
    data = response.json()

    # 將字典轉換為pandas DataFrame
    df = pd.DataFrame(data["result"])
    
    # 將DataFrame保存到JSON文件
    df.to_json('./data/'+current_date+'data.json', orient='records')
else:
    print("Failed to get data. Status code:", response.status_code)