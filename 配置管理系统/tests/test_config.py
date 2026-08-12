"""测试：配置管理系统（三套配置加载 / 热切换 / ${ENV} 注入 / 优先级）。"""
import pytest

from src.config import CONFIG_DIR, Config, ConfigManager, normalize_env


# ---------------- 三套配置均可加载 ----------------
@pytest.mark.parametrize("env", ["dev", "prod", "test"])
def test_load_three_envs(env):
    manager = ConfigManager(env)
    cfg = manager.current()
    assert cfg.env == env
    assert cfg.get("app.name") == "my-agent"
    assert cfg.get("app.max_steps") is not None


def test_envs_differ():
    """三套环境关键配置互不相同：模拟 vs 真实数据源。"""
    dev = ConfigManager("dev").current()
    prod = ConfigManager("prod").current()
    test = ConfigManager("test").current()
    assert dev.get("weather.provider") == "mock"
    assert prod.get("weather.provider") == "wttr"
    assert test.get("weather.provider") == "mock"
    # 缓存文件隔离：prod 与 test 不同
    assert prod.get("weather.cache_file") != test.get("weather.cache_file")


def test_default_env_is_dev(monkeypatch):
    monkeypatch.delenv("MY_AGENT_ENV", raising=False)
    manager = ConfigManager()
    assert manager.env == "dev"


def test_env_var_selects_env(monkeypatch):
    monkeypatch.setenv("MY_AGENT_ENV", "test")
    manager = ConfigManager()
    assert manager.env == "test"


def test_env_alias_normalize():
    assert normalize_env("production") == "prod"
    assert normalize_env("development") == "dev"


def test_missing_config_file_raises():
    with pytest.raises(FileNotFoundError):
        ConfigManager("不存在的环境")


# ---------------- 无硬编码敏感信息 ----------------
def test_configs_have_no_hardcoded_secret():
    """配置文件只允许 ${ENV} 占位符，不应出现明文密钥。"""
    for env in ("dev", "prod", "test"):
        raw = (CONFIG_DIR / f"{env}.yaml").read_text(encoding="utf-8")
        assert "${LLM_API_KEY}" in raw
        assert "secret" not in raw.lower()
        assert "123456" not in raw


def test_env_placeholder_resolved(monkeypatch):
    """${LLM_API_KEY} 应解析为环境变量的值。"""
    monkeypatch.setenv("LLM_API_KEY", "sk-test-value")
    manager = ConfigManager("dev")
    cfg = manager.switch_env("dev")  # 重新加载，触发占位符解析
    assert cfg.get("llm.api_key") == "sk-test-value"


def test_env_placeholder_none_when_unset(monkeypatch):
    """环境变量未设置时返回 None（优雅降级），而不是硬编码假密钥。"""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    manager = ConfigManager("dev")
    cfg = manager.switch_env("dev")
    assert cfg.get("llm.api_key") is None


# ---------------- 热切换 ----------------
def test_hot_switch_between_envs():
    manager = ConfigManager("dev")
    assert manager.current().env == "dev"

    cfg_prod = manager.switch_env("prod")  # 热切换：立即生效
    assert cfg_prod.env == "prod"
    assert manager.current().env == "prod"

    manager.switch_env("test")
    assert manager.current().get("knowledge.store_path") == "data/knowledge_test.json"


def test_get_config_switches_global(monkeypatch):
    """get_config(env) 即热切换全局单例。"""
    monkeypatch.setenv("MY_AGENT_ENV", "dev")
    from src.config import get_config

    assert get_config("dev").env == "dev"
    assert get_config("prod").env == "prod"
    get_config("dev")  # 切回，避免影响其他测试


# ---------------- 点号路径读取与优先级 ----------------
def test_config_dotted_get_with_default():
    cfg = Config("test", {"a": {"b": {"c": 42}}})
    assert cfg.get("a.b.c") == 42
    assert cfg.get("a.b.not_exist", "fallback") == "fallback"


def test_cli_env_overrides_default():
    """优先级演示：显式传参(模拟 CLI) > 环境变量 > 默认值。"""
    manager = ConfigManager("prod")  # 显式传参优先
    assert manager.env == "prod"
