# multiturn：角色扮演与轨迹生成

前置：冻结suite、persona、Prompt、业务参数和请求预算。读gateway.md；默认assistant_direct由当前代理扮演用户，只有客服调用Gateway。只有用户明确选择external_model才使用用户模型。model字段不能路由另一模型。量表由下游analyze冻结，不是角色生成的必要输入。

场景库包含case_id、来源追溯、可见起始上下文、用户角色事实、允许变化状态与停止条件。真实新证据生成新suite/persona版本，比较中途不换。发送模拟器前脱敏，客户号码等不进入角色卡。

- prefix_fork：所有版本在相同真实用户发言结束处开始；标记新生成回复范围供下游分析。
- scenario_seed：真实触发语派生场景，真实账单缺失/历史客服与夹具矛盾时不重放旧客服；报告为派生模拟。
- fresh_start：需要明确平台开场机制，不能杜撰历史。

客服消息：system是渲染Prompt，user是用户话语，assistant是客服历史；不得传入隐藏角色事实或评分答案。
模拟用户消息：system是用户角色与私有状态，其assistant历史是用户自己的话，其user历史是客服话；不得看到客服system、版本名、评分标准、预期答案。也可使用已验证的显式speaker数组，冻结协议。

用户输出合同为`utterance:string,event:continue|hangup|silence,state_update:object`。只允许配置可变字段变更，固定事实不变；结构/事实无效最多一次修复，仍失败记simulator_error，不伪造台词或算客服失败。内部JSON/state不发给客服。无音频静默映射时，silence标能力不支持，不伪装真实音频输入。

会话间并发、同会话逐轮串行，两端/版本/重试共享global_max_inflight。请求上界估算=case×版本×repeats×max_service_turns×（assistant_direct为1，external_model为2），再计重试与修复预算；达到预算即停止新派发并保存状态。每侧有效响应和状态落盘后才能下一轮。

停止：用户hangup；Prompt明确的末尾结束标记；最大轮次/时长/上下文限制；有证据的无进展。承诺后须允许确认计划；达到上限标truncated，不算成功。保留原回复和结束原因，中间出现控制标记为格式异常。

恢复键包含run/scene/case/persona_hash/prompt_hash/repeat/turn/side；验证完整快照后继续，不重生成功回复。对照按case+repeat配对；不同版本用户动态台词分叉属于同场景比较，不声称逐字同输入实验。

输出逐轮CSV、原请求响应、用户状态轨迹、运行清单与analysis-input.json，不输出会话质量评分、版本胜负或分析HTML。交接包含真实文件路径/hash、业务夹具、角色/Prompt快照、实际模型参数、结束原因、失败数、用户模式和analysis_status=not_run。兼容已有目录，不重命名原始文件。

单独调用在原始轨迹交付后完成。组合执行 `multiturn → analyze`，由数据分析模块消费同一运行目录；只重评历史轨迹直接使用analyze，无需再次扮演或调用客服。分析输出不回写角色台词。单轮基线不能替代多轮基线；模拟行动不是真实到账。
