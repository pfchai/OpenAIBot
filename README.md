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

cp config.yaml.example config.yaml

# 补充相关配置信息
vi config.yaml

# 启动服务
flask run

# 指定端口，外网可用
flask run --host 0.0.0.0 --port 8000
```


# ToDos

 - [x] 基于 GPT3 对话机器人
 - [ ] 基于 ChatGPT 对话机器人
 - [x] 支持飞书机器人
 - [x] 支持企业微信机器人
 - [x] 服务支持配置多个机器人
