import json
from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, Sequence, Tuple

from dbt.contracts.graph.manifest import Manifest
from dbt.exceptions import DbtRuntimeError
from rich.progress import Progress

from .exceptions import InvalidManifestError, ManifestNotFoundError


def analyze_unit_tests_and_contracts(
    manifest_path: str,
    package_name: str,
    model_names: Sequence[str] = (),
    model_paths: Sequence[str] = (),
    has_tags: Sequence[str] = (),
    any_tag: bool = False,
    exclude_tags: Sequence[str] = (),
    test_type: str = "all",
) -> Tuple[Dict, Dict, Dict]:
    """Analyze coverage with advanced filtering"""
    manifest = _load_manifest(manifest_path)

    with Progress() as progress:
        task = progress.add_task("[cyan]Analyzing models...", total=len(manifest.nodes))
        filtered_nodes = []
        unit_test_stats = {"total_models": 0, "models_with_unit_tests": 0}
        contract_stats = {"with_contracts": 0, "without_contracts": 0, "contract_issues": []}
        model_details = {}
        column_stats = defaultdict(lambda: {"tested": 0, "total": 0})

        for node in manifest.nodes.values():
            progress.update(task, advance=1)
            if not _passes_filters(
                node=node,
                model_names=model_names,
                model_paths=model_paths,
                has_tags=has_tags,
                any_tag=any_tag,
                exclude_tags=exclude_tags,
                test_type=test_type,
            ):
                continue
            else:
                filtered_nodes.append(node)
        manifest = _load_manifest(manifest_path)

        for node in filtered_nodes:
            if (
                node.resource_type == "model"
                and node.package_name == package_name
                and node.config.get("materialized") != "ephemeral"
            ):

                columns = node.columns.keys() if hasattr(node, "columns") else []

                # Unit test analysis
                unit_tests = [
                    test
                    for test in manifest.unit_tests.values()
                    if (test.model == node.name) and test.package_name == package_name
                ]

                # Contract analysis
                has_contract = hasattr(node, "contract") and node.contract is not None
                contract_enforced = has_contract and getattr(node.contract, "enforced", False)
                contract_issues = []

                if has_contract and not contract_enforced:
                    contract_issues.append("Contract not enforced")

                model_details[node.name] = {
                    "path": node.original_file_path,
                    "unit_tests": len(unit_tests),
                    "has_contract": contract_enforced,
                    "contract_enforced": contract_enforced,
                    "contract_issues": contract_issues,
                    "columns": list(node.columns.keys()) if hasattr(node, "columns") else [],
                    "columns_test": {col: False for col in columns},
                    "total_columns": len(columns),
                    "tested_columns": 0,
                    "coverage_pct": 0.0,
                    "unit_test_pct": 100.0 if unit_tests else 0.0,
                }

                # Update stats
                unit_test_stats["total_models"] += 1
                if unit_tests:
                    unit_test_stats["models_with_unit_tests"] += 1

                if contract_enforced:
                    contract_stats["with_contracts"] += 1
                    if contract_issues:
                        contract_stats["contract_issues"].append(
                            {"model": node.name, "issues": contract_issues}
                        )
                else:
                    contract_stats["without_contracts"] += 1

    # Second pass: identify tested columns
    _analyze_column_tests(manifest, model_details)

    # Calculate coverage stats
    _calculate_coverage_stats(model_details, column_stats)

    return dict(unit_test_stats), contract_stats, model_details


def _passes_filters(
    node,
    model_names: Sequence[str] = (),
    model_paths: Sequence[str] = (),
    has_tags: Sequence[str] = (),
    any_tag: bool = False,
    exclude_tags: Sequence[str] = (),
    test_type: str = "all",
) -> bool:
    """Determine if a node passes all specified filters.

    Args:
        node: The dbt node to check (model or test)
        model_names: Sequence of model name patterns to include (supports wildcards)
        model_paths: Sequence of file path patterns to include (supports wildcards)
        has_tags: Sequence of tags the model must have ALL of
        include_tags_mode: 'ALL' or 'ANY' for how to handle has_tags
        exclude_tags: Sequence of tags to exclude
        test_type: Filter for test type ('singular', 'generic', or 'all')
        materialized_types: Sequence of materialization types to include
        modified_after: Only include models modified after this date

    Returns:
        bool: True if node passes all filters, False otherwise
    """
    # Model name filter (supports wildcards)
    if model_names and not any(fnmatch(node.name, pattern) for pattern in model_names):
        return False

    # Model path filter (supports wildcards)
    if model_paths and not any(
        fnmatch(node.original_file_path, pattern) for pattern in model_paths
    ):
        return False

    # Tag filtering
    node_tags = set(getattr(node, "tags", []))

    # Include tags logic
    if has_tags:
        if any_tag:
            if not set(has_tags).intersection(node_tags):
                return False
        else:  # ANY mode
            if not set(has_tags).issubset(node_tags):
                return False

    # Must NOT have these tags
    if exclude_tags and set(exclude_tags).intersection(node_tags):
        return False

    # Test type filtering
    if getattr(node, "resource_type", None) == "test" and test_type != "all":
        is_generic_test = hasattr(node, "test_metadata")
        if test_type == "singular" and is_generic_test:
            return False
        if test_type == "generic" and not is_generic_test:
            return False
    return True


def _load_manifest(manifest_path: str) -> Manifest:
    """Load and validate manifest file."""
    path = Path(manifest_path)
    if not path.exists():
        raise ManifestNotFoundError(f"Manifest not found: {manifest_path}")

    try:
        with open(path, "r") as f:
            return Manifest.from_dict(json.load(f))
    except json.JSONDecodeError as e:
        raise InvalidManifestError(f"Invalid JSON in manifest: {str(e)}")
    except DbtRuntimeError as e:
        raise InvalidManifestError(f"Failed to parse manifest: {str(e)}")


def _analyze_column_tests(manifest: Manifest, model_details: Dict):
    """Analyze column-level tests."""
    for test_node in manifest.nodes.values():
        if test_node.resource_type == "test":
            for model_id in test_node.depends_on.nodes:
                model_node = manifest.nodes.get(model_id)
                if model_node and model_node.name in model_details:
                    if hasattr(test_node, "column_name") and test_node.column_name:
                        if test_node.column_name in model_details[model_node.name]["columns_test"]:
                            model_details[model_node.name]["columns_test"][
                                test_node.column_name
                            ] = True
                    elif hasattr(test_node, "test_metadata") and test_node.test_metadata:
                        if "column" in test_node.test_metadata.kwargs:
                            col = test_node.test_metadata.kwargs["column"]
                            if col in model_details[model_node.name]["columns_test"]:
                                model_details[model_node.name]["columns_test"][col] = True


def _calculate_coverage_stats(model_details: Dict, column_stats: Dict):
    """Calculate coverage percentages."""
    for model in model_details.values():
        model["tested_columns"] = sum(1 for tested in model["columns_test"].values() if tested)
        model["coverage_pct"] = (
            model["tested_columns"] / model["total_columns"] * 100
            if model["total_columns"] > 0
            else 0.0
        )

        for col, tested in model["columns_test"].items():
            column_stats[col]["total"] += 1
            if tested:
                column_stats[col]["tested"] += 1
