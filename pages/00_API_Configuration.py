import streamlit as st
from utils.config_loader import get_provider_configs # Assuming utils is in parent directory or PYTHONPATH

def api_configuration_ui():
    """Displays UI for API configuration and stores it in session_state."""
    st.header("步骤 0: API 配置 🔑")
    
    provider_configs = get_provider_configs()
    if not provider_configs:
        st.error("未能加载模型提供商配置。请检查 `prompts.yaml` 文件。")
        return False

    provider_names = [p["provider_name"] for p in provider_configs]
    
    # Initialize session state for API config if not already present
    if "api_config" not in st.session_state:
        st.session_state.api_config = {
            "selected_provider_name": provider_names[0] if provider_names else None,
            "api_key": "",
            "base_url": "",
            "selected_model": None,
            "configured": False
        }

    # Let user select a provider
    # Use a temporary variable to get the widget's current state, then update session_state
    # This helps avoid issues with widget state during reruns if not handled carefully
    current_selection_in_widget = st.selectbox(
        "选择 AI 模型提供商:",
        provider_names,
        index=provider_names.index(st.session_state.api_config["selected_provider_name"]) if st.session_state.api_config["selected_provider_name"] in provider_names else 0,
        key="selected_provider_name_widget_config_page" 
    )
    st.session_state.api_config["selected_provider_name"] = current_selection_in_widget
    selected_provider_name = current_selection_in_widget # use this for logic below

    selected_provider_details = next((p for p in provider_configs if p["provider_name"] == selected_provider_name), None)

    if selected_provider_details:
        # API Key input
        current_api_key = st.text_input(
            "API Key:",
            type="password",
            value=st.session_state.api_config.get("api_key", ""),
            key="api_key_input_config_page"
        )
        st.session_state.api_config["api_key"] = current_api_key

        # Base URL input (prefill with template, allow user modification)
        default_base_url = selected_provider_details.get("base_url_template", "")
        # If base_url in session_state is empty, use default_base_url, otherwise use session_state's value
        base_url_to_display = st.session_state.api_config.get("base_url", "") or default_base_url
        
        current_base_url = st.text_input(
            "Base URL:",
            value=base_url_to_display,
            key="base_url_input_config_page"
        )
        st.session_state.api_config["base_url"] = current_base_url
        
        available_models = selected_provider_details.get("models", [])
        if available_models:
            # Model selection
            current_model_selection_in_state = st.session_state.api_config.get("selected_model")
            model_index = 0
            if current_model_selection_in_state and current_model_selection_in_state in available_models:
                model_index = available_models.index(current_model_selection_in_state)
            
            selected_model_in_widget = st.selectbox(
                "选择模型:",
                available_models,
                index=model_index,
                key="selected_model_widget_config_page"
            )
            st.session_state.api_config["selected_model"] = selected_model_in_widget
        else:
            st.warning(f"提供商 '{selected_provider_name}' 没有可用的模型列表。")
            st.session_state.api_config["selected_model"] = None

        if st.button("保存 API 配置", key="save_api_config_button_config_page"):
            if not st.session_state.api_config["api_key"]:
                st.warning("请输入 API Key。")
            elif not st.session_state.api_config["base_url"]:
                st.warning("请输入 Base URL。")
            elif not st.session_state.api_config["selected_model"] and available_models:
                st.warning("请选择一个模型。")
            else:
                st.session_state.api_config["configured"] = True
                st.success(f"API 配置已保存！提供商: {selected_provider_name}, 模型: {st.session_state.api_config['selected_model']}")
                # st.experimental_rerun() # Consider if rerun is needed or if flow naturally updates
    else:
        st.error("无法找到所选提供商的详细信息。")

    if st.session_state.api_config.get("configured", False):
        st.success(f"当前配置: {st.session_state.api_config['selected_provider_name']} - {st.session_state.api_config['selected_model']}")
        st.info("您可以从左侧导航栏选择其他功能模块了。")
        return True
    else:
        st.info("请完成并保存 API 配置以启用其他功能。")
    return False

# Page title and main execution
st.set_page_config(page_title="API 配置", layout="wide", initial_sidebar_state="expanded")
st.sidebar.success("在此配置您的AI模型API。") # Example sidebar message for this page

if __name__ == "__main__":
    api_configuration_ui()