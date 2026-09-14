# LoggerBot 模型接入复用确认 · 2026-09-06

用户要求参考已有 LoggerBot 方法，优先确认是否能够掌握和复用。本次仅只读检查 LoggerBot 代码与必要配置，并执行一个不含研究资料的最小连接测试；未修改该项目、反代服务、共享登录文件、模型选择或其他任务。

## 已确认的方法

- LoggerBot 项目位于同级 `alphabot`；`README.md`、`agents/logger/config.py` 与 `agents/logger/llm/codex_cli.py` 一致说明默认走 Codex 兼容反代的 Responses 接口，模型为 `gpt-5.6-sol`。
- 现有配置使用 `CODEX_PROXY_BASE_URL`、`CODEX_PROXY_API_KEY`、`CODEX_PROXY_MODEL`；本机地址为 `http://127.0.0.1:10531/v1`，对应端口已监听。鉴权配置存在；本记录不包含其值。
- LoggerBot 完整工作流使用可恢复的 `codex exec --json` 会话，严格输出 Schema、会话与阶段检查点，并把任务完成验证与模型自述分开。
- LoggerBot 维护本机反代及其共享登录状态。研究雷达应使用既有服务，不另启一个竞争刷新登录令牌的进程，也不读写其登录文件。

## 最小实测

向已确认的本机 `/v1/responses` 发送一次微型请求：只要求输出布尔字段 `ok`，设置 `store:false`，无工具、无研究语料、无飞书数据。

请求采用 `text.format.type=json_schema`、`strict:true` 与 `additionalProperties:false`。返回：

```json
{"http_status":200,"response_status":"completed","model":"gpt-5.6-sol","structured_ok":true,"error_present":false}
```

这证明现有模型链路可以提供雷达所需的严格结构化输出；不等于完整八月证据包已经生成成功，也不等于全部月报、重试恢复和自动发布通过验收。

## 后续实施边界

1. 在研究雷达本机入口显式读取该配置来源的模型字段，映射到既定 `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` 接口；不载入或转发 LoggerBot 的飞书及个人 OAuth 字段，不把密钥复制进雷达仓库。
2. 保留雷达自己的确定性统计、证据 ID、版本截止和数字校验；不照搬 LoggerBot 的访谈提取或飞书个人授权逻辑。
3. 模型调用、证据包 hash、输出校验及失败原因独立记录。先完成八月真实生成与审校，再扩展到全部月份。
4. 如实际长任务需要 LoggerBot 的可恢复 Codex 会话能力，再引入对应执行适配器；不把单次 HTTP 成功说成已经复刻了完整会话式工作流。

官方结构化输出接口核对：[Responses 创建接口](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)。实际兼容性以上述本机测试为依据，不将第三方反代行为说成 OpenAI 官方保证。
