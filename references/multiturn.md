# multiturn：双角色多轮评测

前置：冻结suite、persona、Prompt、业务参数、量表和请求预算。读gateway.md；用户和客服均可沿用当前Gateway，用独立system/历史；model字段不能路由另一模型。报告同模型自我模拟的相关偏差。

场景库包含case_id、来源追溯、可见起始上下文、用户角色事实、允许变化状态与停止条件。真实新证据生成新suite/persona版本，比较中途不换。发送模拟器前脱敏，客户号码等不进入角色卡。

- prefix_fork：所有版本在相同真实用户发言结束处开始；仅评分新生成客服回复。
- scenario_seed：真实触发语派生场景，真实账单缺失/历史客服与夹具矛盾时不重放旧客服；报告为派生模拟。
- fresh_start：需要明确平台开场机制，不能杜撰历史。

客服消息：system是渲染Prompt，user是用户话语，assistant是客服历史；不得传入隐藏角色事实或评分答案。
模拟用户消息：system是用户角色与私有状态，其assistant历史是用户自己的话，其user历史是客服话；不得看到客服system、版本名、评分标准、预期答案。也可使用已验证的显式speaker数组，冻结协议。

用户输出合同为`utterance:string,event:continue|hangup|silence,state_update:object`。只允许配置可变字段变更，固定事实不变；结构/事实无效最多一次修复，仍失败记simulator_error，不伪造台词或算客服失败。内部JSON/state不发给客服。无音频静默映射时，silence标能力不支持，不伪装真实音频输入。

会话间并发、同会话逐轮串行，两端/版本/重试共享global_max_inflight。请求上界估算=case×版本×repeats×max_service_turns×2，再计重试与修复预算；达到预算即停止新派发并保存状态。每侧有效响应和状态落盘后才能下一轮。

停止：用户hangup；Prompt明确的末尾结束标记；最大轮次/时长/上下文限制；有证据的无进展。承诺后须允许确认计划；达到上限标truncated，不算成功。保留原回复和结束原因，中间出现控制标记为格式异常。

恢复键包含run/scene/case/persona_hash/prompt_hash/repeat/turn/side；验证完整快照后继续，不重生成功回复。对照按case+repeat配对；不同版本用户动态台词分叉属于同场景比较，不声称逐字同输入实验。

输出逐轮CSV、原请求响应、用户状态轨迹、会话级评分与独立HTML，区分客服缺陷、模拟器偏差、基础设施错误、证据不足。单轮基线不能替代多轮基线；口头承诺/模拟预约/模拟付款不是真实业务达成。
