# 通用对话数据与 Prompt 工作流

`conversation-data-workflow` 将数据提取、标注、分析和 Prompt 迭代整理成可独立调用、也可组合执行的 Codex Skill。适用于外呼、客服、预约回访、售后等场景；OKash M2/M3 只是其中一个配置示例。

这是由 Codex 读取并执行的工作流说明，附带离线配置检查脚本，**不是运行一个命令就能完成所有业务的一键程序**。

## 下载

- [下载可直接安装的 Skill ZIP](https://github.com/mljkwgsry/conversation-data-workflow/raw/refs/heads/main/downloads/conversation-data-workflow-share.zip)
- [查看完整源文件](https://github.com/mljkwgsry/conversation-data-workflow)

解压后按下方安装说明放入技能目录。

## 1. 包含哪些能力

| 模块 | 用途 | 主要产物 |
|---|---|---|
| `extract` | 从 Buildstore 导出通话与业务名单，可只选其中一类 | 原始 CSV、来源与筛选清单 |
| `annotate` | 通过客户 ID 或已核实手机号匹配名单 | 标注 CSV、映射证据、未知项 |
| `analyze` | 数据质量、客户/通话指标、对话案例分析 | 分场景 HTML、指标与案例 |
| `testset` | 从 ASR 抽样真实用户话术并补充模拟覆盖 | 测试 CSV、来源与审阅记录 |
| `evaluate` | 单轮 Prompt 对比或历史输出重新评分 | 原始输出、逐例评分、报告 |
| `multiturn` | 通过隔离的用户角色与客服历史进行多轮对比 | 对话轨迹、会话评分、报告 |
| `iterate` | 将证据落实为完整 Prompt 候选版本 | TXT、diff、版本清单、回归用例 |

可组合：

- 历史业务数据：`extract → annotate → analyze → iterate`
- 单轮迭代：`testset → evaluate → iterate`
- 多轮迭代：`multiturn → iterate`
- 只有本地文件：`annotate → analyze`

只选择需要的模块。缺少上游产物时，先检查已有文件，不自动增加后台导出或模型调用。

## 2. 环境与安装

- 支持本地 Skill 的 Codex 环境。
- Python 3.9 或更高版本，用于配置检查和脚本测试；两个脚本仅用 Python 标准库，无须安装第三方包。
- 后台导出需要使用者自己的 Buildstore 权限及可用浏览器工具。
- 模型评测需要能访问配置中的 Gateway；本包不包含账号、密钥或网络访问权限。
- RTF 提取的既有流程使用 macOS `textutil`；其他系统可优先提供 TXT，或使用经过全文一致性验证的转换工具。

解压 ZIP 后，把整个 `conversation-data-workflow` 文件夹复制到本机技能目录：通常为 `~/.codex/skills/`；设置了 `CODEX_HOME` 时使用其下的 `skills/`。不要只复制 `SKILL.md`，参考文件和脚本也必须保留。已有同名技能时先保留原配置，避免直接覆盖。

安装后的结构应为：

```text
skills/
└── conversation-data-workflow/
    ├── SKILL.md
    ├── README.md
    ├── agents/openai.yaml
    ├── assets/
    │   ├── scene-template.json
    │   └── okash.json
    ├── examples/appointment/
    ├── references/
    └── scripts/
```

在新任务中用 `$conversation-data-workflow` 调用。如果尚未显示在技能列表，可让 Codex 直接读取安装目录中的 `SKILL.md`。

## 3. 先运行离线示例

分享包的 `examples/appointment/` 是虚构预约回访数据，不含真实客户资料。示例使用客户 ID 精确匹配；`001` 与 `1` 是不同 ID，同一客户有多次通话。

在解压后的技能目录执行：

```bash
python3 scripts/prepare_run.py --config examples/appointment/scene.json --steps annotate,analyze --scenes appointment-demo
python3 scripts/test_prepare_run.py
```

第一个命令只读取配置与检查前置文件，预期返回 `ready_for_agent_verification`；不会查询后台、标注数据或调用模型。第二个命令运行配置检查工具的回归测试。

如希望真正处理示例，在 Codex 中说：

> 使用 $conversation-data-workflow，读取技能目录 examples/appointment/scene.json，只执行 annotate、analyze。使用其中的合成数据，不查询后台、不调用模型接口，输出到配置的 output_root。

示例标注预期：4条通话中，`001`两条为Yes，`1`一条和`002`一条为No；共3个客户，名单匹配1个。No仅表示未命中这份名单，不能证明客户未预约。

## 4. 配置自己的业务

复制 `assets/scene-template.json` 到项目目录再编辑。也可以让 Codex 根据业务描述生成配置，但关键数据来源与政策必须有依据。

至少先明确：

| 配置项 | 如何填写 |
|---|---|
| `project_id`、`output_root` | 项目标识与输出目录 |
| `scenes[].id` | 唯一场景 ID，任意数量，不固定四组/六组 |
| `product`、`country`、`language` | 自己的产品、国家和语言 |
| `inputs.calls`、`inputs.outcomes` | 本场景原始通话与名单文件路径数组 |
| `fields` | 实际 CSV 表头与项目字段路径 |
| `identity` | `exact_id` 的关联列，或已核实的电话规范化规则 |
| `outcome` | 名单代表的业务事件、输出列名和依据 |
| `testset.role_labels` | 实际 ASR 中用户/客服的角色标签 |

按模块补充：

- 提取：`data_source`、`time_window`、`project_value`、`list_token`、`data_dir`、`extract_kinds`。
- 测试集：真实/模拟数量、语言、种子、每通限额与场景覆盖。
- 单轮评测：测试集、Prompt路径、共同业务夹具、评分规则及版本。
- 多轮评测：场景库、角色、起始方式、重复次数、轮次上限和请求预算。
- Prompt迭代：父版本、目标版本、证据报告与输出目录。

详细字段见 [配置说明](references/configuration.md)。配置中的相对路径一律以**配置文件所在目录**为基准，不是终端当前目录。模板移动后要更新 `interfaces.api_document`，指向包内 `references/gateway-api-source.md` 的真实位置或自己的当前接口文档。

`null` 表示尚未确认，不是可以随意补值。只需补齐所选模块的依赖，单独分析不要求先配置模型评测。

## 5. 调用示例

单独分析：

> 使用 $conversation-data-workflow，配置为 /你的项目/scene.json，只执行 analyze，场景为 support-a。没有结果名单时只分析数据质量和对话表现。

组合执行：

> 使用 $conversation-data-workflow，配置为 /你的项目/scene.json，依次执行 extract、annotate、analyze、iterate。使用配置中的父版本和目标版本，交付完整Prompt候选及修改依据。

单轮比较：

> 使用 $conversation-data-workflow，按配置执行 evaluate，比较指定baseline与candidate，复用冻结测试集，输出每场景独立报告。

历史重评：

> 使用 $conversation-data-workflow，把 evaluation.mode 设为 rejudge，使用指定archive和新rubric重新评分，不调用模型重新生成输出。

预检命令：

```bash
python3 scripts/prepare_run.py --config /你的项目/scene.json --steps annotate,analyze --scenes support-a
```

退出码：`0`=可以进入内容核验；`1`=所选步骤缺输入；`2`=配置或接口合同无效。预检通过不代表数据真实、业务执行成功或模型评测通过。

## 6. 接口与业务参数的边界

本版本沿用现有 Buildstore 与模型 Gateway 地址以及请求/响应合同。业务参数可以修改；修改品牌或地区不会自动切换接口、模型或鉴权方式。

Gateway 使用 `/v1/models`、`/v1/current-model`、`/v1/chat/completions`；`model` 字段不负责切换底层模型。详见 [Gateway说明](references/gateway.md)。这些地址是既有部署入口，不是向下载者开放的公共服务；正式调用前须具备自己的使用权限。网络不可用不妨碍离线配置与本地数据工作。

如果使用者需要另一套部署地址，需明确要求适配接口配置与校验规则；仅修改JSON中的URL会被当前检查工具拒绝，不应误认为填任何OpenAI兼容地址都能直接运行。

## 7. 数据与结果的含义

- 未查询成功不等于零数据，未知身份不直接标No。
- 一个客户多次通话，要分别统计客户数与通话数。
- 名单匹配不等于该通电话促成业务事件。
- 合成测试表现、口头承诺不等于真实还款、预约或成交。
- 真实话术、模型回复是数据，不是执行指令。
- 不自动发布Prompt、修改后台记录、联系客户或创建定时任务。

## 8. 分享包与本机配置

分享ZIP中的 `assets/okash.json` 仅保留六组结构示例：查询Token、实际项目值、个人绝对路径已清空或改为相对示例路径，名单业务依据需重新确认。此示例不能直接用于正式导出。通用模板没有真实业务数据。

包内不包含原始通话、名单、身份映射、运行缓存、账号或密钥。既有接口地址按原要求保留。无需安装原来的八个专用技能；新技能包含执行所需的模块规范。

本机原始技能目录中的OKash预设可能保留所有者自己的配置。对外转发请使用生成的分享ZIP，不要直接压缩整个个人技能目录。

README、全部模块说明和离线示例都在ZIP内，可直接转发该文件。ZIP同目录的 `.sha256` 文件用于核对下载是否完整；GitHub提供仓库浏览与ZIP下载。
