# OpenAIBot

将 OpenAI 的能力包装成各类机器人


# 安装

```
git clone https://github.com/pfchai/OpenAIBot.git

cd OpenAIBot

# 进入虚拟环境


pip install -r requirements.txt
```


# 启动服务

```
# 配置

cp .env.example .env

# 补充相关配置信息
vi .env

# 设置 GPT-3 模型
export GPT_ENGINE='text-davinci-003'

# 启动服务
flask run

# 指定端口，外网可用
flask run --host 0.0.0.0 --port 8000
```
