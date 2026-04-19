"""启动脚本"""
import os

# 1. 设置你的梯子代理地址（请把 7890 换成你实际代理软件的端口）
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

# 2. ✨ 核心魔法：代理白名单！告诉 Python 遇到这些地址绝对不要走梯子
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