"""Tests for config loading."""

import os
from unittest.mock import patch
from agentic_rag.config import Config


def test_config_loads_milvus_uri():
    env = {
        "MILVUS_URI": "http://milvus-host:19530",
        "OPENAI_API_KEY": "sk-test",
        "SPICEDB_TOKEN": "tok",
        "SPICEDB_ENDPOINT": "localhost:50051",
    }
    with patch.dict(os.environ, env, clear=True):
        config = Config.from_env()
    assert config.milvus_uri == "http://milvus-host:19530"


def test_config_milvus_defaults():
    env = {
        "OPENAI_API_KEY": "sk-test",
        "SPICEDB_TOKEN": "tok",
        "SPICEDB_ENDPOINT": "localhost:50051",
    }
    with patch.dict(os.environ, env, clear=True):
        config = Config.from_env()
    assert config.milvus_uri == "http://localhost:19530"
    assert config.milvus_token == ""


def test_config_has_no_weaviate_fields():
    config = Config.from_env()
    assert not hasattr(config, "weaviate_url")
    assert not hasattr(config, "weaviate_api_key")
