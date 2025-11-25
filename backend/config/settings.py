import os
from dataclasses import dataclass, fields
from typing import Any, Dict, List, Mapping, Optional, Sequence


Env = Mapping[str, str]
_FALSE_VALUES = {"0", "false", "no"}


def _as_int(raw: Optional[str], default: int) -> int:
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _as_float(raw: Optional[str], default: float) -> float:
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


@dataclass
class AppConfig:
    SECRET_KEY: str = "change-me"
    SQLALCHEMY_DATABASE_URI: str = (
        "postgresql+psycopg2://rasa_user:rasa123@127.0.0.1:5432/rasa_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    RASA_BASE_URL: str = "http://localhost:5005"
    RASA_REST_WEBHOOK: str = "/webhooks/rest/webhook"
    RASA_PARSE_ENDPOINT: str = "/model/parse"
    RASA_TIMEOUT_SEND: float = 15.0
    RASA_TIMEOUT_PARSE: float = 10.0
    CHAT_CONTEXT_API_KEY: str = ""
    MAX_CONTENT_LENGTH: int = 1024 * 1024
    MAX_MESSAGE_LEN: int = 5000
    DATA_RETENTION_DAYS: int = 730
    METRICS_API_KEY: str = ""
    
    # MercadoPago configuration
    MERCADOPAGO_ACCESS_TOKEN: str = ""
    MERCADOPAGO_PUBLIC_KEY: str = ""
    MERCADOPAGO_NOTIFICATION_URL: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    @classmethod
    def from_env(cls, env: Optional[Env] = None) -> "AppConfig":
        env = os.environ if env is None else env
        return cls(
            SECRET_KEY=env.get("SECRET_KEY", cls.SECRET_KEY),
            SQLALCHEMY_DATABASE_URI=env.get(
                "SQLALCHEMY_DATABASE_URI", cls.SQLALCHEMY_DATABASE_URI
            ),
            RASA_BASE_URL=env.get("RASA_BASE_URL", cls.RASA_BASE_URL).rstrip("/"),
            RASA_REST_WEBHOOK=env.get(
                "RASA_REST_WEBHOOK", cls.RASA_REST_WEBHOOK
            ),
            RASA_PARSE_ENDPOINT=env.get(
                "RASA_PARSE_ENDPOINT", cls.RASA_PARSE_ENDPOINT
            ),
            RASA_TIMEOUT_SEND=_as_float(
                env.get("RASA_TIMEOUT_SEND"), cls.RASA_TIMEOUT_SEND
            ),
            RASA_TIMEOUT_PARSE=_as_float(
                env.get("RASA_TIMEOUT_PARSE"), cls.RASA_TIMEOUT_PARSE
            ),
            CHAT_CONTEXT_API_KEY=env.get(
                "CHAT_CONTEXT_API_KEY", cls.CHAT_CONTEXT_API_KEY
            ),
            MAX_CONTENT_LENGTH=_as_int(
                env.get("MAX_CONTENT_LENGTH"), cls.MAX_CONTENT_LENGTH
            ),
            MAX_MESSAGE_LEN=_as_int(
                env.get("MAX_MESSAGE_LEN"), cls.MAX_MESSAGE_LEN
            ),
            DATA_RETENTION_DAYS=_as_int(
                env.get("DATA_RETENTION_DAYS"), cls.DATA_RETENTION_DAYS
            ),
            METRICS_API_KEY=env.get("METRICS_API_KEY", cls.METRICS_API_KEY),
            MERCADOPAGO_ACCESS_TOKEN=env.get(
                "MERCADOPAGO_ACCESS_TOKEN", cls.MERCADOPAGO_ACCESS_TOKEN
            ),
            MERCADOPAGO_PUBLIC_KEY=env.get(
                "MERCADOPAGO_PUBLIC_KEY", cls.MERCADOPAGO_PUBLIC_KEY
            ),
            MERCADOPAGO_NOTIFICATION_URL=env.get(
                "MERCADOPAGO_NOTIFICATION_URL", cls.MERCADOPAGO_NOTIFICATION_URL
            ),
            FRONTEND_URL=env.get("FRONTEND_URL", cls.FRONTEND_URL),
        )

    def to_mapping(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


def load_app_config(env: Optional[Env] = None) -> AppConfig:
    return AppConfig.from_env(env)


@dataclass(frozen=True)
class JsonConfig:
    ensure_ascii: bool = False
    sort_keys: bool = False


def build_json_config() -> JsonConfig:
    return JsonConfig()


@dataclass(frozen=True)
class CorsConfig:
    origins: List[str]
    supports_credentials: bool
    warning: Optional[str] = None

    @property
    def wildcard(self) -> bool:
        return self.origins == ["*"]

    def to_kwargs(self) -> Dict[str, Any]:
        origins = "*" if self.wildcard else self.origins
        resources = {r"/*": {"origins": origins}}
        return {
            "supports_credentials": self.supports_credentials,
            "resources": resources,
        }


def _parse_cors_origins(raw: str) -> List[str]:
    if not raw.strip():
        return []
    if raw.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def build_cors_config(env: Optional[Env] = None) -> CorsConfig:
    env = os.environ if env is None else env
    raw_origins = env.get("CORS_ORIGINS", "http://localhost:3000")
    supports_credentials = (
        env.get("CORS_SUPPORTS_CREDENTIALS", "true").lower() not in _FALSE_VALUES
    )

    parsed_origins = _parse_cors_origins(raw_origins)
    if not parsed_origins:
        parsed_origins = ["http://localhost:3000"]

    warning = None
    if parsed_origins == ["*"] and supports_credentials:
        warning = (
            "CORS con supports_credentials=True y origins='*' no es valido en navegadores. "
            "Define CORS_ORIGINS con una lista de origenes explicitos en produccion. "
            "Se deshabilita supports_credentials para continuar."
        )
        supports_credentials = False

    return CorsConfig(origins=parsed_origins, supports_credentials=supports_credentials, warning=warning)


@dataclass(frozen=True)
class RateLimitConfig:
    default_limits: Sequence[str]
    storage_uri: Optional[str]
    strategy: Optional[str]

    def to_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "default_limits": tuple(self.default_limits),
            "storage_uri": self.storage_uri or "memory://",
        }
        if self.strategy:
            kwargs["strategy"] = self.strategy
        return kwargs

    @property
    def uses_memory_storage(self) -> bool:
        return not self.storage_uri


def build_rate_limit_config(env: Optional[Env] = None) -> RateLimitConfig:
    env = os.environ if env is None else env
    default_limit = env.get("RATE_LIMIT_DEFAULT", "60/minute") or "60/minute"
    storage_uri = env.get("RATELIMIT_STORAGE_URI") or None
    strategy = env.get("RATELIMIT_STRATEGY") or None
    return RateLimitConfig(
        default_limits=(default_limit,),
        storage_uri=storage_uri,
        strategy=strategy,
    )
