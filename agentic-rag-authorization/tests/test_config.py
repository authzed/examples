"""Tests for config loading."""

import os
from unittest.mock import patch
from agentic_rag.config import Config


def test_config_loads_elasticsearch_url():
    env = {
        "ELASTICSEARCH_URL": "http://es-host:9200",
        "MISTRAL_API_KEY": "mstrl-test",
        "SPICEDB_TOKEN": "tok",
        "SPICEDB_ENDPOINT": "localhost:50051",
    }
    with patch.dict(os.environ, env, clear=True):
        config = Config.from_env()
    assert config.elasticsearch_url == "http://es-host:9200"


def test_config_loads_mistral_api_key():
    env = {
        "MISTRAL_API_KEY": "mstrl-test",
        "SPICEDB_TOKEN": "tok",
        "SPICEDB_ENDPOINT": "localhost:50051",
    }
    with patch.dict(os.environ, env, clear=True):
        config = Config.from_env()
    assert config.mistral_api_key == "mstrl-test"


def test_config_elasticsearch_defaults():
    env = {
        "MISTRAL_API_KEY": "mstrl-test",
        "SPICEDB_TOKEN": "tok",
        "SPICEDB_ENDPOINT": "localhost:50051",
    }
    with patch.dict(os.environ, env, clear=True):
        config = Config.from_env()
    assert config.elasticsearch_url == "http://localhost:9200"
    assert config.elasticsearch_api_key == ""
