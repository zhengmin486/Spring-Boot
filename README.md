# 短链接系统（Short Link System）

一个练手用的后端小项目，用 FastAPI + MySQL 实现短链接的生成、跳转和点击统计。
是我学 Web 开发时的课程作业，功能不复杂，能跑就行。

## 一、功能

- 输入长网址生成短链接，也可以自己指定短码（4-16 位字母数字）
- 访问短链接 302 跳转到原网址
- 记录每个短链接的点击次数
- 查询、删除短链接
- 参数校验：网址不合法返回 422，短码不存在返回 404
- 自动化测试：pytest，一共 10 个用例

## 二、技术栈

| 技术 | 说明 |
| --- | --- |
| Python 3.13 | 主力语言 |
| FastAPI | Web 框架 |
| MySQL 8 | 数据库 |
| PyMySQL | 数据库驱动，没上 ORM |
| pytest | 测试 |

## 三、项目结构

```text
short-link-system/
├── main.py          # API 接口和业务逻辑，全在这一个文件里
├── test_api.py      # 接口测试
├── test_db.py       # 数据库连通性检查
├── conftest.py      # 测试 fixture，负责隔离测试库
├── .env.example     # 配置模板，复制成 .env 用
├── .env             # 本地配置，不上传 Git
├── requirements.txt # 依赖清单
└── README.md
```

## 四、使用说明

### 1. 环境要求

- Windows（在 Win11 上写的，别的系统没试过）
- Python 3.13
- MySQL 8.0

### 2. 建库建表

MySQL 命令行里执行：

```sql
CREATE DATABASE IF NOT EXISTS short_link_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;
```

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

### 3. 配置 .env

复制 `.env.example` 为 `.env`，填上自己的数据库账号密码：

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=short_link_app
DB_PASSWORD=你的密码
DB_NAME=short_link_db
BASE_URL=http://127.0.0.1:8000
```

`BASE_URL` 是拼短链接用的前缀，本地开发用默认值就行，别乱填到公网地址上去。

### 4. 安装依赖并启动

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe test_db.py
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

启动之后：

- 接口文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

## 五、接口说明

### 1. 创建短链接 `POST /links`

```json
{
  "original_url": "https://example.com/article/123",
  "custom_code": "mylink01"
}
```

`custom_code` 可以不填，不填就随机生成。填了但已被占用返回 409，格式不对返回 422。

### 2. 跳转 `GET /r/{code}`

302 跳转到原网址，同时点击次数 +1。短码不存在返回 404。

### 3. 查询短链接 `GET /links/{code}`

返回原网址、创建时间和点击次数。

### 4. 删除短链接 `DELETE /links/{code}`

删除成功返回 200，删不存在的返回 404。

### 5. 健康检查 `GET /health`

返回 `{"status": "ok"}`。

## 六、测试

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

测试会自动切到 `short_link_test_db`，跑之前自动建库、建表、清数据，不会污染正式库。
一共 10 个用例，覆盖上面所有接口。

## 七、更新记录

- **v0.3.0**（2026-10-17）：新增自定义短码、查询、删除接口；短链接前缀改用固定的 `BASE_URL`，不再依赖请求头里的 Host；测试改成自动清理数据
- **v0.2.0**（2026-10-10）：补充健康检查和参数校验
- **v0.1.0**：最开始的版本，只有创建和跳转

## 八、已知问题（诚实清单）

写是能跑，但坑不少，先记在这儿：

- 每个请求都新建一条数据库连接，没有连接池，并发一高肯定扛不住
- 随机短码撞了最多重试 5 次，再撞就返回 500（概率实在太低，懒得管）
- 网址超过 2048 字符会直接报 500，没做长度校验
- 没有限流，接口可以随便刷
- 没有做过期时间，建出来的链接永久有效
- 没有部署过，只在本地跑过，生产环境什么样不知道
- README 是最后赶着写的，个别地方可能和代码对不上，以代码为准

## 九、下一步

按优先级排的话：

1. 上数据库连接池（现在这个是最急的）
2. 加短链接过期时间
3. 点击统计按天拆分，看看访问趋势
