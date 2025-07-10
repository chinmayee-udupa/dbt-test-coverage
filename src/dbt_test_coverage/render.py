import os
from typing import Dict, Optional

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class CoverageRenderer:
    """Handles rendering coverage reports with Rich."""

    def __init__(self, verbose: bool = False):
        self.console = console
        self.verbose = verbose

    def display_combined_report(
        self,
        package: str,
        unit_test_stats: Dict,
        contract_stats: Dict,
        model_details: Dict,
        filters: Optional[Dict] = None,
        show_column_details: bool = False,
    ):
        """Render report with filter information"""
        inner_width = int(console.width * 0.7)
        # inner_width = min(80, self.console.width)

        console.print(
            Panel(
                border_style="bold violet",
                width=inner_width,
                renderable=Text(
                    f'📈 DBT test coverage report for "{package}" package', justify="center"
                ),
            )
        )

        if filters:
            filter_lines = []

            if filters.get("model_names"):
                filter_lines.append(f"Model names: {', '.join(filters['model_names'])}")
            if filters.get("model_paths"):
                filter_lines.append(f"Paths: {', '.join(filters['model_paths'])}")
            if filters.get("has_tags"):
                filter_lines.append(f"Must have tags: {', '.join(filters['has_tags'])}")
            if filters.get("any_tags"):
                filter_lines.append(f"Any of tags: {', '.join(filters['any_tags'])}")
            if filters.get("exclude_tags"):
                filter_lines.append(f"Excluded tags: {', '.join(filters['exclude_tags'])}")
            if filters.get("modified_after"):
                filter_lines.append(f"Modified after: {filters['modified_after']}")
            if filters.get("test_type"):
                filter_lines.append(f"Test type: {filters['test_type']}")

            if filter_lines:
                console.print(
                    Panel(
                        "\n".join(filter_lines),
                        title="[bold blue]Active Filters[/bold blue]",
                        border_style="blue",
                        width=inner_width,
                    )
                )

        # Summary Panels
        self._display_summary_panels(unit_test_stats, contract_stats, model_details, inner_width)

        # Detailed column view if requested
        if show_column_details:
            self.display_column_test_report(model_details)

        # Model table
        self._display_model_table(model_details, inner_width)

        # Contract issues if any
        if contract_stats["contract_issues"]:
            self._display_contract_issues(contract_stats)

    def display_column_test_report(self, model_details: Dict):
        """Render detailed column test coverage by model."""
        self.console.print(
            Panel.fit(
                "[bold yellow]Detailed Column Test Coverage by Model[/bold yellow]",
                border_style="yellow",
            )
        )

        for model_name, details in sorted(model_details.items()):
            if details["total_columns"] == 0:
                continue

            path = os.path.basename(details["path"])
            self.console.print(
                Panel.fit(
                    f"[bold]{model_name}[/bold] [dim]({path})[/dim]",
                    subtitle=f"Coverage: {details['coverage_pct']:.1f}%",
                    subtitle_align="right",
                )
            )

            table = Table(box=box.SIMPLE, show_header=True)
            table.add_column("Column", style="cyan")
            table.add_column("Tested", justify="center")

            for col, tested in details["columns_test"].items():
                table.add_row(col, "✅" if tested else "❌")

            self.console.print(table)
            self.console.print()

    def _display_summary_panels(self, unit_test_stats, contract_stats, model_details, width):
        """Display summary panels for each coverage type."""
        # Column Test Summary
        total_models = len(model_details)
        models_with_column_tests = sum(
            1 for m in model_details.values() if m["tested_columns"] > 0
        )
        avg_column_coverage = (
            sum(m["coverage_pct"] for m in model_details.values()) / total_models
            if total_models
            else 0
        )

        column_test_panel = Align.center(
            Panel(
                f"[bold yellow]Column-Level Test Coverage[/bold yellow]\n"
                f"[green]✓ Models with column tests:[/green] {models_with_column_tests}/{total_models}\n"
                f"[cyan]📊 Average column coverage:[/cyan] {avg_column_coverage:.1f}%",
                title="[bold]Column Test Status[/bold]",
                width=width,
            )
        )

        # Unit Test Summary
        unit_test_coverage = (
            unit_test_stats["models_with_unit_tests"] / unit_test_stats["total_models"] * 100
            if unit_test_stats["total_models"]
            else 0
        )

        unit_test_panel = Align.center(
            Panel(
                f"[bold yellow]Unit Test Coverage[/bold yellow]\n"
                f"[green]✓ Models with unit tests:[/green] {unit_test_stats['models_with_unit_tests']}/{unit_test_stats['total_models']}\n"
                f"[cyan]📊 Coverage:[/cyan] {unit_test_coverage:.1f}%",
                title="[bold]Unit Test Status[/bold]",
                width=width,
            )
        )

        # Contract Summary
        total_contract_models = (
            contract_stats["with_contracts"] + contract_stats["without_contracts"]
        )
        contract_coverage = (
            contract_stats["with_contracts"] / total_contract_models * 100
            if total_contract_models
            else 0
        )

        contract_panel = Align.center(
            Panel(
                f"[bold yellow]Model Contracts Analysis[/bold yellow]\n"
                f"[green]✓ Models with contracts:[/green] {contract_stats['with_contracts']}\n"
                f"[red]✗ Models without contracts:[/red] {contract_stats['without_contracts']}\n"
                f"[cyan]📊 Coverage:[/cyan] {contract_coverage:.1f}%",
                title="[bold]Contract Status[/bold]",
                width=width,
            )
        )

        # Display panels in a group
        inner_group = Group(column_test_panel, unit_test_panel, contract_panel)
        align_box = Align.left(inner_group)
        outer_panel = Panel.fit(
            align_box,
            title="[bold magenta]DBT Test Coverage Summary[/bold magenta]",
            padding=1,
            width=width,
        )
        self.console.print(Align.left(outer_panel))
        self.console.print()

    def _display_model_table(self, model_details: Dict, width: int):
        """Display the model summary table."""
        table = Table(
            title="🔍 Model-Level Summary (with coverage percentages)",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold blue",
            width=width,
        )
        table.add_column("Model")
        table.add_column("Unit Tests", justify="center")
        table.add_column("Column Tests", justify="center")
        table.add_column("Contract", justify="center")

        for name, details in sorted(model_details.items()):
            # Unit test cell
            unit_text = Text(f"{details['unit_tests']} ({details['unit_test_pct']:.0f}%)")
            unit_text.style = "green" if details["unit_tests"] else "red"

            # Column test cell
            col_text = Text(
                f"{details['tested_columns']}/{details['total_columns']} ({details['coverage_pct']:.1f}%)"
            )
            col_text.style = (
                "green"
                if details["coverage_pct"] > 80
                else "yellow" if details["coverage_pct"] > 50 else "red"
            )

            # Contract cell
            contract_icon = "✅" if details["has_contract"] else "❌"
            contract_text = Text(contract_icon)
            contract_text.style = "green" if details["has_contract"] else "red"

            table.add_row(name, unit_text, col_text, contract_text)

        # self.console.print(Panel(Align.center(table), border_style="blue"))
        self.console.print(
            Panel(
                Align.center(table),
                title="[bold magenta]DBT Model Coverage Table[/bold magenta]",
                padding=(1, 2),
                border_style="magenta",
                box=box.ROUNDED,
                width=width,
            )
        )

    def _display_contract_issues(self, contract_stats: Dict):
        """Display contract issues if any exist."""
        self.console.print(
            Panel.fit("[bold red]Contract Issues Found[/bold red]", border_style="red")
        )

        for issue in contract_stats["contract_issues"]:
            self.console.print(f"[bold]{issue['model']}[/bold]")
            for item in issue["issues"]:
                self.console.print(f"  - {item}")
