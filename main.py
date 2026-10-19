import os
import secrets

import pymysql
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, HttpUrl

# 加载项目根目录下的 .env 配置
load_dotenv()

app = FastAPI(
    title="Short Link System",
    version="0.3.0",
)

# 随机短码最多重试几次，撞码概率很低，5次还不行就放弃
MAX_RETRY = 5

# 拼接短链接用的固定前缀，不信任客户端的 Host 头
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def get_db_connection():
    """创建 MySQL 数据库连接。

    这段和 test_db.py 里差不多，是复制过来的，暂时没封装成公共模块。
    每次请求都新建连接，并发高了肯定扛不住，先凑合用。
    """
    required_keys = [
        "DB_HOST",
        "DB_PORT",
        "DB_USER",
        "DB_PASSWORD",
        "DB_NAME",
    ]

    missing_keys = [
        key for key in required_keys
        if not os.getenv(key)
    ]

    if missing_keys:
        raise RuntimeError(
            f"缺少数据库配置：{', '.join(missing_keys)}"
        )

    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
        connect_timeout=5,
        autocommit=True,
    )


class LinkCreate(BaseModel):
    original_url: HttpUrl
    # 自定义短码，4-16位字母、数字、- 或 _，不填就随机生成
    custom_code: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z0-9_-]{4,16}$",
    )


@app.get("/")
def read_root():
    return {"message": "Short Link System is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/links")
def create_link(payload: LinkCreate):
    """创建短链接，并保存到 MySQL。"""
    original_url = str(payload.original_url)
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            # 用户自己指定了短码，直接用，撞了返回 409
            if payload.custom_code:
                try:
                    cursor.execute(
                        """
                        INSERT INTO short_links (code, original_url)
                        VALUES (%s, %s)
                        """,
                        (payload.custom_code, original_url),
                    )
                except pymysql.err.IntegrityError as error:
                    # 1062 表示短码已存在
                    if error.args and error.args[0] == 1062:
                        raise HTTPException(
                            status_code=409,
                            detail="自定义短码已存在",
                        )
                    raise

                code = payload.custom_code
                link_id = cursor.lastrowid
            else:
                # 随机生成短码，撞了重新生成，最多试 MAX_RETRY 次
                for i in range(MAX_RETRY):
                    code = secrets.token_urlsafe(5)

                    try:
                        cursor.execute(
                            """
                            INSERT INTO short_links (code, original_url)
                            VALUES (%s, %s)
                            """,
                            (code, original_url),
                        )
                        link_id = cursor.lastrowid
                        break

                    except pymysql.err.IntegrityError as error:
                        # 1062 表示短码重复，重新生成再试
                        if error.args and error.args[0] == 1062:
                            continue
                        raise
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="生成短码失败，请重试",
                    )

            print(f"[debug] 新短码: {code}")  # 调试用的，忘了删

    finally:
        connection.close()

    return {
        "id": link_id,
        "code": code,
        "short_url": f"{BASE_URL}/r/{code}",
        "original_url": original_url,
    }


@app.get("/r/{code}")
def redirect_to_original(code: str):
    """从 MySQL 查询原始网址，并执行重定向。"""
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT original_url
                FROM short_links
                WHERE code = %s
                """,
                (code,),
            )

            row = cursor.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Short link not found",
                )

            original_url = row[0]

            # 原子增加访问次数
            cursor.execute(
                """
                UPDATE short_links
                SET click_count = click_count + 1
                WHERE code = %s
                """,
                (code,),
            )

    finally:
        connection.close()

    return RedirectResponse(
        url=original_url,
        status_code=302,
    )


@app.get("/links/{code}")
def get_link_info(code: str):
    """查询短码对应的原始网址和访问次数。"""
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT code, original_url, created_at, click_count
                FROM short_links
                WHERE code = %s
                """,
                (code,),
            )

            row = cursor.fetchone()

    finally:
        connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="短码不存在")

    return {
        "code": row[0],
        "original_url": row[1],
        "created_at": row[2],
        "click_count": row[3],
    }


@app.delete("/links/{code}")
def delete_link(code: str):
    """删除短链接，删掉之后就不能再跳转了。"""
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM short_links
                WHERE code = %s
                """,
                (code,),
            )

            deleted_rows = cursor.rowcount

    finally:
        connection.close()

    if deleted_rows == 0:
        raise HTTPException(status_code=404, detail="短码不存在")

    return {"message": f"短码 {code} 已删除"}
