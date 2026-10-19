import os

import pymysql
import pytest


@pytest.fixture(autouse=True)
def use_test_database(monkeypatch):
    """所有测试都切到独立的测试数据库，跑之前把表清空。"""
    monkeypatch.setenv("DB_NAME", "short_link_test_db")

    # 测试库不存在就建一个，没权限就自己手动建（README 里写了）
    try:
        server_conn = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            charset="utf8mb4",
            connect_timeout=5,
        )
        with server_conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE DATABASE IF NOT EXISTS short_link_test_db
                CHARACTER SET utf8mb4
                COLLATE utf8mb4_0900_ai_ci
                """
            )
        server_conn.close()
    except pymysql.MySQLError:
        pass

    # 建表语句和 README 里的一样，复制过来的
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="short_link_test_db",
        charset="utf8mb4",
        connect_timeout=5,
        autocommit=True,
    )
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS short_links (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                code VARCHAR(16) NOT NULL,
                original_url VARCHAR(2048) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                click_count BIGINT UNSIGNED NOT NULL DEFAULT 0,
                PRIMARY KEY (id),
                UNIQUE KEY uk_short_links_code (code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        # 简单粗暴，直接把表清空，测试库本来就是干这个的
        cursor.execute("DELETE FROM short_links")
    conn.close()
