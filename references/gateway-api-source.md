**AI 模型调用接口文档**  
**6. LLM OpenAI 兼容接口**  
**6.1 查询模型**  
GET /v1/models  
   
返回 OpenAI 风格模型列表。  
GET /v1/current-model  
   
返回当前 Gateway 实际加载的单个模型：  
{  
   "status": "ok",  
   "model": "qwen35-9b",  
   "servedModelName": "/opt/models/Qwen3.5-9B",  
   "backend": "vllm",  
   "endpoint": "http://127.0.0.1:9040/v1/chat/completions"  
 }  
   
**6.2 对话生成**  
POST /v1/chat/completions  
   
非流式请求：  
{  
   "requestId": "llm-20260918-0001",  
   "model": "qwen35-9b",  
   "messages": [  
     {"role": "system", "content": "You are a concise assistant."},  
     {"role": "user", "content": "Hello"}  
   ],  
   "temperature": 0.7,  
   "top_p": 0.9,  
   "max_tokens": 1024,  
   "stream": false,  
   "chat_template_kwargs": {  
     "enable_thinking": false  
   }  
 }  
   
关键字段：  
| | | | |  
|-|-|-|-|  
| **字段** | **类型** | **必填** | **说明** |   
| requestId | string | 否 | 幂等请求标识；缺省时自动生成 |   
| model | string | 否 | 兼容字段；单模型 Gateway 不使用它路由 |   
| messages | array | 是 | 至少一条消息 |   
| messages[].role | string | 是 | system、user、assistant、tool 或 developer |   
| messages[].content | JSON | 是 | 不能为 null，通常为字符串 |   
| stream | boolean | 否 | 默认 false |   
| temperature | number | 否 | 采样温度 |   
| top_p | number | 否 | 核采样参数 |   
| top_k | integer | 否 | Top-K 参数 |   
| max_tokens | integer | 否 | 最大输出 Token，不能超过模型 Profile 限制 |   
| response_format | object | 否 | OpenAI 兼容响应格式 |   
| tools | array | 否 | OpenAI 兼容工具定义 |   
| tool_choice | JSON | 否 | 工具选择策略 |   
| priority | integer | 否 | vLLM 请求优先级 |   
| chat_template_kwargs | object | 否 | 仅允许 enable_thinking、thinking_budget |   
   
参数白名单由模型 Profile 决定。未允许字段返回 400 unsupported_parameter。Gateway 未收到 chat_template_kwargs 时默认关闭思考：  
{"enable_thinking": false}  
   
请求中的 model 只作为兼容元数据和响应模型名；实际发送给 vLLM 的模型由 Gateway 配置决定。使用 /v1/current-model 查询实际模型。  
非流式成功响应：  
{  
   "choices": [  
     {  
       "index": 0,  
       "message": {  
        "role": "assistant",  
         "content": "Hello!"  
       },  
       "finish_reason": "stop"  
     }  
   ],  
   "model": "qwen35-9b",  
   "object": "chat.completion",  
   "usage": {  
     "prompt_tokens": 20,  
     "completion_tokens": 4,  
     "total_tokens": 24  
   }  
 }  
   
调用示例：  
curl -sS http://127.0.0.1:9050/v1/chat/completions \  
   -H 'Content-Type: application/json' \  
   -H 'X-Request-ID: llm-demo-1' \  
   -d '{  
     "messages": [{"role": "user", "content": "Hello"}],  
     "max_tokens": 128,  
     "stream": false  
   }'  
   
**6.3 流式响应**  
设置 "stream": true。响应 Content-Type 为 text/event-stream，内容透传 vLLM OpenAI SSE 数据块，并以 data: [DONE] 结束。调用方必须按 SSE 事件解析，不能把每次 TCP 读取视为完整 JSON。  
curl -N http://127.0.0.1:9050/v1/chat/completions \  
   -H 'Content-Type: application/json' \  
   -d '{  
     "messages": [{"role": "user", "content": "Hello"}],  
     "max_tokens": 128,  
     "stream": true  
   }'  
   
