from environs import Env
from dataclasses import dataclass

BOT_USERNAME = "vistly_bot"


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: int = 5432


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]


@dataclass
class OmdbConfig:
    api_key: str


@dataclass
class KpConfig:
    api_key: str


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    omdb: OmdbConfig
    kp: KpConfig


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"), admin_ids=list(map(int, env.list("ADMINS")))
        ),
        db=DbConfig(
            host=env.str("DB_HOST"),
            password=env.str("DB_PASS"),
            user=env.str("DB_USER"),
            database=env.str("DB_NAME"),
            port=env.int("DB_PORT", 5432),
        ),
        omdb=OmdbConfig(api_key=env.str("OMDB_API_KEY")),
        kp=KpConfig(api_key=env.str("KP_API_KEY")),
    )
