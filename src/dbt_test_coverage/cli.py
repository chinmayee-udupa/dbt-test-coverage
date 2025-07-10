import json
import sys
from pathlib import Path
from typing import Optional, Tuple

import click
from rich.console import Console

from .coverage import (
    InvalidManifestError,
    ManifestNotFoundError,
    analyze_unit_tests_and_contracts,
)
from .render import CoverageRenderer

console = Console()


@click.command()
@click.option("--manifest-file", default=None, help="Path to manifest.json")
@click.option("--package", required=True, help="Your dbt package name")
# Model filters
@click.option("--model-name", multiple=True, help="Filter models by name (supports wildcards)")
@click.option("--model-path", multiple=True, help="Filter by model path (supports wildcards)")
# Tag filters
@click.option(
    "--has-tags",
    help="""Comma-separated list of required tags 'gold,smb'""",
    callback=lambda ctx, param, value: value.split(",") if value else [],
)
@click.option(
    "--any-tag",
    is_flag=True,
    help="Change --has-tags behavior to match ANY instead of ALL match (default is ALL if flag not set)",
)
@click.option(
    "--exclude-tag",
    help="""Comma-separated list of required tags 'cicd,sandbox,test_only'""",
    callback=lambda ctx, param, value: value.split(",") if value else [],
)
# Test filters
@click.option(
    "--test-type",
    type=click.Choice(["singular", "generic", "all"]),
    default="all",
    help="Filter by test type",
)
@click.option("--unit-test-threshold", type=float, default=0, help="Unit test coverage threshold")
@click.option(
    "--column-test-threshold", type=float, default=0, help="Column test coverage threshold"
)
@click.option("--contract-threshold", type=float, default=0, help="Contract coverage threshold")
@click.option("--show-column-details", is_flag=True, help="Show detailed column coverage")
@click.option("--json-out", help="Output JSON report to file")
def main(
    manifest_file: Optional[str],
    package: str,
    unit_test_threshold: float,
    column_test_threshold: float,
    contract_threshold: float,
    show_column_details: bool,
    json_out: Optional[str],
    model_name: Tuple[str],
    model_path: Tuple[str],
    has_tags: Tuple[str],
    any_tag: bool,
    exclude_tag: Tuple[str],
    test_type: str,
):
    """Analyze test coverage in dbt projects."""
    try:
        manifest_path = manifest_file or _find_manifest()
        if not manifest_path:
            raise ManifestNotFoundError(
                "Could not find manifest.json automatically. " "Please specify with --manifest"
            )

        # Create filters dictionary
        filters = {
            "model_names": model_name,
            "model_paths": model_path,
            "has_tags": has_tags,
            "any_tag": any_tag,
            "exclude_tags": exclude_tag,
            "test_type": test_type,
        }

        renderer = CoverageRenderer()
        unit_stats, contract_stats, model_details = analyze_unit_tests_and_contracts(
            manifest_path,
            package,
            model_name,
            model_path,
            has_tags,
            any_tag,
            exclude_tag,
            test_type,
        )

        renderer.display_combined_report(
            package, unit_stats, contract_stats, model_details, filters, show_column_details
        )

        if json_out:
            _save_json_report(json_out, package, unit_stats, contract_stats, model_details)

        exit_code = _check_thresholds(
            unit_stats,
            contract_stats,
            model_details,
            unit_test_threshold,
            column_test_threshold,
            contract_threshold,
        )
        sys.exit(exit_code)

    except (ManifestNotFoundError, InvalidManifestError) as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)


def _find_manifest() -> Optional[str]:
    """Automatically locate manifest.json in common locations."""
    search_paths = [
        "target/manifest.json",
        "../target/manifest.json",
        "../../target/manifest.json",
    ]
    for path in search_paths:
        if Path(path).exists():
            return path
    return None


def _save_json_report(
    path: str, package: str, unit_stats: dict, contract_stats: dict, model_details: dict
):
    """Save the report data to a JSON file."""
    output = {
        "package": package,
        "unit_test_stats": unit_stats,
        "contract_stats": contract_stats,
        "model_details": model_details,
    }
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    console.print(f"\n📄 JSON report written to {path}")


def _check_thresholds(
    unit_stats: dict,
    contract_stats: dict,
    model_details: dict,
    unit_thresh: float,
    col_thresh: float,
    contract_thresh: float,
) -> int:
    """Check coverage against thresholds and return exit code."""
    exit_code = 0

    # Calculate coverages
    unit_cov = (
        unit_stats["models_with_unit_tests"] / unit_stats["total_models"] * 100
        if unit_stats["total_models"]
        else 0
    )

    contract_cov = (
        contract_stats["with_contracts"]
        / (contract_stats["with_contracts"] + contract_stats["without_contracts"])
        * 100
        if (contract_stats["with_contracts"] + contract_stats["without_contracts"])
        else 0
    )

    avg_col_cov = (
        sum(m["coverage_pct"] for m in model_details.values()) / len(model_details)
        if model_details
        else 0
    )

    # Check thresholds
    if unit_thresh > 0 and unit_cov < unit_thresh:
        console.print(
            f"\n[bold red]❌ Unit test coverage {unit_cov:.1f}% "
            f"below threshold {unit_thresh}%[/bold red]"
        )
        exit_code = 1

    if col_thresh > 0 and avg_col_cov < col_thresh:
        console.print(
            f"\n[bold red]❌ Column test coverage {avg_col_cov:.1f}% "
            f"below threshold {col_thresh}%[/bold red]"
        )
        exit_code = 1

    if contract_thresh > 0 and contract_cov < contract_thresh:
        console.print(
            f"\n[bold red]❌ Contract coverage {contract_cov:.1f}% "
            f"below threshold {contract_thresh}%[/bold red]"
        )
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    main()
