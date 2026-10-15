# 产物、组合与恢复

建议运行目录：`output_root/project_id/run_id/scene_id/step/`。run_id使用时间戳加随机后缀避免碰撞。原始导出归场景data_dir；运行目录存引用/hash及派生结果。

每模块manifest字段：schema_version、run_id、scene_id、step、status、started_at、finished_at、effective_config_hash、inputs[{path,sha256,role,coverage}]、outputs[{path,sha256,role}]、counts、limitations、next_actions。网络模块另记接口文档hash、请求/响应索引、model快照、参数hash、预算消耗与重试。日期有timezone；未知时保留原字符串和unknown，不猜转换。

状态：complete=该模块合同全部验证；partial=有可用产物但缺失影响结论；blocked=必要输入/配置不可得；failed=执行错误；not_run=未执行。零记录可以complete且counts=0，有查询证明；“没查到”且查询失败是failed。

每步输入优先级：本轮上游已验证产物 → 用户明确既有产物 → 同场景经hash验证的归档。上游partial时仅允许不依赖缺失数据的分析部分继续，并传播限制；不得把草稿unknown自动转成No。读取外部旧产物需补manifest/来源审计，不强迫重跑。

单独步骤只验证自己的依赖。例如analyze没有标签可输出对话质量；iterate用现成报告无须extract；evaluate.mode=rejudge无须网络。工具的计划只是初检，代理仍需验证真实表头、hash和场景语义。

恢复前核对输入/配置/版本/模型快照；同条件才复用成功输出，变化则新run/attempt。不可覆盖旧原始响应或跨attempt悄悄拼接。选择的最终attempt写清楚，错误、unknown、截断保留计数。

报告HTML对ASR/模型文本转义，不把原始客户文本当HTML执行。公开交付仅脱敏摘要；本地敏感映射与可分享的技能包隔离。密钥由命名环境变量读取，配置和日志不写密钥值。
