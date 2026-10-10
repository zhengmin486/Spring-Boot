import os
import secrets

import pymysql
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

# 加载项目根目录下的 .env 配置
load_dotenv()

app = FastAPI(
    title="Short Link System",
    version="0.2.0",
)


def get_db_connection():
    """创建 MySQL 数据库连接。"""
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


@app.get("/")
def read_root():
    return {"message": "Short Link System is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/links")
def create_link(payload: LinkCreate, request: Request):
    """创建短链接，并保存到 MySQL。"""
    original_url = str(payload.original_url)
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            while True:
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
                    # 1062 表示重复键，重新生成短码再试
                    if error.args and error.args[0] == 1062:
                        continue
                    raise

    finally:
        connection.close()

    return {
        "id": link_id,
        "code": code,
        "short_url": f"{request.base_url}r/{code}",
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