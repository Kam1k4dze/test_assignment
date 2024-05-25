import yaml


def load_config():
    try:
        with open("config.yaml", 'r') as stream:
            config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        return None
    return config


config = load_config()

if config is None:
    raise ValueError("Failed to load configuration. Please check your config.yaml file.")

try:
    DB_USER = config['database']['DB_USER']
    DB_PASSWORD = config['database']['DB_PASSWORD']
    DB_HOST = config['database']['DB_HOST']
    DB_NAME = config['database']['DB_NAME']
    DB_PORT = config['database']['DB_PORT']
    NAME_MAX_LENGTH = config['models']['NAME_MAX_LENGTH']
    REDIS_URL = config['cache']['REDIS_URL']
    CACHE_TTL = config['cache']['CACHE_TTL']
except KeyError as e:
    raise ValueError(f"Missing configuration key: {e}")
