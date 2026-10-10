import os

import pymysql
from dotenv import load_dotenv

# 加载项目根目录下的 .env 配置
load_dotenv()

required_keys = [
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
]

missing_keys = [key for key in required_keys if not os.getenv(key)]

if missing_keys:
    raise SystemExit(
        f"缺少环境配置：{', '.join(missing_keys)}，请检查 .env 文件。"
    )

connection = None

try:
    connection = pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        connect_timeout=5,
    )

    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE(), VERSION()")
        database_name, mysql_version = cursor.fetchone()

    print("数据库连接成功！")
    print(f"当前数据库：{database_name}")
    print(f"MySQL 版本：{mysql_version}")

except (pymysql.MySQLError, ValueError) as error:
    print(f"数据库连接失败：{error}")

finally:
    if connection is not None:
        connection.close()