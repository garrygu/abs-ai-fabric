"""
Standard Asset Schema v1.0 - Pydantic Models

Runtime validation for ABS AI Fabric asset definitions.
Use these models to parse and validate asset.yaml files.

Usage:
    from schemas.asset_schema import Asset, ServiceAsset, AppAsset

    asset = Asset.model_validate(yaml_data)
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


# =========================
# Enums
# =========================

class AssetClass(str, Enum):
    APP = "app"
    SERVICE = "service"
    MODEL = "model"
    TOOL = "tool"
    DATASET = "dataset"


class OwnershipProvider(str, Enum):
    SYSTEM = "system"
    ADMIN = "admin"
    USER = "user"


class Visibility(str, Enum):
    SHARED = "shared"
    PRIVATE = "private"


class RuntimeType(str, Enum):
    CONTAINER = "container"
    NATIVE = "native"
    EXTERNAL = "external"


class LifecycleDesired(str, Enum):
    RUNNING = "running"
    ON_DEMAND = "on-demand"
    SUSPENDED = "suspended"


class LifecycleState(str, Enum):
    REGISTERED = "registered"
    INSTALLED = "installed"
    IDLE = "idle"
    WARMING = "warming"
    RUNNING = "running"
    SUSPENDED = "suspended"  # v1.0: Added for auto-sleep
    ERROR = "error"


class EndpointProtocol(str, Enum):
    REST = "rest"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


# =========================
# Nested Models
# =========================

class Ownership(BaseModel):
    """Asset ownership and visibility settings."""
    provider: OwnershipProvider = OwnershipProvider.SYSTEM
    visibility: Visibility = Visibility.SHARED
    requestable: bool = False


class Resources(BaseModel):
    """Resource requirements for scheduling and governance."""
    gpu_required: bool = False
    min_vram_gb: Optional[float] = None
    min_ram_gb: Optional[float] = None
    disk_gb: Optional[float] = None
    cold_start_sec: Optional[int] = None


class ContainerConfig(BaseModel):
    """Docker container configuration."""
    image: Optional[str] = None
    name: Optional[str] = None
    ports: Optional[List[str]] = None
    volumes: Optional[List[str]] = None


class InstallConfig(BaseModel):
    """One-time install or pull configuration."""
    command: Optional[str] = None
    once: bool = True


class Runtime(BaseModel):
    """Runtime execution configuration."""
    type: RuntimeType = RuntimeType.CONTAINER
    container: Optional[ContainerConfig] = None
    install: Optional[InstallConfig] = None


class Endpoints(BaseModel):
    """API endpoint configuration."""
    protocol: EndpointProtocol = EndpointProtocol.REST
    api_base: Optional[str] = None
    health: Optional[str] = None


class Lifecycle(BaseModel):
    """
    Asset lifecycle configuration.
    
    Note: `state` is Gateway-owned and read-only.
    Asset authors MUST NOT set `state` in asset.yaml.
    """
    desired: LifecycleDesired = LifecycleDesired.ON_DEMAND
    auto_sleep_min: Optional[int] = None
    state: Optional[LifecycleState] = None  # Gateway-owned, not authored


class Policy(BaseModel):
    """Usage policy and governance."""
    max_concurrency: Optional[int] = None
    allowed_apps: Optional[List[str]] = None
    
    # v1.0: Split model semantics
    required_models: Optional[List[str]] = None  # Models required by apps only
    served_models: Optional[List[str]] = None    # Models served by runtimes only
    
    # Legacy compatibility
    allowed_models: Optional[List[str]] = None
    allowed_embeddings: Optional[List[str]] = None
    
    defaults: Optional[Dict[str, Any]] = None


# =========================
# Main Asset Model
# =========================

class Asset(BaseModel):
    """
    Standard Asset Schema v1.0
    
    Represents any managed entity in ABS AI Fabric:
    services, models, tools, applications, datasets.
    """
    
    # Identity
    asset_id: str = Field(..., description="Unique identifier (required)")
    display_name: str = Field(..., description="Human-readable name")
    version: str = Field(default="1.0.0", description="Semantic version")
    
    # Contract
    interface: str = Field(..., description="Interface implemented (e.g., llm-runtime)")
    interface_version: str = Field(default="v1", description="Interface version")
    asset_class: AssetClass = Field(alias="class", description="Asset classification")
    
    description: Optional[str] = None
    
    # Pack Association (v1.0)
    pack_id: Optional[str] = Field(default=None, description="Asset Pack identifier")
    
    # Ownership
    ownership: Optional[Ownership] = None
    
    # Resources
    resources: Optional[Resources] = None
    
    # Runtime
    runtime: Optional[Runtime] = None
    
    # Endpoints
    endpoints: Optional[Endpoints] = None
    
    # Lifecycle
    lifecycle: Optional[Lifecycle] = None
    
    # Policy
    policy: Optional[Policy] = None
    
    # Metadata (free-form extension)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True  # Allow using 'class' as field name via alias
        extra = "allow"  # Allow additional fields for future compatibility
    
    # =========================
    # v1.0 Compliance Validators
    # =========================
    
    @model_validator(mode='after')
    def validate_v1_compliance(self):
        """Enforce v1.0 schema governance rules."""
        
        # Rule 1: lifecycle.state is Gateway-owned, MUST NOT be authored
        if self.lifecycle and self.lifecycle.state is not None:
            raise ValueError(
                "lifecycle.state is Gateway-owned and must not be set in asset.yaml. "
                "The Gateway will populate this field at runtime."
            )
        
        # Rule 2: metadata._status is Gateway-owned, MUST NOT be authored
        if self.metadata and "_status" in self.metadata:
            raise ValueError(
                "metadata._status is Gateway-owned and must not be set in asset.yaml. "
                "The Gateway will populate this field at runtime."
            )
        
        # Rule 3: Policy semantics enforcement
        if self.policy:
            # required_models applies ONLY to apps
            if self.asset_class != AssetClass.APP and self.policy.required_models:
                raise ValueError(
                    f"required_models is only valid for app assets, not {self.asset_class.value}"
                )
            
            # served_models applies ONLY to services/runtimes
            if self.asset_class == AssetClass.APP and self.policy.served_models:
                raise ValueError(
                    "served_models is not valid for app assets, use required_models instead"
                )
        
        return self


# =========================
# Helper Functions
# =========================

def validate_asset_yaml(data: Dict[str, Any]) -> Asset:
    """Validate a dictionary (parsed from YAML) as an Asset."""
    return Asset.model_validate(data)


def validate_asset_file(filepath: str) -> Asset:
    """Load and validate an asset.yaml file."""
    import yaml
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return validate_asset_yaml(data)


# =========================
# Specialized Asset Types
# =========================

class ServiceAsset(Asset):
    """Specialized model for service assets with required fields."""
    asset_class: AssetClass = Field(default=AssetClass.SERVICE, alias="class")
    runtime: Runtime
    endpoints: Endpoints


class AppAsset(Asset):
    """Specialized model for application assets."""
    asset_class: AssetClass = Field(default=AssetClass.APP, alias="class")
    policy: Policy  # Apps typically have policies


class ModelAsset(Asset):
    """Specialized model for LLM/ML model assets."""
    asset_class: AssetClass = Field(default=AssetClass.MODEL, alias="class")
    resources: Resources  # Models always have resource requirements
