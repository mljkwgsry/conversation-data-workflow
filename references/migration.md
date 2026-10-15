# 原技能迁移对照

| 原独立技能 | 通用模块 | 参数迁移 |
|---|---|---|
| okash-call-export | extract(calls) | 项目、数据源、范围、目录 |
| okash-repayment-export | extract(outcomes) | Token、事件含义、时间、目录 |
| okash-repayment-mark | annotate | 身份键/电话规则、名单含义、标注列 |
| opay-collection-analysis | analyze | 字段、指标、维度、场景案例 |
| call-asr-testset | testset | ASR结构、角色、数量、语言、模拟库 |
| opay-prompt-evaluation | evaluate | 场景数、版本、夹具、评分、固定集 |
| opay-multiturn-evaluation | multiturn | 角色、起始方式、轮次、重复、预算 |
| opay-prompt-iteration | iterate | 父版本、目标版本、业务规则、证据 |

旧技能未删除或改写，保留旧调用兼容。新入口内模块可单独选择；这些模块是统一skill的步骤，不是另外七个需要安装的skill。旧技能的四组/六组、品牌、日期、确认记录不覆盖新配置。

独立脚本analyze.py含业务特定规则，不直接作为通用分析执行器；旧测试集脚本也需确认解析格式和数量参数才复用。本包是代理执行的完整工作流+离线配置规划器，不宣称已有一键联网执行引擎。

通用接口来源：本地AI模型调用接口文档快照gateway-api-source.md；操作依据为八个原技能。新增业务只需配置场景与证据规则；后台表结构或网关协议变化需要单独适配并验证。
