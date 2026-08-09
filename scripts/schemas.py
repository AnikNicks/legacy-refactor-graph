"""Pydantic contracts every phase's output/*.json must satisfy.

Referenced by scripts/validate_state.py's `validate` subcommand — never imported
directly by an agent; agents just write JSON matching these shapes.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ModuleInventoryEntry(BaseModel):
    name: str
    path: str
    loc: int
    churn_commits: int = Field(description="commits touching this module, from git log --stat")
    description: str


class EntryPoint(BaseModel):
    module: str
    path: str
    kind: str
    description: str


class CouplingNote(BaseModel):
    from_module: str
    to_module: str
    description: str
    evidence: str


class SchemaTable(BaseModel):
    name: str
    columns: list[str]
    foreign_keys: list[str] = []


class ArchaeologyReport(BaseModel):
    target: str
    modules: list[ModuleInventoryEntry]
    entry_points: list[EntryPoint]
    schema_tables: list[SchemaTable] = []
    coupling_notes: list[CouplingNote] = []
    deep_dive_notes: list[str] = []


class ModuleRiskScore(BaseModel):
    module: str
    churn_score: float
    complexity_score: float
    coupling_score: float
    security_score: float
    total_score: float
    rationale: str


class RiskAssessment(BaseModel):
    target: str
    ranked_modules: list[ModuleRiskScore]
    findings: list[str] = []


class Stage(BaseModel):
    id: int
    module: str
    description: str
    target_files: list[str]
    pattern: Literal["strangler-fig", "branch-by-abstraction", "direct", "contract-test-only"]
    risk_level: Literal["low", "medium", "high"]
    acceptance_criteria: list[str]
    depends_on: list[int] = []


class RefactorPlan(BaseModel):
    target: str
    stages: list[Stage]


class StageResult(BaseModel):
    stage_id: int
    status: Literal["approved", "modified", "rejected", "failed"]
    tests_passed: bool
    summary: str
    commit_sha: Optional[str] = None
