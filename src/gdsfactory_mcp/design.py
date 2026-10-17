"""Operations for creating and editing a design description."""

from pathlib import Path
from collections.abc import Callable
from typing import Any

from gdsfactory_mcp.models import (
    ConnectionSpec,
    DesignSpec,
    GenericComponentSpec,
    PlacementSpec,
    RegisteredReference,
    PortName,
    StraightCreateParameters,
    StraightSpec,
    TaperCreateParameters,
    TaperSpec,
)
from gdsfactory_mcp.registry import get_component_definition


class DesignService:
    """Manage one design without depending on MCP or gdsfactory geometry."""

    def __init__(self, name: str, *, has_unsaved_changes: bool = False) -> None:
        self._design = DesignSpec(name=name)
        self._has_unsaved_changes = has_unsaved_changes

    @property
    def spec(self) -> DesignSpec:
        """Return a copy so callers cannot silently change internal state."""
        return self._design.model_copy(deep=True)

    @property
    def has_unsaved_changes(self) -> bool:
        """Report whether the current state changed since its last save or load."""
        return self._has_unsaved_changes

    def add_straight(self, name: str, *, length_um: float, width_um: float) -> None:
        self._ensure_name_is_available(name)
        component = StraightSpec(name=name, length_um=length_um, width_um=width_um)
        self._design.components.append(component)
        self._has_unsaved_changes = True

    def add_taper(
        self,
        name: str,
        *,
        length_um: float,
        width1_um: float,
        width2_um: float,
    ) -> None:
        self._ensure_name_is_available(name)
        component = TaperSpec(
            name=name,
            length_um=length_um,
            width1_um=width1_um,
            width2_um=width2_um,
        )
        self._design.components.append(component)
        self._has_unsaved_changes = True

    def add_component(
        self,
        name: str,
        type_name: str,
        parameters: dict[str, Any],
    ) -> GenericComponentSpec:
        """Create one component through the explicit safe generic allowlist."""
        definition = get_component_definition(type_name)
        if definition.status != "integrated":
            raise ValueError(
                f"component type is registered but not yet available for creation: {type_name}"
            )
        self._ensure_name_is_available(name)
        component = GenericComponentSpec(
            name=name,
            type_name=type_name,
            parameters=parameters,
        )
        self._design.components.append(component)
        self._has_unsaved_changes = True
        return component

    def connect(
        self,
        source_component: str,
        source_port: PortName,
        target_component: str,
        target_port: PortName,
    ) -> None:
        self._get_component(source_component)
        self._get_component(target_component)
        if source_component == target_component:
            raise ValueError("a component cannot connect to itself")

        connection = ConnectionSpec(
            source_component=source_component,
            source_port=source_port,
            target_component=target_component,
            target_port=target_port,
        )
        if connection in self._design.connections:
            raise ValueError("connection already exists")
        candidate = self._design.model_copy(deep=True)
        candidate.connections.append(connection)
        self._design = DesignSpec.model_validate(candidate.model_dump())
        self._has_unsaved_changes = True

    def route(
        self,
        source_component: str,
        source_port: PortName,
        target_component: str,
        target_port: PortName,
        *,
        cross_section: str = "strip",
        radius_um: float | None = None,
        waypoints_um: list[tuple[float, float]] | None = None,
    ) -> None:
        """Connect fixed component ports with a generated waveguide route."""
        self._get_component(source_component)
        self._get_component(target_component)
        if source_component == target_component:
            raise ValueError("a component cannot connect to itself")
        connection = ConnectionSpec(
            source_component=source_component,
            source_port=source_port,
            target_component=target_component,
            target_port=target_port,
            connection_type="route",
            cross_section=RegisteredReference(
                reference_type="cross_section",
                name=cross_section,
            ),
            radius_um=radius_um,
            waypoints_um=waypoints_um,
        )
        candidate = self._design.model_copy(deep=True)
        candidate.connections.append(connection)
        self._design = DesignSpec.model_validate(candidate.model_dump())
        self._has_unsaved_changes = True

    def update_component(self, name: str, **parameters: float) -> None:
        """Validate and replace the parameters of an existing component."""
        component = self._get_component(name)
        allowed = set(type(component).model_fields) - {"kind", "name", "placement"}
        unknown = set(parameters) - allowed
        if unknown:
            unknown_text = ", ".join(sorted(unknown))
            raise ValueError(f"unsupported parameters for {component.kind}: {unknown_text}")

        updated_data = component.model_dump() | parameters
        updated = type(component).model_validate(updated_data)
        index = self._design.components.index(component)
        self._design.components[index] = updated
        self._has_unsaved_changes = True

    def update_component_parameters(
        self,
        name: str,
        parameters: dict[str, Any],
        *,
        validate_candidate: Callable[[DesignSpec], None] | None = None,
    ) -> StraightSpec | TaperSpec | GenericComponentSpec:
        """Atomically update safe public parameters for one component."""
        component = self._get_component(name)
        if not parameters:
            raise ValueError("at least one parameter must be provided")

        if isinstance(component, GenericComponentSpec):
            updated = GenericComponentSpec(
                name=component.name,
                type_name=component.type_name,
                parameters=component.parameters | parameters,
                placement=component.placement,
            )
        elif isinstance(component, StraightSpec):
            current = {
                "length": component.length_um,
                "width": component.width_um,
            }
            values = StraightCreateParameters.model_validate(current | parameters)
            updated = StraightSpec(
                name=component.name,
                length_um=values.length,
                width_um=values.width,
                placement=component.placement,
            )
        elif isinstance(component, TaperSpec):
            current = {
                "length": component.length_um,
                "width1": component.width1_um,
                "width2": component.width2_um,
            }
            values = TaperCreateParameters.model_validate(current | parameters)
            updated = TaperSpec(
                name=component.name,
                length_um=values.length,
                width1_um=values.width1,
                width2_um=values.width2,
                placement=component.placement,
            )
        else:  # pragma: no cover - the component union prevents this branch
            raise ValueError(f"unsupported component type: {component.kind}")

        index = self._design.components.index(component)
        candidate = self._design.model_copy(deep=True)
        candidate.components[index] = updated
        validated_candidate = DesignSpec.model_validate(candidate.model_dump())
        if validate_candidate is not None:
            validate_candidate(validated_candidate)
        self._design = validated_candidate
        self._has_unsaved_changes = True
        return updated

    def place_component(
        self,
        name: str,
        *,
        x_um: float | None = None,
        y_um: float | None = None,
        rotation_deg: float | None = None,
        mirror_x: bool | None = None,
    ) -> PlacementSpec:
        """Atomically update persistent placement for one component."""
        component = self._get_component(name)
        changes = {
            key: value
            for key, value in {
                "x_um": x_um,
                "y_um": y_um,
                "rotation_deg": rotation_deg,
                "mirror_x": mirror_x,
            }.items()
            if value is not None
        }
        if not changes:
            raise ValueError("at least one placement value must be provided")
        placement = PlacementSpec.model_validate(
            component.placement.model_dump() | changes | {"is_explicit": True}
        )
        updated = type(component).model_validate(
            component.model_dump() | {"placement": placement.model_dump()}
        )
        index = self._design.components.index(component)
        candidate = self._design.model_copy(deep=True)
        candidate.components[index] = updated
        self._design = DesignSpec.model_validate(candidate.model_dump())
        self._has_unsaved_changes = True
        return placement

    def delete_component(
        self,
        name: str,
        *,
        delete_connections: bool = False,
    ) -> tuple[
        StraightSpec | TaperSpec | GenericComponentSpec,
        list[ConnectionSpec],
    ]:
        """Atomically delete a component and optionally its related connections."""
        component = self._get_component(name)
        related_connections = [
            connection
            for connection in self._design.connections
            if connection.source_component == name
            or connection.target_component == name
        ]
        if related_connections and not delete_connections:
            details = ", ".join(
                f"{item.source_component}.{item.source_port} -> "
                f"{item.target_component}.{item.target_port} ({item.connection_type})"
                for item in related_connections
            )
            raise ValueError(
                f"component '{name}' has {len(related_connections)} connection(s): "
                f"{details}; use delete_connections=true to remove them together"
            )

        candidate = self._design.model_copy(deep=True)
        candidate.components = [
            item for item in candidate.components if item.name != name
        ]
        candidate.connections = [
            item
            for item in candidate.connections
            if item.source_component != name and item.target_component != name
        ]
        self._design = DesignSpec.model_validate(candidate.model_dump())
        self._has_unsaved_changes = True
        return component, related_connections

    def rename_component(
        self,
        name: str,
        new_name: str,
    ) -> tuple[
        StraightSpec | TaperSpec | GenericComponentSpec,
        list[ConnectionSpec],
    ]:
        """Atomically rename a component and every connection reference."""
        component = self._get_component(name)
        if name == new_name:
            raise ValueError("new_name must be different from the current name")
        self._ensure_name_is_available(new_name)

        renamed = type(component).model_validate(
            component.model_dump() | {"name": new_name}
        )
        candidate = self._design.model_copy(deep=True)
        index = self._design.components.index(component)
        candidate.components[index] = renamed
        updated_connections = []
        for connection in candidate.connections:
            data = connection.model_dump()
            changed = False
            if data["source_component"] == name:
                data["source_component"] = new_name
                changed = True
            if data["target_component"] == name:
                data["target_component"] = new_name
                changed = True
            if changed:
                replacement = ConnectionSpec.model_validate(data)
                connection_index = candidate.connections.index(connection)
                candidate.connections[connection_index] = replacement
                updated_connections.append(replacement)

        self._design = DesignSpec.model_validate(candidate.model_dump())
        self._has_unsaved_changes = True
        return renamed, updated_connections

    def copy_component(
        self,
        name: str,
        new_name: str,
    ) -> StraightSpec | TaperSpec | GenericComponentSpec:
        """Copy one component's data and placement without copying connections."""
        component = self._get_component(name)
        if name == new_name:
            raise ValueError("new_name must be different from the source name")
        self._ensure_name_is_available(new_name)

        copied = type(component).model_validate(
            component.model_dump() | {"name": new_name}
        )
        candidate = self._design.model_copy(deep=True)
        candidate.components.append(copied)
        self._design = DesignSpec.model_validate(candidate.model_dump())
        self._has_unsaved_changes = True
        return copied

    def disconnect_components(
        self,
        component_a: str,
        port_a: PortName,
        component_b: str,
        port_b: PortName,
        *,
        direct_target_placement: PlacementSpec | None = None,
    ) -> ConnectionSpec:
        """Atomically remove the connection between two unordered endpoints."""
        first = self._get_component(component_a)
        second = self._get_component(component_b)
        if port_a not in first.port_names:
            raise ValueError(f"port does not exist: {component_a}.{port_a}")
        if port_b not in second.port_names:
            raise ValueError(f"port does not exist: {component_b}.{port_b}")
        requested_endpoints = {(component_a, port_a), (component_b, port_b)}
        matches = [
            connection
            for connection in self._design.connections
            if {
                (connection.source_component, connection.source_port),
                (connection.target_component, connection.target_port),
            }
            == requested_endpoints
        ]
        if not matches:
            raise ValueError(
                f"connection does not exist between {component_a}.{port_a} and "
                f"{component_b}.{port_b}"
            )
        connection = matches[0]
        candidate = self._design.model_copy(deep=True)
        candidate.connections.remove(connection)

        if connection.connection_type == "direct":
            if direct_target_placement is None:
                raise ValueError(
                    "direct_target_placement is required to preserve geometry"
                )
            target = next(
                item
                for item in candidate.components
                if item.name == connection.target_component
            )
            target_index = candidate.components.index(target)
            candidate.components[target_index] = type(target).model_validate(
                target.model_dump()
                | {"placement": direct_target_placement.model_dump()}
            )

        self._design = DesignSpec.model_validate(candidate.model_dump())
        self._has_unsaved_changes = True
        return connection

    def load_json(self, path: Path) -> None:
        """Validate a saved design before replacing the current state."""
        loaded = DesignSpec.model_validate_json(path.read_text(encoding="utf-8"))
        self._design = loaded
        self._has_unsaved_changes = False

    def save_json(self, path: Path) -> Path:
        """Save a human-readable copy of the design intent."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._design.model_dump_json(indent=2), encoding="utf-8")
        self._has_unsaved_changes = False
        return path

    def _ensure_name_is_available(self, name: str) -> None:
        if any(component.name == name for component in self._design.components):
            raise ValueError(f"component name already exists: {name}")

    def _get_component(
        self, name: str,
    ) -> StraightSpec | TaperSpec | GenericComponentSpec:
        for component in self._design.components:
            if component.name == name:
                return component
        raise ValueError(f"component does not exist: {name}")
