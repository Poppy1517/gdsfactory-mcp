"""Explicit allowlist of component types supported by the first release."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

IntegrationStatus = Literal["integrated", "planned"]
ComponentCategoryKey = Literal[
    "waveguide_bend_crossing",
    "taper",
    "coupler",
    "mmi",
    "resonator",
    "grating_coupler",
    "edge_coupler",
    "spiral_delay",
    "circuit",
]


@dataclass(frozen=True)
class ComponentCategory:
    """One user-facing group of related photonic components."""

    key: str
    name_zh: str
    name_en: str
    common_name: str


@dataclass(frozen=True)
class ComponentDefinition:
    """One allowed component type and its registered gdsfactory factory."""

    type_name: str
    category: ComponentCategoryKey
    factory_name: str
    name_zh: str
    common_name: str
    status: IntegrationStatus


_CATEGORIES = (
    ComponentCategory("waveguide_bend_crossing", "波导、弯曲与交叉", "waveguide, bend and crossing", "波导 / bend / 交叉"),
    ComponentCategory("taper", "渐变波导", "taper", "taper"),
    ComponentCategory("coupler", "耦合器", "coupler", "耦合器"),
    ComponentCategory("mmi", "多模干涉器", "multimode interferometer", "MMI"),
    ComponentCategory("resonator", "环形与微盘谐振器", "ring and disk resonator", "微环 / 微盘"),
    ComponentCategory("grating_coupler", "光栅耦合器", "grating coupler", "光栅耦合器 / GC"),
    ComponentCategory("edge_coupler", "端面耦合器", "edge coupler", "端面耦合器"),
    ComponentCategory("spiral_delay", "螺旋与延迟线", "spiral and delay line", "螺旋波导 / 延迟线"),
    ComponentCategory("circuit", "组合光路", "photonic circuit", "光路"),
)

_COMPONENTS = (
    ComponentDefinition("straight", "waveguide_bend_crossing", "straight", "直波导", "straight", "integrated"),
    ComponentDefinition("bend_euler", "waveguide_bend_crossing", "bend_euler", "欧拉弯曲", "Euler bend", "integrated"),
    ComponentDefinition("bend_s", "waveguide_bend_crossing", "bend_s", "S 形弯曲", "S-bend", "integrated"),
    ComponentDefinition("crossing", "waveguide_bend_crossing", "crossing", "波导交叉", "crossing", "integrated"),
    ComponentDefinition("taper", "taper", "taper", "线性渐变波导", "taper", "integrated"),
    ComponentDefinition("taper_adiabatic", "taper", "taper_adiabatic", "绝热渐变波导", "adiabatic taper", "integrated"),
    ComponentDefinition("coupler", "coupler", "coupler", "定向耦合器", "coupler", "integrated"),
    ComponentDefinition("coupler_straight", "coupler", "coupler_straight", "直耦合区", "straight coupler", "integrated"),
    ComponentDefinition("coupler_ring", "coupler", "coupler_ring", "微环耦合结构", "ring coupler", "integrated"),
    ComponentDefinition("mmi1x2", "mmi", "mmi1x2", "一分二多模干涉器", "MMI 1x2", "integrated"),
    ComponentDefinition("mmi2x2", "mmi", "mmi2x2", "二进二出多模干涉器", "MMI 2x2", "integrated"),
    ComponentDefinition("ring_single", "resonator", "ring_single", "单总线微环", "single-bus ring", "integrated"),
    ComponentDefinition("ring_double", "resonator", "ring_double", "双总线微环", "double-bus ring", "integrated"),
    ComponentDefinition("coupled_ring_chain", "resonator", "ring_crow", "四级耦合微环链", "four-ring CROW", "integrated"),
    ComponentDefinition("disk", "resonator", "disk", "微盘谐振器", "disk", "integrated"),
    ComponentDefinition("grating_coupler_elliptical", "grating_coupler", "grating_coupler_elliptical", "椭圆聚焦光栅耦合器", "elliptical GC", "integrated"),
    ComponentDefinition("grating_coupler_rectangular", "grating_coupler", "grating_coupler_rectangular", "矩形光栅耦合器", "rectangular GC", "integrated"),
    ComponentDefinition("edge_coupler_silicon", "edge_coupler", "edge_coupler_silicon", "硅端面耦合器", "silicon edge coupler", "integrated"),
    ComponentDefinition("edge_coupler_array", "edge_coupler", "edge_coupler_array", "端面耦合器阵列", "edge coupler array", "integrated"),
    ComponentDefinition("spiral", "spiral_delay", "spiral", "螺旋波导", "spiral", "integrated"),
    ComponentDefinition("spiral_racetrack_fixed_length", "spiral_delay", "spiral_racetrack_fixed_length", "指定长度跑道形螺旋", "fixed-length racetrack spiral", "integrated"),
    ComponentDefinition("delay_snake_sbend", "spiral_delay", "delay_snake_sbend", "S 弯蛇形延迟线", "snake delay", "integrated"),
    ComponentDefinition("mzi", "circuit", "mzi", "马赫–曾德尔干涉仪", "MZI", "integrated"),
    ComponentDefinition("mzi2x2_2x2_phase_shifter", "circuit", "mzi2x2_2x2_phase_shifter", "带热调移相器的二进二出马赫–曾德尔干涉仪", "heater MZI 2x2", "integrated"),
    ComponentDefinition("straight_heater_metal", "circuit", "straight_heater_metal", "金属加热直波导", "thermo-optic phase shifter", "integrated"),
    ComponentDefinition("splitter_tree", "circuit", "splitter_tree", "分光树", "splitter tree", "integrated"),
    ComponentDefinition("dbr", "circuit", "dbr", "分布式布拉格反射器", "DBR", "integrated"),
    ComponentDefinition("loop_mirror", "circuit", "loop_mirror", "环路反射镜", "loop mirror", "integrated"),
)

CATEGORY_REGISTRY = MappingProxyType({item.key: item for item in _CATEGORIES})
COMPONENT_REGISTRY = MappingProxyType({item.type_name: item for item in _COMPONENTS})
ALLOWED_COMPONENT_TYPES = frozenset(COMPONENT_REGISTRY)

# References exposed to JSON are data-only names, never arbitrary Python callables.
REGISTERED_REFERENCES = MappingProxyType({
    "cross_section": frozenset({"strip", "rib", "slot"}),
})


def get_component_definition(type_name: str) -> ComponentDefinition:
    """Return one registered definition; reject names outside the allowlist."""
    try:
        return COMPONENT_REGISTRY[type_name]
    except KeyError as error:
        raise ValueError(f"unsupported component type: {type_name}") from error

