"""启动脚本"""
import os

# 使用 eth1 的真实物理网关 IP
windows_ip = "10.82.120.61"
proxy_url = f"http://{windows_ip}:7897"

os.environ["HTTP_PROXY"] = proxy_url
os.environ["HTTPS_PROXY"] = proxy_url
os.environ["NO_PROXY"] = "localhost,127.0.0.1,.amap.com"
import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )