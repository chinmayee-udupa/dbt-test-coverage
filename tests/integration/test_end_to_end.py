import json
import subprocess
from pathlib import Path


def test_manifest_generation_and_coverage():
    project_dir = Path(__file__).parent / "jaffle_shop"
    profiles_dir = Path(__file__).parent / "profiles"

    result = subprocess.run(
        ["dbt", "compile", "--project-dir", str(project_dir), "--profiles-dir", str(profiles_dir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    manifest_path = project_dir / "target" / "manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text())
    assert "nodes" in manifest
    assert any("model" in k for k in manifest["nodes"])
