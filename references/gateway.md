# 固定Gateway接口与可靠执行

契约原文：[接口文档快照](gateway-api-source.md)。业务场景变更不改变以下地址与语义。运行时保存所用文档hash，并核实可用的当前文档；快照不是服务永远不变的保证。

- 基址 `http://112.13.90.15:60035`；GET `/v1/models`、GET `/v1/current-model`，POST `/v1/chat/completions`。
- 批次开始/恢复/结束保存current-model原始响应。实际model、servedModelName、backend变更时暂停新派发、隔离结果；不调用返回的内部127.0.0.1 endpoint。
- `model`仅元数据，不能切换底层模型。不凭历史实测写死实际模型名。文档没有要求鉴权，不编造key或读取浏览器凭证；遇401/403暂停并解决实际鉴权需求。凭据仅环境变量取值，不进日志。
- 不存在已文档化的文件上传、批任务创建、取消、结果下载API；状态和调度本地维护。

非流式请求（字段保持现有接口）：

```json
{
  "requestId": "run-scene-version-case-turn-side-A01",
  "model": "本次current-model.model",
  "messages": [{"role":"system","content":"渲染后的完整Prompt"},{"role":"user","content":"用户原话"}],
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 1024,
  "stream": false,
  "chat_template_kwargs": {"enable_thinking": false}
}
```

请求头Content-Type=application/json，X-Request-ID与requestId一致。默认采样是可修改的离线实验参数，不代表线上生产配置。允许参数依当前Profile；chat_template_kwargs仅enable_thinking、thinking_budget。参数不支持时停下修订整批，不逐条删参数造成不可比。模板参数与传输参数分开。

## 并发、重试和恢复

1. 默认全局8个在途请求，两端、所有场景、版本和重试共享同一上限；用户可设置更低或明确更高的已知上限。一个协调器负责索引/清单写入，一个requestId同时仅一个执行者。每场景每版本先一条冒烟，成功样本复用，不重复调用。
2. 发送前原子保存请求、hash与in_flight；收到响应立即保存原JSON、HTTP状态、时间、usage、finish_reason，再标最终状态。单请求默认120秒；代理轮询不超过60秒。预算包含重试与格式修复，达到max_requests停止新派发，已在途正常收集。
3. 网络超时/429/502/503/504最多3次传输（2次重试），同一逻辑请求复用完全相同请求体和requestId，每次另记序号。遵循有界Retry-After/指数退避，超时为unknown，不保证未执行或服务端已去重。
4. 429或连续暂时错误时暂停新派发、并发减半最低1；连续32成功再逐步恢复配置上限。长退避保存next_retry_at。400/401/403立即停新派发；连续3个逻辑请求耗尽重试也停；收集在途结果，不声称取消远端。
5. 恢复核对输入/配置/模型hash，跳过已有有效输出；in_flight/unknown有限同ID重试。修改内容或参数必须新attempt/requestId，旧输出保留。不得自动切网页或模型。

## 响应与归档

读取choices[0].message.content，正常完整输出需非空文本及finish_reason=stop。HTTP成功不等于业务通过；length标truncated，tool_calls/未知结束原因待核查，不能自动执行工具。error、无choices、null或空内容保留错误，不伪造AI回答。

原JSON与请求永久留痕；每场景/版本/attempt隔离；CSV是本地转换，website_task_id=null，不伪造网站ID。按场景+测试ID+轮次(+重复/side)配对，不按完成顺序。usage缺失留空，不填0。
