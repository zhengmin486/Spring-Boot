from fastapi.testclient import TestClient

from main import app


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
        json={"original_url": original_url},
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
        json={"original_url": "not-a-url"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()