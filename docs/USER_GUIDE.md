# gdsfactory MCP 使用指南

这是一份面向零基础用户的操作说明。目标不是让你先学完整套 Python，而是让你能够启动
MCP、让 AI 调用工具生成版图，并且知道每一步产生了什么结果。

## 1. 先认识四个核心名词

- **gdsfactory**：Python 光子版图工具库，大家通常直接说“gdsfactory”。它真正负责生成器件几何和 GDS。
- **MCP Server（Model Context Protocol Server，模型上下文协议服务器）**：把 Python 功能提供给 AI 调用的程序，大家常说“MCP server”或“MCP 服务”。
- **MCP Client（Model Context Protocol Client，模型上下文协议客户端）**：连接 MCP server 的 AI 应用，大家常说“MCP client”或“MCP 客户端”。
- **Tool（工具）**：MCP server 对外提供的单个能力，例如创建器件、连接端口或导出 GDS，大家常说“tool”。

关系可以简单理解为：你对 AI 描述需求 → MCP 客户端选择 tool → 本项目调用 gdsfactory → 生成版图文件。

## 2. 安装与环境检查

在终端进入项目目录：

```bash
cd /absolute/path/to/gdsfactory-mcp
```

安装或同步项目依赖：

```bash
uv sync
```

检查关键程序和版本：

```bash
git --version
uv --version
uv run python --version
uv run python -c "import gdsfactory as gf; print(gf.__version__)"
```

最后运行自动测试：

```bash
uv run python -m pytest
```

看到全部测试通过，说明 Python 环境、依赖和主要功能可以正常工作。

## 3. 启动方式

### 3.1 独立生成三个示例

这不需要 MCP 客户端，适合先检查 gdsfactory 是否能生成文件：

```bash
uv run python examples/generate_examples.py --output-dir example_outputs
```

结果位于 `example_outputs/`。每个示例包含：

- `.json`：可继续编辑的参数、器件和连接数据；
- `.gds`：版图交换文件，大家常说“GDS”；
- `.png`：方便人眼查看的预览图。

### 3.2 手动启动 MCP server

```bash
uv run gdsfactory-mcp-server
```

服务器使用 stdio 等待 MCP 客户端通信。终端看起来停住通常不是故障，而是在等待消息。按
`Control+C` 可以停止手动启动的服务器。正常使用时一般由 MCP 客户端自动启动它，不需要先
在另一个终端运行。

## 4. MCP 客户端配置

支持本地 stdio MCP 的客户端通常需要填写 `command` 和 `args`。通用 JSON 配置如下：

```json
{
  "mcpServers": {
    "gdsfactory": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/gdsfactory-mcp",
        "run",
        "gdsfactory-mcp-server"
      ]
    }
  }
}
```

字段含义：

- `gdsfactory`：这项 MCP 服务在客户端中显示的名字，可以自行修改；
- `command`：客户端要运行的程序，这里是依赖管理工具 `uv`；
- `args`：传给 `uv` 的参数；`--directory` 指定项目目录，`run` 表示在项目虚拟环境中运行；
- `gdsfactory-mcp-server`：本项目在 `pyproject.toml` 中登记的服务器启动命令。

不同客户端的配置页面和最外层字段可能不同，但核心命令保持不变。如果客户端使用表单，
Command 填 `uv`，Arguments 按上面数组顺序逐项填写。保存配置后重启或重新连接 MCP；成功时
应能看到下面列出的 23 个工具。

## 5. 第一次完整对话

连接成功后，可以直接对 AI 说：

> 新建一个名为 first_chip 的设计。创建一段宽 800 nm、长 500 µm 的直波导，连接一个长
> 20 µm、从 800 nm 变为 500 nm 的 taper。检查设计，生成预览，然后导出 GDS。

AI 合理的调用顺序是：

1. `new_design` 新建设计；
2. `get_component_schema` 查询参数规则；
3. `create_component` 创建 `straight` 和 `taper`；
4. `get_component_ports` 确认实际端口；
5. `connect_components` 连接端口；
6. `check_design` 检查；
7. `preview_design` 生成带标注预览；
8. `export_gds` 导出 GDS、JSON 和 PNG。

推荐让 AI 在每一步后说明调用了哪个工具、参数如何解释，以及结果是否成功。

## 6. 23 个 MCP 工具

### 6.1 查询类：只读，不修改设计

| 工具 | 中文作用 | 何时使用 |
| --- | --- | --- |
| `get_design` | 查看当前设计 | 想确认器件、参数、连接和未保存状态时 |
| `list_component_types` | 列出 28 种器件 | 不知道支持哪些器件时 |
| `get_component_schema` | 查询器件参数规则 | 创建或修改器件前，确认参数名、单位、默认值和限制 |
| `get_technology` | 查看工艺配置 | 查询 PDK、图层、截面和最小弯曲半径时 |
| `get_component_ports` | 查看真实端口 | 连接前确认 `o1`、`o2` 等端口的位置、方向和宽度 |
| `list_designs` | 列出已保存方案 | 查找 `designs/` 中可加载的 JSON 时 |
| `check_design` | 检查设计 | 保存或导出前检查连接、端口和几何问题 |

### 6.2 设计与器件编辑类

| 工具 | 中文作用 | 关键注意事项 |
| --- | --- | --- |
| `new_design` | 新建设计 | 有未保存修改时默认拒绝替换 |
| `create_component` | 通用器件创建 | 推荐入口，支持全部 28 种器件；先查 schema |
| `create_straight` | 创建直波导 | 兼容旧接口，带 `_um` 的参数只使用微米 |
| `create_taper` | 创建线性 taper | 兼容旧接口，带 `_um` 的参数只使用微米 |
| `update_component` | 修改器件参数 | 一次修改一个或多个参数；失败时原设计不变 |
| `place_component` | 放置、旋转或镜像器件 | 顺序为镜像、逆时针旋转、平移 |
| `delete_component` | 删除器件 | 有连接时需明确允许同时删除连接 |
| `rename_component` | 重命名器件 | 自动更新连接中的名称引用 |
| `copy_component` | 复制器件 | 不复制连接；复制品最初与原件重叠 |

### 6.3 连接类

| 工具 | 中文作用 | 关键注意事项 |
| --- | --- | --- |
| `connect_components` | 端口直接连接 | 目标器件自动贴合；宽度不匹配会拒绝 |
| `route_components` | 自动波导布线 | 两个器件保持原位；需要绕行时可用 `waypoints_um` 指定若干 `[x, y]` 微米坐标；工具会自动补入真实起止端口 |
| `disconnect_components` | 断开连接 | 器件保留，direct 目标器件保持断开前位置 |

**Direct Connection（直接连接，常说“direct”）** 会让目标端口贴到源端口上。
**Route（路由或自动布线，常说“route”）** 不移动两端器件，而是在中间生成波导。

### 6.4 保存、预览与导出类

| 工具 | 中文作用 | 产生的文件 |
| --- | --- | --- |
| `save_design` | 保存可编辑方案 | 只生成 JSON，默认放入 `designs/` |
| `load_design` | 加载可编辑方案 | 读取 JSON 并替换内存中的当前设计 |
| `preview_design` | 生成带标注预览 | 只生成 PNG，默认放入 `previews/` |
| `export_gds` | 最终导出版图 | 同时生成 GDS、JSON 和带图层、器件名、端口名的标注 PNG，默认放入 `build/`；客户端应默认展示该图 |

## 7. 参数和单位规则

通用的 `create_component` 和 `update_component` 中，长度可以写成：

```json
500
"500 nm"
"0.5 um"
"0.5 µm"
{"value": 500, "unit": "nm"}
```

重要规则：

- 没写单位的裸数字默认是 **nm（nanometre，纳米，常说“纳米”或“nm”）**；
- `um` 和 `µm` 都代表 **micrometre（微米，常说“微米”或“um”）**；
- 内部计算和 JSON 文件统一保存为微米；
- `length_um`、`x_um`、`radius_um` 等明确带 `_um` 的兼容参数始终是微米；
- `rotation_deg`、`angle` 等角度使用 degree（度，常说“度”）；
- 数量、折射率、`p`、`fill_factor` 等无量纲参数不进行长度换算。

例如，创建直波导的通用工具参数可以是：

```json
{
  "name": "wg1",
  "type_name": "straight",
  "parameters": {
    "length": "500 um",
    "width": "800 nm"
  }
}
```

不要猜复杂器件的参数名。先调用 `get_component_schema`，再根据返回的
`generic_creation_exposed`、单位和限制填写参数。

## 8. 成功、警告和错误怎么读

- `ok: true`：工具调用成功；
- `ok: false`：调用失败；读取 `error_type`、`error` 和 `suggestion`；
- `warnings`：操作成功，但有需要注意的问题；
- `has_unsaved_changes: true`：内存设计相对最近保存或导出的版本有修改；
- `check_report.passed: false`：检查发现阻断错误，不能导出。

失败操作遵循 **Atomic Operation（原子操作，大家常说“原子操作”）**：要么全部成功，要么
完全不修改设计。不要因为一次调用失败就立即重建设计；先根据 `suggestion` 修正参数再调用。

## 9. 常见错误排查

### 客户端看不到工具

1. 在项目目录运行 `uv run gdsfactory-mcp-server`，确认命令可以启动；
2. 检查客户端配置中的项目绝对路径；
3. 检查 `command` 是否为 `uv`；如果客户端找不到它，可把终端中 `which uv` 返回的绝对路径填入 `command`；
4. 保存配置后重启或重新连接 MCP 客户端。

### `invalid_parameters`：参数错误

通常是参数名、单位、范围或类型不正确。调用 `get_component_schema` 查询该器件，只提交开放的
参数。长度单位只使用 `nm`、`um` 或 `µm`。

### `name_conflict`：名称冲突

器件名称必须唯一。换一个名称，或者先用 `get_design` 查看当前名称。

### `component_not_found` 或 `port_not_found`

先调用 `get_design` 检查器件名称，再调用 `get_component_ports` 获取真实端口名。不同器件的
端口数量可能不同，不能默认都有 `o1` 和 `o2`。

### direct 连接失败

direct 要求两端为可连接的片上光学端口，并且宽度一致。如果器件已经明确摆放、方向不合适
或需要中间弯曲，请改用 `route_components`。

### route 半径过小

调用 `get_technology` 查看所选截面的真正最小半径。增大 `radius_um`，或省略它以使用默认值。

### route 使用途经点

`waypoints_um` 只填写源端口与目标端口之间的中间点，不要重复填写端口坐标。相邻点以及端口到
首尾途经点应构成水平或垂直的 Manhattan 路径。服务会自动把真实源端口和目标端口补到路径
两端；`check_design` 也会验证生成的路线骨架是否真正抵达两个端口，发现断口时以
`disconnected_route_geometry` 错误阻止导出。

### 无法新建或加载设计

当前设计存在未保存修改。优先调用 `save_design`；只有确定不要这些修改时，才设置
`discard_unsaved_changes=true`。

### `file_conflict`：文件已存在

默认不覆盖任何文件。换一个名称，或在明确确认旧文件可以被替换后设置 `overwrite=true`。

### 设计检查阻止导出

读取 `check_report.findings` 中所有 `severity: "error"` 项并逐个修正。同层路由发生意外交叉、接触或重叠时，检查会给出位置并阻止导出；可移动器件、用 `waypoints_um` 绕行，或明确加入 crossing 器件。`warning` 需要人工查看，
但不会阻止导出。当前检查不是晶圆厂完整 DRC，也不代表已经通过光学仿真。

### GDS 已生成但效果不符合预期

先用 `preview_design` 打开带器件名和端口名的 PNG，再用 `get_design`、
`get_component_ports` 检查参数、位置和连接。GDS 成功生成只代表几何文件创建成功，不代表器件
具有预期光学性能。

## 10. 推荐的安全工作习惯

1. 新建设计；
2. 查询器件 schema；
3. 创建器件；
4. 查询端口并连接；
5. 先保存 JSON；
6. 生成预览并检查；
7. 修改后再次检查；
8. 最后导出 GDS；
9. 需要覆盖文件时明确说明覆盖对象。

项目目前使用 gdsfactory 的 generic PDK，适合学习和功能开发，不是晶圆厂认证的流片 PDK。
未来接入具体代工工艺后，还需要使用对应的图层、截面和 DRC 规则重新验证设计。
