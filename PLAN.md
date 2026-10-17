# gdsfactory MCP 第一版开发计划

本计划记录与用户确认的范围，是后续开发、教学和验收的依据。
第一版原定的 25 种器件已经完成；随后增加 2 种通用热调结构和 1 种论文 Demo 微环链，当前共 28 种。

## 目标与边界

通过自然语言调用 MCP，创建、查询、摆放、连接、修改光子版图，保存和恢复不同方案，
预览、检查并导出 GDS。当前支持下列 9 类、共 28 种结构。

第一版不包含 Lumerical 等仿真、自动优化、独立网站或图形操作界面，以及未列出的器件扩展。
几何生成成功不代表光学性能已验证，也不代表满足某个工艺的流片规则。
工艺相关限制以明确选择并配置的工艺设计套件为依据。

## 已完成的基础

- [x] 配置 Python、Git、uv、项目虚拟环境和 gdsfactory。
- [x] 建立参数模型、设计操作、几何生成、MCP 入口和测试的分层结构。
- [x] 创建 `straight` 和 `taper`，连接端口，导出 JSON、GDS、PNG。
- [x] 提供 `update_component`，非法修改保留原设计。
- [x] 提供 `get_design`，只读查询当前设计。
- [x] 提供 `load_design`，从本项目 JSON 恢复设计，加载失败保留原设计。
- [x] 验证跨程序保存、恢复、修改和导出流程。

阶段一结束时共有十四个 MCP 工具：`get_design`、`list_component_types`、`get_component_schema`、`create_component`、`get_component_ports`、`new_design`、`save_design`、
`list_designs`、`load_design`、`create_straight`、`create_taper`、
`update_component`、`connect_components`、`export_gds`。
多方案管理已经完成；现有器件功能后续仍需适配通用器件模型和多端口。

## 第一版器件清单

筛选依据为通用光子版图的代表性和使用便利性，不是官方使用频率排名。
参考目录：https://gdsfactory.github.io/gdsfactory/components/#components
具体参数和可用性以项目安装的 gdsfactory 版本为准；不兼容项需说明原因并讨论替代，
不得静默替换名单。原定 25 种器件、2 种热调器件及论文 Demo 微环链已全部接入。

| 类别、中英文与常用叫法 | 数量 | 纳入结构 | 用途 |
| --- | --- | --- | --- |
| 波导、弯曲与交叉（waveguide / bend / crossing）；常说“波导”“bend”“交叉” | 4 | `straight`、`bend_euler`、`bend_s`、`crossing` | 直线、转弯、横向偏移、交叉 |
| 渐变波导（taper）；通常说“taper” | 2 | `taper`、`taper_adiabatic` | 线性和绝热渐变 |
| 耦合器（coupler）；常说“耦合器” | 3 | `coupler`、`coupler_straight`、`coupler_ring` | 完整定向耦合器、直耦合区、微环耦合结构 |
| 多模干涉器（multimode interferometer）；通常说“MMI” | 2 | `mmi1x2`、`mmi2x2` | 一分二、二进二出 |
| 环形与微盘谐振器（ring / disk resonator）；常说“微环”“微盘” | 4 | `ring_single`、`ring_double`、`coupled_ring_chain`、`disk` | 单总线微环、双总线微环、四级耦合微环链、微盘 |
| 光栅耦合器（grating coupler）；常说“光栅耦合器”或“GC” | 2 | `grating_coupler_elliptical`、`grating_coupler_rectangular` | 椭圆聚焦型、矩形光栅型 |
| 端面耦合器（edge coupler）；通常说“端面耦合器” | 2 | `edge_coupler_silicon`、`edge_coupler_array` | 单个器件、阵列 |
| 螺旋与延迟线（spiral / delay line）；常说“螺旋波导”“延迟线” | 3 | `spiral`、`spiral_racetrack_fixed_length`、`delay_snake_sbend` | 普通螺旋、指定长度跑道形螺旋、蛇形延迟线 |
| 组合光路（photonic circuit）；通常说“光路” | 6 | `mzi`、`mzi2x2_2x2_phase_shifter`、`straight_heater_metal`、`splitter_tree`、`dbr`、`loop_mirror` | 干涉仪、热调移相器、分光树、布拉格反射器、环路反射镜 |
| 合计 | 27 | | |

`mzi` 指马赫–曾德尔干涉仪（Mach–Zehnder interferometer），通常说“MZI”；
`dbr` 指分布式布拉格反射器（distributed Bragg reflector），通常说“DBR”。

## 开发阶段和完成标准

### 阶段一：设计文件与多方案管理（已完成）

- [x] `save_design`：以指定名称或项目内路径保存 JSON，不必先导出几何；默认不覆盖。
- [x] `new_design`：创建有名称的空白设计；未保存修改默认阻止替换，可明确丢弃。
- [x] `list_designs`：递归列出项目 `designs/` 目录中的方案，并报告损坏文件。
- [x] 改进 `load_design`：支持方案名和项目内路径，未保存修改默认阻止替换。
- [x] 改进 `export_gds`：支持输出名称和项目内目录，整组文件默认不覆盖。
- [x] 明确保存、覆盖、项目内文件路径及结构化错误提示规则。

完成标准：方案 A、B 可分别保存和恢复；恢复后可继续编辑；导出文件能明确对应方案。
已通过端到端测试验证方案 A、B 的独立保存、恢复、修改和导出。

### 阶段二：通用器件机制

- [x] 建立明确允许的 28 种器件注册表和 9 个分类，不开放任意 Python 执行。
- [x] `list_component_types`：列出并按类别或接入状态查询登记器件。
- [x] `get_component_schema`：查询真实参数、默认值、单位、已知限制和安全开放状态。
- [x] `create_component`：通过器件类型和已开放参数创建；先支持 `straight`、`taper`，后续按批扩展。
- [x] `get_component_ports`：查询实际端口名、全局位置、方向、宽度、图层、端口类型和连接状态。
- [x] 将当前仅支持 `o1`、`o2` 的模型适配为真实多端口模型；动态校验端口存在性和重复连接。
- [x] 改进 `update_component`：根据器件类型使用安全参数模型，一次原子修改多个参数。
- [x] 保存、加载和导出适配 `type_name + parameters` 通用器件结构；现有 straight/taper JSON 无需迁移，可继续加载、修改和导出。
- [x] 明确复杂参数的 JSON 安全规则；第一版开放已验证标量和已登记引用，首批截面为 `strip`、`rib`、`slot`。
- [x] 保留现有直波导和 taper 工具，作为旧 JSON 格式的兼容入口。

完成标准：AI 能先查询器件及参数，再创建、检查端口和修改；错误输入给出可操作的原因。

### 阶段三：分批接入全部器件

- [x] 第一批：波导、bend、crossing、taper、MMI，共 8 种。
  - [x] 已接入：`straight`、`bend_euler`、`bend_s`、`crossing`、`taper`、`taper_adiabatic`。
  - [x] `mmi1x2`、`mmi2x2` 已接入，本批全部完成。
- [x] 第二批：耦合器、微环和微盘，共 6 种。
  - [x] 已接入：`coupler`、`coupler_straight`、`coupler_ring`。
  - [x] `ring_single`、`ring_double`、`disk` 已接入，本批全部完成；后续为论文 Demo 增加 `coupled_ring_chain`。
- [x] 第三批：光栅与端面耦合器，共 4 种。
  - [x] 已接入：`grating_coupler_elliptical`、`grating_coupler_rectangular`。
  - [x] 已接入：`edge_coupler_silicon`、`edge_coupler_array`；阵列端口数由 `n` 动态决定。
- [x] 第四批：螺旋、延迟线、组合光路，共 7 种。
  - [x] 已接入：`spiral`、`spiral_racetrack_fixed_length`、`delay_snake_sbend`、`mzi`、`splitter_tree`、`dbr`、`loop_mirror`。
- [x] 通用热调结构扩展：`mzi2x2_2x2_phase_shifter`、`straight_heater_metal`；生成热调层和电端口，电极自动布线暂不包含。

每种器件的完成标准：

1. 参数可查询，默认或明确示例参数可生成器件。
2. 实际端口和适用连接方式可查询；阵列、光纤接口等端口按类型区分。
3. 开放的参数可修改；失败时保留原设计。
4. JSON 保存和恢复后参数、摆放和连接一致。
5. 能生成 GDS 和预览，相关参数及集成检查通过。
6. 提供至少一个可复现用例；注明工艺或参数依赖。

### 阶段四：摆放、多端口连接与布线

- [x] 指定和查询器件位置、角度及必要的镜像变换；通过 `place_component` 持久化 `x_um`、`y_um`、`rotation_deg`、`mirror_x`。
- [x] 区分端口直接贴合与通过波导连接远处端口；`connect_components` 为 direct，`route_components` 为 route。
- [x] 提供单条光学连接的自动布线；当前支持已登记截面和可选弯曲半径的 Manhattan route，暂不开放自定义途经点。
- [x] 检查端口存在性、类型、宽度、方向、占用和弯曲半径；类型、direct 宽度、最小半径为阻断错误，route 自动 taper 和额外弯曲为警告。
- [x] 拒绝或解释互相冲突的连接；placement 记录 `is_explicit`，direct 不得移动显式摆放的目标器件并建议使用 route。
- [x] 修改器件参数后在候选设计中重建真实端口，逐条检查原连接；失败时原子回滚，route 可返回自动 taper 警告。

完成标准：能构建带弯曲的线路和 MMI 分光线路，多端口器件连接正确；
无法满足的连接明确报错，原设计保持有效。

### 阶段五：基本编辑

- [x] `delete_component`：默认拒绝删除尚有连接的器件；仅在 `delete_connections=true` 时原子删除器件及全部相关 direct/route。
- [x] `rename_component`：原子重命名器件，同步更新全部 direct/route 中的源和目标引用，并保留参数、placement 与路由设置。
- [x] `disconnect_components`：按无序端点精确断开指定 direct/route；direct 断开时将目标器件的最终变换保存为显式 placement，route 断开时保持两端原 placement。
- [x] `copy_component`：以新名称深复制类型、参数和 placement；不复制连接，并明确提示复制品初始与原件重叠。
- [x] 统一名称重复、器件缺失、端口缺失、非法参数等错误返回；包含稳定的 `error_type`、错误原因、修正建议和未改变的设计快照。

完成标准：编辑后不残留悬空引用，保存恢复结果与当前设计一致。

### 阶段六：预览、检查、图层与工艺

- [x] 按需生成独立 PNG 预览，支持开关器件名称、`component.port` 端口标签和 GDS layer/datatype 图例；不生成 GDS/JSON，不改变保存状态。
- [x] 检查未连接端口、连接宽度/类型、重复连接和端口重复占用，并区分 warning 与 blocking error。
- [x] 使用同一 GDS 图层上的真实多边形交集面积检测器件实例间重叠；单个 MMI/coupler/ring 等器件内部结构不误报，已连接器件重叠为警告，未连接器件重叠为阻断错误。
- [x] `export_gds` 导出前复用 `check_design`；阻断错误不创建文件，警告允许导出，结果列出 checks_performed、scope 和未检查项目。
- [x] 公开通用参数同时接受 nm 与 um/µm，未写单位的长度数字默认 nm，并在 MCP 边界统一转换为内部 µm；带 `_um` 的兼容字段保持显式微米，角度为 degree，计数和无量纲参数不换算，旧 JSON 不重新解释。
- [x] 通过集中 `technology.py` 和只读 `get_technology` 管理 PDK 图层及 strip/rib/slot；区分运行时读取的默认宽度、默认弯曲半径和真正 `radius_min`，route 按最小半径阻断。
- [x] 记录当前 gdsfactory generic PDK 9.51.0、运行时参数来源、GDS database unit 和“非晶圆厂认证”限制；确定具体目标工艺时再替换 PDK 并配置 foundry DRC。

完成标准：预览可读、检查结果可解释；通用版图检查与特定工艺制造检查明确区分。

### 阶段七：第一版验收与文档

- [x] 原定 25 种器件逐项达到接入标准；加入通用热调结构和论文 Demo 微环链后共 28 种。
- [x] 以“800 nm × 500 µm 直波导连接 800→500 nm taper”为自然语言验收场景，通过独立 stdio MCP 子进程完成器件/参数/工艺查询、创建、连接、修改、保存、重新加载、检查和 GDS/JSON/PNG 导出；纳入自动回归测试。
- [x] 提供可重复运行的“直波导接 taper”“弯曲线路”“MMI 分光线路”三个完整 Python 示例；每例导出 JSON/GDS/PNG 前执行设计检查，自动测试验证器件数、direct/route 类型、文件和零阻断错误，并完成 PNG 视觉验收。
- [x] 通过真实 stdio MCP 子进程连续验证非法单位、重复名称、非法修改、错误端口、受保护删除、重命名冲突、不存在连接、损坏/缺失 JSON、越界路径和重复导出；每次失败后器件、参数、连接及保存状态与最后有效设计完全一致。
- [x] 整理零基础使用指南，覆盖安装与环境检查、stdio 启动、通用 MCP 客户端配置、首次完整对话、23 个工具、参数与单位规则、返回结果和常见错误排查。
- [x] 使用 `uv.lock` 锁定并核对依赖版本；在独立空虚拟环境中完成安装、gdsfactory 版本、23 个工具和 277 项测试验证。
- [x] 在 README 和第一版验收记录中说明参数白名单、单条 Manhattan route、generic PDK、几何检查、仿真、GDS 反向恢复和并发范围限制。

## 贯穿各阶段的规范

- 为实际行为、错误处理和完整流程添加必要测试，按变更风险运行检查。
- MCP 工具说明包含用途、参数、单位、返回结果和副作用。
- 明确区分“设计已保存”“GDS 已导出”“检查已通过”。
- 沿用分层结构：数据模型、设计操作、gdsfactory 几何、MCP 入口各有职责。
- 保护已有文件和用户改动；未经用户要求不提交 Git 或上传 GitHub。
- 不把器件函数存在视为接入完成，不把默认几何视为光学性能证明。

## 边开发边教学

用户是零基础学习者，按本项目实际代码教学：

- 开始前说明本次做什么、为什么需要。
- 每次只解释当前改动涉及的少量知识，不要求先学整套课程。
- 新术语给出中文、英文，并说明大家常用哪种叫法。
- 完成后说明改了哪些文件、核心代码怎样工作、验证结果及下一步。

常见术语：

| 中文 | 英文 | 常用叫法 |
| --- | --- | --- |
| 器件、单元 | component / cell | 中文常说“器件”，代码常见 component、cell |
| 参数定义 | schema | 开发者常直接说 schema |
| 接口 | Application Programming Interface | API 或接口 |
| 布线 | routing | 中文常说“布线” |
| 截面 | cross-section | 中文常说“截面” |
| 工艺设计套件 | Process Design Kit | PDK |
| 持久化 | persistence | 中文常说“持久化” |
| 反序列化 | deserialization | 中文常说“反序列化” |

第一版计划已全部完成。下一步在用户确认后整理 Git 仓库提交内容，并准备首次 GitHub 发布；发布前补充许可证、仓库地址和贡献说明。
