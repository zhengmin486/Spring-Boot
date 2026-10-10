# Short Link System

一个基于 Python、FastAPI 和 MySQL 的短链接服务，用于练习后端接口开发、数据库持久化和自动化测试。

## 一、项目功能

- 创建短链接：输入原始网址，生成短码并返回短链接。
- 短链接跳转：访问短链接后，查询原始网址并执行 HTTP 302 重定向。
- 数据持久化：使用 MySQL 保存短码、原始网址、创建时间和访问次数。
- 参数校验：使用 FastAPI 和 Pydantic 校验请求数据。
- 异常处理：短码不存在时返回 HTTP 404，非法网址返回 HTTP 422。
- 访问统计：每次成功访问短链接后，更新对应记录的访问次数。
- 自动化测试：使用 pytest 和 FastAPI TestClient 验证主要业务功能。

## 二、技术栈

| 技术 | 用途 |
| --- | --- |
| Python 3.13 | 主要开发语言 |
| FastAPI | Web API 框架 |
| Uvicorn | 本地运行 Web 服务 |
| MySQL 8 | 关系型数据库 |
| PyMySQL | Python MySQL 驱动 |
| python-dotenv | 读取本地环境配置 |
| pytest | 自动化测试 |
| HTTPX | HTTP 测试依赖 |

## 三、项目结构

```text
short-link-system/
├── main.py          # API 接口与业务逻辑
├── test_api.py      # API 自动化测试
├── test_db.py       # 数据库连接测试
├── .env             # 本地数据库配置，不提交到 Git
├── .gitignore       # Git 忽略规则
├── README.md        # 项目说明
└── .venv/           # Python 虚拟环境，不提交到 Git
```

## 四、运行环境

- Windows
- Python 3.13
- MySQL 8.0
- PowerShell

## 五、数据库配置

### 1. 创建数据库

在 MySQL 命令行中执行：

```sql
CREATE DATABASE IF NOT EXISTS short_link_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;
```

### 2. 创建数据表

```sql
USE short_link_db;

CREATE TABLE IF NOT EXISTS short_links (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(16) NOT NULL,
    original_url VARCHAR(2048) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    click_count BIGINT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_short_links_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3. 配置环境变量

在项目根目录创建本地 `.env` 文件：

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=short_link_app
DB_PASSWORD=替换为你自己的数据库密码
DB_NAME=short_link_db
```

请使用本地实际的数据库账号和密码，不要将真实密码提交到 GitHub。

项目应用账号至少需要对 `short_link_db` 具有 SELECT、INSERT 和 UPDATE 权限。

## 六、安装与启动

### 1. 创建虚拟环境

在项目根目录执行：

```powershell
python -m venv .venv
```

### 2. 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install fastapi "uvicorn[standard]" PyMySQL python-dotenv pytest httpx
```

### 3. 检查数据库连接

确保 MySQL 服务器已经启动，然后执行：

```powershell
.\.venv\Scripts\python.exe test_db.py
```

连接成功时，会输出数据库名称和 MySQL 版本。

### 4. 启动 API 服务

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

启动后访问：

- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

## 七、接口说明

### 1. 创建短链接

- 方法：POST
- 路径：`/links`

请求示例：

```json
{
  "original_url": "https://example.com/article/123"
}
```

成功时返回短码、短链接、原始网址和数据库记录 ID。

### 2. 访问短链接

- 方法：GET
- 路径：`/r/{code}`

系统根据短码查询原始网址，并返回 HTTP 302 重定向。

如果短码不存在，返回 HTTP 404。

### 3. 健康检查

- 方法：GET
- 路径：`/health`

正常情况下返回：

```json
{
  "status": "ok"
}
```

## 八、运行自动化测试

确保 MySQL 已启动，并且项目根目录下的 `.env` 配置正确。

执行：

```powershell
.\.venv\Scripts\python.exe -m pytest -v test_api.py
```

目前已验证的测试场景：

- 健康检查接口。
- 创建短链接与重定向。
- 不存在的短码返回 HTTP 404。
- 非法网址返回 HTTP 422。

测试会通过数据库创建短链接记录，因此多次运行可能产生额外的测试数据。

## 九、当前项目范围

当前版本主要用于学习和演示，已实现短链接创建、数据库持久化、重定向、访问次数更新和基础自动化测试。

后续可以逐步完善：

- 测试数据隔离与清理。
- 更完善的异常处理和日志。
- Redis 缓存及缓存失效策略。
- 数据库查询性能分析。
- 自动化测试与持续集成。

当前版本尚未实现 Redis 缓存和生产环境部署，不应将这些内容描述为已经完成的功能。