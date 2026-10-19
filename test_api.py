import pytest
from fastapi.testclient import TestClient

from main import app

# 数据库隔离和清理在 conftest.py 里，这里就不重复写了

# 创建测试客户端，不自动跟随重定向
client = TestClient(app, follow_redirects=False)


def test_health_check():
    """健康检查接口应返回成功。"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_link_and_redirect():
    """创建短链接后，应能查询并重定向到原始网址。"""
    original_url = "https://example.com/article/123"

    # 创建短链接
    create_response = client.post(
        "/links",
        json={"original_url": original_url}
    )

    assert create_response.status_code == 200

    data = create_response.json()
    assert data["code"]
    assert data["original_url"] == original_url
    assert data["short_url"].endswith(f"/r/{data['code']}")

    # 访问短链接，检查重定向
    redirect_response = client.get(f"/r/{data['code']}")

    assert redirect_response.status_code == 302
    assert redirect_response.headers["location"] == original_url


def test_missing_link_returns_404():
    """不存在的短码应返回 404。"""
    response = client.get(
        "/r/definitely_missing_test_code_12345"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Short link not found"
    }


def test_create_link_rejects_invalid_url():
    """非法网址应返回 422，不应创建短链接。"""
    response = client.post(
        "/links",
        json={"original_url": "not-a-url"}
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_link_with_custom_code():
    """指定自定义短码创建短链接。"""
    response = client.post(
        "/links",
        json={
            "original_url": "https://example.com/custom",
            "custom_code": "testcode001",
        }
    )

    assert response.status_code == 200

    data = response.json()
    assert data["code"] == "testcode001"
    assert data["short_url"].endswith("/r/testcode001")


def test_duplicate_custom_code_returns_409():
    """自定义短码重复时应返回 409。"""
    client.post(
        "/links",
        json={
            "original_url": "https://example.com/first",
            "custom_code": "dupe001",
        }
    )

    response = client.post(
        "/links",
        json={
            "original_url": "https://example.com/second",
            "custom_code": "dupe001",
        }
    )

    assert response.status_code == 409


def test_invalid_custom_code_rejected():
    """太短的自定义短码应返回 422。"""
    response = client.post(
        "/links",
        json={
            "original_url": "https://example.com/x",
            "custom_code": "ab",
        }
    )

    assert response.status_code == 422


def test_get_link_info_and_click_count():
    """查询短链接信息，点击次数要准确。"""
    create_response = client.post(
        "/links",
        json={
            "original_url": "https://example.com/info",
            "custom_code": "info001",
        }
    )
    code = create_response.json()["code"]

    # 先访问一次，点击次数应该变成 1
    client.get(f"/r/{code}")

    response = client.get(f"/links/{code}")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == code
    assert data["original_url"] == "https://example.com/info"
    assert data["click_count"] == 1


def test_delete_link():
    """删除短链接后，再访问应该 404。"""
    create_response = client.post(
        "/links",
        json={
            "original_url": "https://example.com/del",
            "custom_code": "del001",
        }
    )
    code = create_response.json()["code"]

    response = client.delete(f"/links/{code}")
    assert response.status_code == 200

    # 删掉了，跳转应该查不到
    assert client.get(f"/r/{code}").status_code == 404


def test_delete_missing_link_returns_404():
    """删除不存在的短码应返回 404。"""
    response = client.delete("/links/nothing_here_404")

    assert response.status_code == 404
