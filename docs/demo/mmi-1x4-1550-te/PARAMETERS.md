# Demo 参数：1550 nm TE 1×4 MMI 分光网络

本目录是可核对的演示材料包（提示词、GDS、预览与 KLayout 截图）。

## 参数表

| 参数 | 值 | 来源 |
|---|---|---|
| 波长 / 偏振 | 1550 nm / TE | 用户提示词 |
| 拓扑 | 两级分光树：3× `mmi1x2`，1 入 + 4 出椭圆光栅耦合器 | 用户提示词 |
| strip 波导宽 | 500 nm（0.5 µm） | 用户提示词（与 generic strip 默认一致） |
| 欧拉弯曲半径 | 100 μm | 用户提示词（脚本路由 `radius_um=100`） |
| 两级 MMI 横向间距 | 400 μm | 用户提示词（`splitter_tree.spacing_x`） |
| 第二级上下间距 | 254 μm | 用户提示词（`splitter_tree.spacing_y`） |
| 输出光栅纵向间距 | 127 μm（= 254 / 2） | 用户提示词（由树输出端口间距自然得到） |
| PDK | gdsfactory generic PDK | 用户提示词 |

## 实现侧默认值（提示词未逐条指定）

| 项 | 值 | 说明 |
|---|---|---|
| 树器件 | `splitter_tree`（内部 3× `mmi1x2`） | 用现有包 API 复现“三 MMI 树”，而非手摆三个独立 MMI 单元 |
| 光栅波长参数 | `wavelength=1.55` µm，`polarization=te` | 与提示词一致；其余椭圆 GC 几何用工厂默认 |
| MMI 内部尺寸 | generic `mmi1x2` 默认 | 提示词写“采用 generic PDK 默认器件参数” |
| 输入 GC 旋转 | 180° | 光路从左向右 |
| 树原点 x | 200 µm | 脚本布局默认（`tree_x_um`） |
| 树输出到 GC 间距 | 200 µm | 脚本布局默认（`gc_gap_um`） |
| 默认输出目录 | `build/mmi_1x4_1550_te/` | `scripts/build_1x4_mmi_network.py` |

## 文件

| 文件 | 说明 |
|---|---|
| `prompt.txt` | 与 README Demo 提示词一致的纯文本 |
| `mmi_1x4_1550_te.gds` | 由 `uv run python scripts/build_1x4_mmi_network.py` 生成 |
| `mmi_1x4_1550_te.json` | 可再编辑的设计 JSON |
| `preview.png` | gdsfactory/matplotlib 标注预览 |
| `klayout_screenshot.png` | 用 KLayout 0.28 打开上述 GDS 后导出的截图（含标尺） |

重新生成（会覆盖本目录中的 GDS/JSON/PNG；截图需另跑 KLayout）：

```bash
uv run python scripts/build_1x4_mmi_network.py --output-dir docs/demo/mmi-1x4-1550-te
mv docs/demo/mmi-1x4-1550-te/mmi_1x4_1550_te.png docs/demo/mmi-1x4-1550-te/preview.png
```
