# 已有项目接入

本工作流自包含；不要求安装或保留其他专用Skill。若已有数据处理项目，可按以下合同接入。

| 现有产物 | 接入位置 | 复用前检查 |
|---|---|---|
| 通话CSV | inputs.calls | 实际字段、ASR结构、场景归属和时间覆盖 |
| 业务结果名单 | inputs.outcomes | 事件含义、客户关联键和来源依据 |
| 已核验身份映射 | inputs.identity_map | 数据源、场景和完整复合键、未解决项 |
| 固定单轮测试集 | inputs.testset | 两列格式、唯一ID、来源记录及hash |
| 多轮场景库 | inputs.suite及persona_path | 角色事实、可见前缀、状态合同和版本 |
| 既有分析报告 | inputs.report | 来源文件、适用场景、证据与限制 |
| 原始评测回复 | evaluation.archive | 原请求响应、实际配置、Prompt与测试集hash |
| Prompt正文 | evaluation或iteration路径 | 版本与分支、变量、输出约定及正文hash |

原文件不必搬迁。用outputs保留项目目录结构，用history索引定位产物；详见[历史复用](history-reuse.md)。原始证据缺失时记录限制，不能只凭文件名宣称同条件可比。

若复用项目自己的脚本，先验证字段、默认值、输入/输出与运行副作用；未验证的业务特定脚本不视为本工作流执行器。其他工具的升级不会自动改变本包内部规范。
