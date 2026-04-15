from pathlib import Path


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
        "src/domain_models/settings.py",
        "src/domain_models/resilience.py",
        "src/domain_models/farm_task.py",
        "src/domain_models/user_status.py",
        "src/engines/leveling.py",
    ]:
        content = Path(relative).read_text()
        assert "habiticalib" not in content
        assert "aiohttp" not in content
        assert "loguru" not in content


def test_no_inner_layer_imports_delivery():
    for relative in [
        "src/domain_models/settings.py",
        "src/domain_models/resilience.py",
        "src/domain_models/farm_task.py",
        "src/domain_models/user_status.py",
        "src/engines/leveling.py",
        "src/services/levelup_service.py",
        "src/integrations/session.py",
        "src/integrations/retry.py",
        "src/integrations/habitica_gateway.py",
    ]:
        content = Path(relative).read_text()
        assert "src.delivery" not in content
