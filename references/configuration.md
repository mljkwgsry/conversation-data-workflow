# 场景配置合同

配置采用JSON；`schema_version=1`。通用模板中的null须在依赖该字段的模块运行前核实，未选择的模块不要求配置完整。`prepare_run.py`只作结构和前置项提示，不进行导出、电话查询、标注、语义判断或模型调用。

## 字段

| 配置 | 含义 |
|---|---|
| project_id / output_root | 本地项目标识与运行产物根目录 |
| interfaces.buildstore_url | 固定 https://admin.buildstore.cn/，沿用现有页面交互，不猜测后台API |
| interfaces.gateway_base_url | 固定 http://112.13.90.15:60035；改业务参数不能改变传输接口 |
| interfaces.api_document | 契约文档路径；打包快照可用，实际运行核对当前授权文档 |
| execution | 并发、超时、重试、请求预算；两侧共享global_max_inflight |
| generation | 网关允许的采样字段；模板默认实验值不是生产事实 |
| scenes[] | 任意数量场景；id唯一。每组独立配置，不默认四组或六组 |
| scene.product / language / country / timezone | 业务品牌、运行语言、国家和时间口径；仅填写有证据的值 |
| scene.data_source / time_window | 后台数据源和查询范围。明确起止时优先，滚动窗口记录实际页面口径 |
| scene.project_value / list_token / data_dir | 精确项目值、业务名单查询Token、本组数据目录；Token是筛选标识，不是鉴权凭据 |
| scene.inputs | calls、outcomes为显式路径数组；identity_map为映射文件；report、testset、suite为既有产物路径 |
| scene.fields | CSV列名、call_log中的项目字段路径、ASR字段、唯一通话/客户键、名单任务三元组、时间字段 |
| scene.identity | phone或exact_id；phone配置国家和normalize，exact_id配置两表关联列。所有键按字符串比较 |
| scene.outcome | event为业务目标事件，column为输出列名，positive/negative为标签值；membership_basis记录名单为何代表该事件及证据；未知记录单列 |
| scene.policy | 该场景业务政策与依据。无政策不自动继承催收、减免、征信或付款承诺规则 |
| scene.analysis | 业务分层维度、业务指标及证据规则；可无结果名单只分析对话质量 |
| scene.testset | real_count、synthetic_count、seed、max_per_call、role_labels、synthetic_path；角色标签依实际ASR核实 |
| scene.evaluation | mode=generate或rejudge、历史archive、baseline/candidate文件、suite_version、fixture及其来源、rubric与rubric_version |
| scene.multiturn | user_endpoint仍沿用Gateway；persona_path、start_mode、repeats、max_service_turns、timeout、end_markers |
| scene.iteration | parent_path、target_version、prompt_dir、保留的变量/输出约定。不自动选“最高版本”为父版本 |

所有path/dir、输入数组与output_root相对路径，均相对**配置文件父目录**解析；同组数据目录不会自动作为其他路径的基准。显式路径优先；用户只给目录时代理发现文件后，将实际文件列表写入有效配置，排除备份、派生输出与占位文件。不要在每一步重新glob而改变输入集。

筛选、手机号规则、政策和指标是场景参数；Buildstore页面、Gateway路由、请求字段与原有模型选择语义是接口合同。更换业务不自动更改合同。必须扩展接口时另按用户明确要求处理，不能混进场景配置。

## 电话与身份

`identity.normalize=exact`只去首尾空白，保留全部数字与前导零；可比较完全相同、已核实语义的ID或电话，不宣称跨格式匹配。`ng_e164`仅在country=NG且号码有效时允许；其他地区先配置并验证其规则/正规号码解析器，没有规则就保留未知。禁止用后几位、名字或任务ID后缀猜匹配。

`exact_id`使用`identity.call_key`和`identity.outcome_key`直接关联，不需要查后台手机号；仍须验证名单来源、场景归属、唯一性和覆盖范围。默认Buildstore名单只有任务三元组时，走subTaskInfo查询链路。

## 配置示例的地位

`scene-template.json`是待填写模板，不能直接执行正式任务。分享包的`okash.json`保留六组结构和NG规则，实际项目值、Token及名单依据需使用者填写，evaluation/iteration保留待选版本。M2减免组没有基线也可以导出；缺少基线仅阻塞该组评测/迭代。实际是否有数据每次查证，不永久跳过。

单轮样本数量、语言、名单标签和评分维度均可改。更改测试集、角色、量表或业务夹具要生成新版本，不能与旧条件混算。业务参数使用字面量模板替换，保留变量大小写，不执行模板代码。新增变量需供值方、类型及缺失行为；同一对照共同业务条件一致。

## 复制到新项目

复制scene-template.json后，先填写项目/场景身份、输入与目标事件，再填写所选模块的字段。`interfaces.api_document`原本相对技能assets目录；单独移动配置文件时，将它改为当前接口文档的绝对路径（使用者自己的接口文档位置），或同步复制文档并更新相对路径。不要直接执行含null的通用模板。

运行检查工具的退出码：0表示可进入代理的内容核验，1表示选定步骤有缺口，2表示配置/接口合同无效；三者都没有执行后台或模型请求。`ready_for_agent_verification`不是业务完成，也不保证输入文件内容合格。

## 沿用原技能目录

`layout_mode=legacy` 时，`scenes[].outputs` 保存各模块目标目录，优先于output_root：

- extract：calls_dir、outcomes_dir。
- annotate：output_dir、backup_dir、audit_dir、write_mode（默认copy；原地更新须符合本次授权）。
- analyze：report_dir、evidence_dir。
- testset：output_dir、existing_suite_policy。
- evaluate / multiturn：run_dir、report_dir。
- iterate：prompt_dir、record_dir；未选定Prompt分支时不能自行落入其他分支。

`history.catalog_path` 是已有产物目录；archive_pointer是ZIP清单入口。每个文件记录原路径及hash。运行前检查原件存在且hash未变，变化时重建本次快照，不能把旧索引当永久真相。后续新增文件在用户指定场景目录内重新发现，核验完整项目值后才更新输入列表。

候选版本、目标版本等未选定值不因历史接续而自动填成最新版。使用者可在本地预设中连接历史数据、身份映射、固定测试集与历史分析报告；公开模板不含这些真实路径，零记录占位应单独登记。另项目文件即使位于同一组目录，也仅进入历史候选，不自动继承名单。历史索引仅留本地，不加入公开分享包。
