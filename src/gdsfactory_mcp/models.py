"""Serializable descriptions of a photonic layout."""

from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gdsfactory_mcp.registry import REGISTERED_REFERENCES, get_component_definition

PositiveMicrometre = Annotated[float, Field(gt=0)]
EulerFraction = Annotated[float, Field(ge=0, le=1)]
SignedBendValue = Annotated[float, Field(ge=-360, le=360)]
ComponentName = Annotated[
    str,
    Field(
        min_length=1,
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
        description="A short identifier such as wg1 or taper_input.",
    ),
]
PortName = Annotated[
    str,
    Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z_][A-Za-z0-9_.-]*$",
        description="A real component port name such as o1, o3, or e1.",
    ),
]


class PlacementSpec(BaseModel):
    """Persistent placement applied before direct port connections."""

    model_config = ConfigDict(extra="forbid")
    x_um: Annotated[float, Field(ge=-1_000_000, le=1_000_000)] = 0.0
    y_um: Annotated[float, Field(ge=-1_000_000, le=1_000_000)] = 0.0
    rotation_deg: Annotated[float, Field(ge=-360, le=360)] = 0.0
    mirror_x: bool = False
    is_explicit: bool = False

    @model_validator(mode="after")
    def nondefault_transform_is_explicit(self) -> "PlacementSpec":
        if not self.is_explicit and (
            self.x_um != 0
            or self.y_um != 0
            or self.rotation_deg != 0
            or self.mirror_x
        ):
            self.is_explicit = True
        return self


class RegisteredReference(BaseModel):
    """A data-only reference to an explicitly allowlisted gdsfactory object."""

    model_config = ConfigDict(extra="forbid")
    kind: Literal["registered_reference"] = "registered_reference"
    reference_type: Literal["cross_section"]
    name: Annotated[str, Field(min_length=1, max_length=128)]

    @model_validator(mode="after")
    def name_is_registered(self) -> "RegisteredReference":
        allowed = REGISTERED_REFERENCES[self.reference_type]
        if self.name not in allowed:
            choices = ", ".join(sorted(allowed))
            raise ValueError(
                f"unregistered {self.reference_type} reference: {self.name}; "
                f"available references: {choices}"
            )
        return self


class StraightCreateParameters(BaseModel):
    """Safe generic-creation parameters for a straight waveguide."""

    model_config = ConfigDict(extra="forbid")
    length: PositiveMicrometre = 10.0
    width: PositiveMicrometre = 0.5
    cross_section: RegisteredReference | None = None


class TaperCreateParameters(BaseModel):
    """Safe generic-creation parameters for a linear taper."""

    model_config = ConfigDict(extra="forbid")
    length: PositiveMicrometre = 10.0
    width1: PositiveMicrometre = 0.5
    width2: PositiveMicrometre = 0.5
    cross_section: RegisteredReference | None = None


class BendEulerCreateParameters(BaseModel):
    """Safe parameters for an Euler bend."""

    model_config = ConfigDict(extra="forbid")
    radius: PositiveMicrometre = 10.0
    angle: SignedBendValue = 90.0
    p: EulerFraction = 0.5
    width: PositiveMicrometre = 0.5
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def angle_is_nonzero(self) -> "BendEulerCreateParameters":
        if self.angle == 0:
            raise ValueError("angle must not be 0")
        return self


class BendSCreateParameters(BaseModel):
    """Safe scalar parameters for an S-bend."""

    model_config = ConfigDict(extra="forbid")
    size_x: PositiveMicrometre = 11.0
    size_y: Annotated[float, Field(ge=-10_000, le=10_000)] = 1.8
    width: PositiveMicrometre = 0.5
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def vertical_offset_is_nonzero(self) -> "BendSCreateParameters":
        if self.size_y == 0:
            raise ValueError("size_y must not be 0")
        return self


class CrossingCreateParameters(BaseModel):
    """Safe flattened parameters for a four-port waveguide crossing."""

    model_config = ConfigDict(extra="forbid")
    r1: PositiveMicrometre = 3.0
    r2: PositiveMicrometre = 1.1
    arm_width: PositiveMicrometre = 1.2
    arm_length: PositiveMicrometre = 3.4
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def outer_radius_exceeds_inner_radius(self) -> "CrossingCreateParameters":
        if self.r1 <= self.r2:
            raise ValueError("r1 must be greater than r2")
        return self


class TaperAdiabaticCreateParameters(BaseModel):
    """Safe parameters for an automatically sized adiabatic taper."""

    model_config = ConfigDict(extra="forbid")
    width1: PositiveMicrometre = 0.5
    width2: PositiveMicrometre = 5.0
    alpha: Annotated[float, Field(gt=0, le=100)] = 1.0
    wavelength: Annotated[float, Field(gt=0, le=100)] = 1.55
    npoints: Annotated[int, Field(ge=20, le=5000)] = 200
    max_length: Annotated[float, Field(gt=0, le=10_000)] = 200.0

    @model_validator(mode="after")
    def endpoint_widths_differ(self) -> "TaperAdiabaticCreateParameters":
        if self.width1 == self.width2:
            raise ValueError("width1 and width2 must be different")
        return self


class MMICreateParameters(BaseModel):
    """Safe shared geometry parameters for MMI 1x2 and MMI 2x2."""

    model_config = ConfigDict(extra="forbid")
    width: PositiveMicrometre = 0.5
    width_taper: PositiveMicrometre = 1.0
    length_taper: PositiveMicrometre = 10.0
    length_mmi: PositiveMicrometre = 5.5
    width_mmi: PositiveMicrometre = 2.5
    gap_mmi: Annotated[float, Field(ge=0)] = 0.25
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def multimode_region_fits_output_tapers(self) -> "MMICreateParameters":
        required_width = 2 * self.width_taper + self.gap_mmi
        if self.width_mmi < required_width:
            raise ValueError(
                "width_mmi must be at least 2 * width_taper + gap_mmi"
            )
        return self


class CouplerCreateParameters(BaseModel):
    """Safe parameters for a complete directional coupler."""

    model_config = ConfigDict(extra="forbid")
    gap: PositiveMicrometre = 0.236
    length: PositiveMicrometre = 20.0
    dy: PositiveMicrometre = 4.0
    dx: PositiveMicrometre = 10.0
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def vertical_spacing_exceeds_gap(self) -> "CouplerCreateParameters":
        if self.dy <= self.gap:
            raise ValueError("dy must be greater than gap")
        return self


class CouplerStraightCreateParameters(BaseModel):
    """Safe parameters for a straight coupling region."""

    model_config = ConfigDict(extra="forbid")
    length: PositiveMicrometre = 10.0
    gap: PositiveMicrometre = 0.27
    cross_section: RegisteredReference | None = None


class CouplerRingCreateParameters(BaseModel):
    """Safe parameters for a ring coupling section."""

    model_config = ConfigDict(extra="forbid")
    gap: PositiveMicrometre = 0.2
    radius: PositiveMicrometre = 10.0
    length_x: PositiveMicrometre = 4.0
    cross_section: RegisteredReference | None = None
    cross_section_bend: RegisteredReference | None = None


class RingSingleCreateParameters(BaseModel):
    """Safe parameters for a single-bus ring resonator."""

    model_config = ConfigDict(extra="forbid")
    gap: PositiveMicrometre = 0.2
    radius: PositiveMicrometre = 10.0
    length_x: PositiveMicrometre = 4.0
    length_y: PositiveMicrometre = 0.6
    cross_section: RegisteredReference | None = None


class RingDoubleCreateParameters(BaseModel):
    """Safe parameters for a double-bus ring resonator."""

    model_config = ConfigDict(extra="forbid")
    gap: PositiveMicrometre = 0.2
    gap_top: PositiveMicrometre | None = None
    gap_bot: PositiveMicrometre | None = None
    radius: PositiveMicrometre = 10.0
    length_x: PositiveMicrometre = 0.01
    length_y: PositiveMicrometre = 0.01
    cross_section: RegisteredReference | None = None


class CoupledRingChainCreateParameters(BaseModel):
    """Safe paper-demo parameters for a four-ring coupled resonator chain."""

    model_config = ConfigDict(extra="forbid")
    radius: PositiveMicrometre = 10.0
    waveguide_width: PositiveMicrometre = 0.45
    gap_input: PositiveMicrometre = 0.151
    gap_12: PositiveMicrometre = 0.493
    gap_23: PositiveMicrometre = 0.587
    gap_34: PositiveMicrometre = 0.493
    gap_output: PositiveMicrometre = 0.151
    coupling_length: PositiveMicrometre = 0.01
    vertical_straight_length: PositiveMicrometre = 0.01
    include_electrodes: bool = True
    pad_width: PositiveMicrometre = 22.0
    pad_height: PositiveMicrometre = 28.0
    metal_width: PositiveMicrometre = 2.0


class DiskCreateParameters(BaseModel):
    """Safe parameters for a disk resonator."""

    model_config = ConfigDict(extra="forbid")
    radius: PositiveMicrometre = 10.0
    gap: PositiveMicrometre = 0.2
    wrap_angle_deg: Annotated[float, Field(gt=0, le=360)] = 180.0
    parity: Literal[-1, 1] = 1
    cross_section: RegisteredReference | None = None


class GratingCouplerEllipticalCreateParameters(BaseModel):
    """Safe parameters for an elliptical focusing grating coupler."""

    model_config = ConfigDict(extra="forbid")
    polarization: Literal["te", "tm"] = "te"
    taper_length: PositiveMicrometre = 16.6
    taper_angle: Annotated[float, Field(gt=0, lt=180)] = 40.0
    wavelength: Annotated[float, Field(gt=0, le=100)] = 1.554
    fiber_angle: Annotated[float, Field(ge=-90, le=90)] = 15.0
    grating_line_width: PositiveMicrometre = 0.343
    neff: PositiveMicrometre = 2.638
    nclad: PositiveMicrometre = 1.443
    n_periods: Annotated[int, Field(ge=1, le=1000)] = 30
    big_last_tooth: bool = False
    slab_xmin: Annotated[float, Field(ge=-10_000, le=10_000)] = -1.0
    slab_offset: PositiveMicrometre = 2.0
    spiked: bool = True
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def effective_index_exceeds_cladding(self) -> "GratingCouplerEllipticalCreateParameters":
        if self.neff <= self.nclad:
            raise ValueError("neff must be greater than nclad")
        return self


class GratingCouplerRectangularCreateParameters(BaseModel):
    """Safe parameters for a rectangular grating coupler."""

    model_config = ConfigDict(extra="forbid")
    n_periods: Annotated[int, Field(ge=1, le=1000)] = 20
    period: PositiveMicrometre = 0.75
    fill_factor: Annotated[float, Field(gt=0, lt=1)] = 0.5
    width_grating: PositiveMicrometre = 11.0
    length_taper: PositiveMicrometre = 150.0
    polarization: Literal["te", "tm"] = "te"
    wavelength: Annotated[float, Field(gt=0, le=100)] = 1.55
    fiber_angle: Annotated[float, Field(ge=-90, le=90)] = 15.0
    slab_xmin: Annotated[float, Field(ge=-10_000, le=10_000)] = -1.0
    slab_offset: PositiveMicrometre = 1.0
    cross_section: RegisteredReference | None = None


class EdgeCouplerSiliconCreateParameters(BaseModel):
    """Safe geometry parameters for one silicon edge coupler."""

    model_config = ConfigDict(extra="forbid")
    length: PositiveMicrometre = 100.0
    width1: PositiveMicrometre = 0.5
    width2: PositiveMicrometre = 0.2
    cross_section: RegisteredReference | None = None


class EdgeCouplerArrayCreateParameters(BaseModel):
    """Safe flattened parameters for an array of silicon edge couplers."""

    model_config = ConfigDict(extra="forbid")
    n: Annotated[int, Field(ge=1, le=256)] = 5
    pitch: PositiveMicrometre = 127.0
    x_reflection: bool = False
    length: PositiveMicrometre = 100.0
    width1: PositiveMicrometre = 0.5
    width2: PositiveMicrometre = 0.2
    cross_section: RegisteredReference | None = None
    include_text: bool = True


class SpiralCreateParameters(BaseModel):
    """Safe parameters for a double spiral waveguide."""

    model_config = ConfigDict(extra="forbid")
    length: PositiveMicrometre = 100.0
    spacing: PositiveMicrometre = 3.0
    n_loops: Annotated[int, Field(ge=2, le=100)] = 6
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def loop_count_is_even(self) -> "SpiralCreateParameters":
        if self.n_loops % 2:
            raise ValueError("n_loops must be even")
        return self


class SpiralRacetrackFixedLengthCreateParameters(BaseModel):
    """Safe parameters for a racetrack spiral with a target total length."""

    model_config = ConfigDict(extra="forbid")
    length: PositiveMicrometre = 1000.0
    in_out_port_spacing: PositiveMicrometre = 150.0
    n_straight_sections: Annotated[int, Field(ge=2, le=100)] = 8
    min_radius: PositiveMicrometre | None = None
    min_spacing: PositiveMicrometre = 5.0
    cross_section: RegisteredReference | None = None
    cross_section_s: RegisteredReference | None = None

    @model_validator(mode="after")
    def straight_section_count_is_even(
        self,
    ) -> "SpiralRacetrackFixedLengthCreateParameters":
        if self.n_straight_sections % 2:
            raise ValueError("n_straight_sections must be even")
        return self


class DelaySnakeSBendCreateParameters(BaseModel):
    """Safe scalar parameters for an S-bend snake delay line."""

    model_config = ConfigDict(extra="forbid")
    length: PositiveMicrometre = 100.0
    length1: Annotated[float, Field(ge=0)] = 0.0
    length4: Annotated[float, Field(ge=0)] = 0.0
    radius: PositiveMicrometre = 5.0
    waveguide_spacing: PositiveMicrometre = 5.0
    sbend_xsize: PositiveMicrometre = 100.0
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def end_straights_fit_length_budget(self) -> "DelaySnakeSBendCreateParameters":
        if self.length <= self.length1 + self.length4:
            raise ValueError("length must be greater than length1 + length4")
        return self


class MZICreateParameters(BaseModel):
    """Safe scalar parameters for a two-port Mach-Zehnder interferometer."""

    model_config = ConfigDict(extra="forbid")
    delta_length: Annotated[float, Field(ge=-10_000, le=10_000)] = 10.0
    length_y: PositiveMicrometre = 2.0
    length_x: PositiveMicrometre = 0.1
    nbends: Annotated[int, Field(ge=2, le=100)] = 2
    mirror_bot: bool = False
    min_length: PositiveMicrometre = 0.01
    cross_section: RegisteredReference | None = None


class MZI2x2PhaseShifterCreateParameters(BaseModel):
    """Safe parameters for a four-port MZI with a metal heater."""

    model_config = ConfigDict(extra="forbid")
    delta_length: Annotated[float, Field(ge=-10_000, le=10_000)] = 10.0
    length_y: PositiveMicrometre = 2.0
    length_x: PositiveMicrometre = 200.0
    nbends: Annotated[int, Field(ge=2, le=100)] = 2
    mirror_bot: bool = False
    min_length: PositiveMicrometre = 0.01
    cross_section: RegisteredReference | None = None


class StraightHeaterMetalCreateParameters(BaseModel):
    """Safe geometry parameters for a straight metal-heated waveguide."""

    model_config = ConfigDict(extra="forbid")
    length: PositiveMicrometre = 320.0
    with_undercut: bool = False
    heater_taper_length: PositiveMicrometre = 5.0
    cross_section: RegisteredReference | None = None


class SplitterTreeCreateParameters(BaseModel):
    """Safe flattened parameters for a binary splitter tree."""

    model_config = ConfigDict(extra="forbid")
    noutputs: Annotated[int, Field(ge=2, le=256)] = 4
    spacing_x: PositiveMicrometre = 90.0
    spacing_y: PositiveMicrometre = 50.0
    bend_s_xsize: PositiveMicrometre | None = None
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def output_count_is_power_of_two(self) -> "SplitterTreeCreateParameters":
        if self.noutputs & (self.noutputs - 1):
            raise ValueError("noutputs must be a power of 2")
        return self


class DBRCreateParameters(BaseModel):
    """Safe parameters for a one-port distributed Bragg reflector."""

    model_config = ConfigDict(extra="forbid")
    w1: PositiveMicrometre = 0.45
    w2: PositiveMicrometre = 0.55
    l1: PositiveMicrometre = 0.159
    l2: PositiveMicrometre = 0.159
    n: Annotated[int, Field(ge=1, le=10_000)] = 10
    straight_length: PositiveMicrometre = 0.01
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def widths_are_different(self) -> "DBRCreateParameters":
        if self.w1 == self.w2:
            raise ValueError("w1 and w2 must be different")
        return self


class LoopMirrorCreateParameters(BaseModel):
    """Safe flattened MMI geometry for a one-port loop mirror."""

    model_config = ConfigDict(extra="forbid")
    width: PositiveMicrometre = 0.5
    width_taper: PositiveMicrometre = 1.0
    length_taper: PositiveMicrometre = 10.0
    length_mmi: PositiveMicrometre = 5.5
    width_mmi: PositiveMicrometre = 2.5
    gap_mmi: Annotated[float, Field(ge=0)] = 0.25
    cross_section: RegisteredReference | None = None

    @model_validator(mode="after")
    def multimode_region_fits_output_tapers(self) -> "LoopMirrorCreateParameters":
        required_width = 2 * self.width_taper + self.gap_mmi
        if self.width_mmi < required_width:
            raise ValueError(
                "width_mmi must be at least 2 * width_taper + gap_mmi"
            )
        return self


def validate_generic_parameters(
    type_name: str,
    parameters: dict[str, object],
) -> dict[str, object]:
    """Validate and normalize parameters for an integrated generic component."""
    definition = get_component_definition(type_name)
    if definition.status != "integrated":
        raise ValueError(
            f"component type is registered but not yet available for creation: {type_name}"
        )
    if type_name == "straight":
        return StraightCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "taper":
        return TaperCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "bend_euler":
        return BendEulerCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "bend_s":
        return BendSCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "crossing":
        return CrossingCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "taper_adiabatic":
        return TaperAdiabaticCreateParameters.model_validate(parameters).model_dump()
    if type_name in {"mmi1x2", "mmi2x2"}:
        return MMICreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "coupler":
        return CouplerCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "coupler_straight":
        return CouplerStraightCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "coupler_ring":
        return CouplerRingCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "ring_single":
        return RingSingleCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "ring_double":
        return RingDoubleCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "coupled_ring_chain":
        return CoupledRingChainCreateParameters.model_validate(
            parameters,
        ).model_dump(exclude_none=True)
    if type_name == "disk":
        return DiskCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "grating_coupler_elliptical":
        return GratingCouplerEllipticalCreateParameters.model_validate(
            parameters,
        ).model_dump(exclude_none=True)
    if type_name == "grating_coupler_rectangular":
        return GratingCouplerRectangularCreateParameters.model_validate(
            parameters,
        ).model_dump(exclude_none=True)
    if type_name == "edge_coupler_silicon":
        return EdgeCouplerSiliconCreateParameters.model_validate(
            parameters,
        ).model_dump(exclude_none=True)
    if type_name == "edge_coupler_array":
        return EdgeCouplerArrayCreateParameters.model_validate(
            parameters,
        ).model_dump(exclude_none=True)
    if type_name == "spiral":
        return SpiralCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "spiral_racetrack_fixed_length":
        return SpiralRacetrackFixedLengthCreateParameters.model_validate(
            parameters,
        ).model_dump(exclude_none=True)
    if type_name == "delay_snake_sbend":
        return DelaySnakeSBendCreateParameters.model_validate(
            parameters,
        ).model_dump(exclude_none=True)
    if type_name == "mzi":
        return MZICreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "mzi2x2_2x2_phase_shifter":
        return MZI2x2PhaseShifterCreateParameters.model_validate(
            parameters,
        ).model_dump(exclude_none=True)
    if type_name == "straight_heater_metal":
        return StraightHeaterMetalCreateParameters.model_validate(
            parameters,
        ).model_dump(exclude_none=True)
    if type_name == "splitter_tree":
        return SplitterTreeCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "dbr":
        return DBRCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    if type_name == "loop_mirror":
        return LoopMirrorCreateParameters.model_validate(parameters).model_dump(
            exclude_none=True,
        )
    raise ValueError(f"component type has no safe parameter adapter: {type_name}")


class StraightSpec(BaseModel):
    """Parameters needed to create one straight waveguide."""

    kind: Literal["straight"] = "straight"
    name: ComponentName
    length_um: PositiveMicrometre
    width_um: PositiveMicrometre
    placement: PlacementSpec = Field(default_factory=PlacementSpec)
    port_names: ClassVar[frozenset[str]] = frozenset({"o1", "o2"})


class TaperSpec(BaseModel):
    """Parameters needed to create one linear taper."""

    kind: Literal["taper"] = "taper"
    name: ComponentName
    length_um: PositiveMicrometre
    width1_um: PositiveMicrometre
    width2_um: PositiveMicrometre
    placement: PlacementSpec = Field(default_factory=PlacementSpec)
    port_names: ClassVar[frozenset[str]] = frozenset({"o1", "o2"})


class GenericComponentSpec(BaseModel):
    """Extensible component record used by the generic MCP workflow."""

    kind: Literal["component"] = "component"
    name: ComponentName
    type_name: str
    parameters: dict[str, object] = Field(default_factory=dict)
    placement: PlacementSpec = Field(default_factory=PlacementSpec)

    @model_validator(mode="after")
    def parameters_are_safe(self) -> "GenericComponentSpec":
        self.parameters = validate_generic_parameters(
            self.type_name, self.parameters,
        )
        return self

    @property
    def port_names(self) -> frozenset[str]:
        """Return declared ports for connection validation."""
        if self.type_name == "crossing":
            return frozenset({"o1", "o2", "o3", "o4"})
        if self.type_name == "mmi1x2":
            return frozenset({"o1", "o2", "o3"})
        if self.type_name == "mmi2x2":
            return frozenset({"o1", "o2", "o3", "o4"})
        if self.type_name in {"coupler", "coupler_straight", "coupler_ring"}:
            return frozenset({"o1", "o2", "o3", "o4"})
        if self.type_name == "ring_double":
            return frozenset({"o1", "o2", "o3", "o4"})
        if self.type_name == "coupled_ring_chain":
            return frozenset({"input", "through", "drop", "add"})
        if self.type_name in {"ring_single", "disk"}:
            return frozenset({"o1", "o2"})
        if self.type_name in {
            "grating_coupler_elliptical", "grating_coupler_rectangular",
        }:
            return frozenset({"o1", "o2"})
        if self.type_name == "edge_coupler_silicon":
            return frozenset({"o1", "o2"})
        if self.type_name == "edge_coupler_array":
            return frozenset(
                f"o{index}" for index in range(1, int(self.parameters["n"]) + 1)
            )
        if self.type_name in {"spiral", "spiral_racetrack_fixed_length"}:
            return frozenset({"o1", "o2"})
        if self.type_name == "delay_snake_sbend":
            return frozenset({"o1", "o2"})
        if self.type_name == "mzi":
            return frozenset({"o1", "o2"})
        if self.type_name == "mzi2x2_2x2_phase_shifter":
            return frozenset({
                "o1", "o2", "o3", "o4",
                "e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8",
            })
        if self.type_name == "straight_heater_metal":
            return frozenset({
                "o1", "o2",
                "l_e1", "l_e2", "l_e3", "l_e4",
                "r_e1", "r_e2", "r_e3", "r_e4",
            })
        if self.type_name == "splitter_tree":
            noutputs = int(self.parameters["noutputs"])
            level = noutputs.bit_length() - 2
            return frozenset(
                {"o1_0_0"}
                | {f"o2_{level}_{index}" for index in range(1, noutputs + 1)}
            )
        if self.type_name == "dbr":
            return frozenset({"o1"})
        if self.type_name == "loop_mirror":
            return frozenset({"o1"})
        if self.type_name in {
            "straight", "taper", "taper_adiabatic", "bend_euler", "bend_s",
        }:
            return frozenset({"o1", "o2"})
        return frozenset()


ComponentSpec = Annotated[
    StraightSpec | TaperSpec | GenericComponentSpec,
    Field(discriminator="kind"),
]


class ConnectionSpec(BaseModel):
    """A connection between two named component ports."""

    model_config = ConfigDict(extra="forbid")
    source_component: ComponentName
    source_port: PortName
    target_component: ComponentName
    target_port: PortName
    connection_type: Literal["direct", "route"] = "direct"
    cross_section: RegisteredReference | None = None
    radius_um: PositiveMicrometre | None = None
    waypoints_um: list[
        tuple[
            Annotated[float, Field(ge=-1_000_000, le=1_000_000)],
            Annotated[float, Field(ge=-1_000_000, le=1_000_000)],
        ]
    ] | None = None

    @model_validator(mode="after")
    def direct_connection_has_no_route_options(self) -> "ConnectionSpec":
        if self.connection_type == "direct" and (
            self.cross_section is not None
            or self.radius_um is not None
            or self.waypoints_um is not None
        ):
            raise ValueError("direct connections cannot include route options")
        return self


class DesignSpec(BaseModel):
    """The complete, serializable design intent."""

    name: ComponentName
    components: list[ComponentSpec] = Field(default_factory=list)
    connections: list[ConnectionSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def component_names_are_unique(self) -> "DesignSpec":
        names = [component.name for component in self.components]
        if len(names) != len(set(names)):
            raise ValueError("component names must be unique")
        seen_connections = set()
        used_ports: set[tuple[str, str]] = set()
        components_by_name = {
            component.name: component for component in self.components
        }
        for connection in self.connections:
            if (connection.source_component not in names
                    or connection.target_component not in names):
                raise ValueError("connection references a component that does not exist")
            if connection.source_component == connection.target_component:
                raise ValueError("a component cannot connect to itself")
            source = components_by_name[connection.source_component]
            target = components_by_name[connection.target_component]
            if (
                connection.connection_type == "direct"
                and target.placement.is_explicit
            ):
                raise ValueError(
                    f"direct connection would move explicitly placed target: "
                    f"{target.name}; use route_components instead"
                )
            if connection.source_port not in source.port_names:
                available = ", ".join(sorted(source.port_names))
                raise ValueError(
                    f"port does not exist: {source.name}.{connection.source_port}; "
                    f"available ports: {available}"
                )
            if connection.target_port not in target.port_names:
                available = ", ".join(sorted(target.port_names))
                raise ValueError(
                    f"port does not exist: {target.name}.{connection.target_port}; "
                    f"available ports: {available}"
                )
            key = (connection.source_component, connection.source_port,
                   connection.target_component, connection.target_port)
            if key in seen_connections:
                raise ValueError("connection already exists")
            seen_connections.add(key)
            endpoints = {
                (connection.source_component, connection.source_port),
                (connection.target_component, connection.target_port),
            }
            reused = endpoints & used_ports
            if reused:
                component_name, port_name = sorted(reused)[0]
                raise ValueError(
                    f"port is already connected: {component_name}.{port_name}"
                )
            used_ports.update(endpoints)
        return self
