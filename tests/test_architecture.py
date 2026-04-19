import ast
from pathlib import Path

LAYER_PATHS = {
    "delivery": Path("src/delivery"),
    "services": Path("src/services"),
    "integrations": Path("src/integrations"),
    "engines": Path("src/engines"),
    "domain_models": Path("src/domain_models"),
}

ALLOWED_IMPORTS = {
    "delivery": {"delivery", "services", "integrations", "engines", "domain_models"},
    "services": {"services", "integrations", "engines", "domain_models"},
    "integrations": {"integrations", "domain_models"},
    "engines": {"engines", "domain_models"},
    "domain_models": {"domain_models"},
}


def _python_files(path: Path) -> list[Path]:
    return [file for file in path.rglob("*.py") if "__pycache__" not in file.parts]


def _layer_for_path(path: Path) -> str | None:
    for layer, layer_path in LAYER_PATHS.items():
        if layer_path in path.parents or path == layer_path:
            return layer
    return None


def _imported_layers(path: Path) -> set[str]:
    imported_layers: set[str] = set()
    tree = ast.parse(path.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            if not node.module.startswith("src."):
                continue
            parts = node.module.split(".")
            if len(parts) >= 2 and parts[1] in LAYER_PATHS:
                imported_layers.add(parts[1])

        if isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.name.startswith("src."):
                    continue
                parts = alias.name.split(".")
                if len(parts) >= 2 and parts[1] in LAYER_PATHS:
                    imported_layers.add(parts[1])

    return imported_layers


def test_masa_directories_exist():
    root = Path("src")
    assert (root / "domain_models").is_dir()
    assert (root / "engines").is_dir()
    assert (root / "services").is_dir()
    assert (root / "integrations").is_dir()
    assert (root / "delivery").is_dir()


def test_legacy_flat_modules_removed():
    root = Path("src")
    assert not (root / "bot.py").exists()
    assert not (root / "core.py").exists()
    assert not (root / "tasks.py").exists()
    assert not (root / "infrastructure.py").exists()
    assert not (root / "config.py").exists()
    assert not (root / "logging_config.py").exists()


def test_domain_and_engine_layers_do_not_import_infrastructure_packages():
    for relative in [
        "src/domain_models/farm_task.py",
        "src/domain_models/party_quest_status.py",
        "src/domain_models/user_status.py",
        "src/engines/leveling.py",
    ]:
        content = Path(relative).read_text()
        assert "habiticalib" not in content
        assert "aiohttp" not in content
        assert "loguru" not in content
        assert "pydantic" not in content
        assert "dotenv" not in content


def test_layer_import_directions_follow_masa():
    for layer, layer_path in LAYER_PATHS.items():
        for path in _python_files(layer_path):
            imported_layers = _imported_layers(path)
            disallowed = imported_layers - ALLOWED_IMPORTS[layer]
            assert not disallowed, f"{path} imports disallowed layers: {sorted(disallowed)}"


def test_domain_models_remain_pure():
    for path in _python_files(Path("src/domain_models")):
        imported_layers = _imported_layers(path)
        assert imported_layers <= {"domain_models"}, (
            f"{path} imports non-domain layers: {sorted(imported_layers)}"
        )


def test_delivery_settings_and_service_resilience_own_framework_concerns():
    assert Path("src/delivery/settings.py").is_file()
    assert Path("src/services/resilience.py").is_file()
    assert Path("src/integrations/retry_policy.py").is_file()
    assert not Path("src/domain_models/settings.py").exists()
    assert not Path("src/domain_models/resilience.py").exists()
