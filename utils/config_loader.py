import yaml
import streamlit as st

PROMPTS_FILE = "prompts.yaml"

@st.cache_data # Cache the loaded YAML data
def load_yaml_config():
    """Loads the YAML configuration file."""
    try:
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        st.error(f"错误：找不到 {PROMPTS_FILE} 文件。请确保该文件存在于项目根目录。")
        return None
    except yaml.YAMLError as e:
        st.error(f"错误：解析 {PROMPTS_FILE} 文件时出错：{e}")
        return None

def get_provider_configs():
    """Returns the list of available model provider configurations."""
    config = load_yaml_config()
    if config and "available_model_providers" in config:
        return config["available_model_providers"]
    return []

def get_prompts():
    """Returns the prompts configuration."""
    config = load_yaml_config()
    if config and "prompts" in config:
        return config["prompts"]
    return {}