import streamlit as st
from utils.api_utils import call_openai_api, get_prompt_content
from utils.config_loader import get_prompts # To load all prompts once

# Page Configuration
st.set_page_config(page_title="大纲生成", layout="wide", initial_sidebar_state="expanded")
st.sidebar.header("大纲生成") # Optional: Add a header to the sidebar for this page

# Load all prompts once
PROMPTS_CONFIG = get_prompts()

def check_api_config():
    """Checks if API is configured and displays a message if not."""
    if "api_config" not in st.session_state or not st.session_state.api_config.get("configured", False):
        st.warning("API 尚未配置。请先前往 🔑 API 配置页面进行设置。")
        st.page_link("pages/00_API_Configuration.py", label="前往 API 配置", icon="🔑")
        return False
    return True

def outline_generation_page():
    st.title("步骤 1: 📝 大纲生成")
    st.markdown("请输入您的视频主题，AI 将为您生成初步的视频大纲。")

    if not check_api_config():
        st.stop() # Stop execution if API is not configured

    # Initialize session state variables for this page if they don't exist
    if "topic_input" not in st.session_state:
        st.session_state.topic_input = ""
    if "outline_content" not in st.session_state:
        st.session_state.outline_content = ""
    if "outline_score_feedback" not in st.session_state:
        st.session_state.outline_score_feedback = ""
    if "last_outline_request" not in st.session_state: # For "View AI Request"
        st.session_state.last_outline_request = {}
    if "last_score_request" not in st.session_state: # For "View AI Request"
        st.session_state.last_score_request = {}


    # --- UI Elements ---
    st.session_state.topic_input = st.text_area(
        "请输入视频主题:", 
        value=st.session_state.topic_input,
        height=100,
        placeholder="例如：如何用 Streamlit 制作一个简单的 Web 应用"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 生成大纲", type="primary", use_container_width=True):
            if not st.session_state.topic_input.strip():
                st.warning("请输入视频主题。")
            else:
                with st.spinner("AI 正在生成大纲中，请稍候..."):
                    api_conf = st.session_state.api_config
                    system_msg, user_msg_text_template, params = get_prompt_content( # Renamed user_msg_template to user_msg_text_template for clarity
                        "outline_generation", 
                        api_conf["selected_model"], 
                        PROMPTS_CONFIG,
                        {"topic": st.session_state.topic_input}
                    )
                    st.session_state.last_outline_request = {"system": system_msg, "user": user_msg_text_template, "params": params}

                    if user_msg_text_template is not None: # Check if prompt text was successfully prepared
                        generated_outline = call_openai_api(
                            api_key=api_conf["api_key"],
                            base_url=api_conf["base_url"],
                            model=api_conf["selected_model"],
                            system_message=system_msg,
                            user_message_text=user_msg_text_template, # Changed from user_message
                            temperature=params.get("temperature", 0.7), 
                            max_tokens=params.get("max_tokens", 1500)
                        )
                        if generated_outline:
                            st.session_state.outline_content = generated_outline
                            st.session_state.outline_score_feedback = "" # Clear previous score
                        else:
                            st.error("未能生成大纲。请检查 API 配置或稍后再试。")
                    else:
                        st.error("未能准备生成大纲的提示词。")


    st.divider()
    st.subheader("AI 生成的大纲")
    st.session_state.outline_content = st.text_area(
        "预览和编辑大纲:", 
        value=st.session_state.outline_content, 
        height=300,
        key="outline_edit_area"
    )

    if st.session_state.outline_content:
        if st.button("🧐 AI 评分大纲", use_container_width=True):
            with st.spinner("AI 正在对大纲进行评分，请稍候..."):
                api_conf = st.session_state.api_config
                system_msg, user_msg_text_template, params = get_prompt_content( # Renamed for clarity
                    "outline_scoring",
                    api_conf["selected_model"],
                    PROMPTS_CONFIG,
                    {"outline_content": st.session_state.outline_content}
                )
                st.session_state.last_score_request = {"system": system_msg, "user": user_msg_text_template, "params": params}

                if user_msg_text_template is not None: # Check if prompt text was successfully prepared
                    score_feedback = call_openai_api(
                        api_key=api_conf["api_key"],
                        base_url=api_conf["base_url"],
                        model=api_conf["selected_model"], 
                        system_message=system_msg,
                        user_message_text=user_msg_text_template, # Changed from user_message
                        temperature=params.get("temperature", 0.5),
                        max_tokens=params.get("max_tokens", 1000)
                    )
                    if score_feedback:
                        st.session_state.outline_score_feedback = score_feedback
                    else:
                        st.error("未能获取大纲评分。")
                else:
                    st.error("未能准备评分大纲的提示词。")


    if st.session_state.outline_score_feedback:
        st.subheader("AI 评分反馈")
        st.markdown(st.session_state.outline_score_feedback)

    # --- Optional: View AI Request ---
    with st.expander("🔍 查看上一次 AI 请求内容 (仅供调试)", expanded=False):
        if st.session_state.last_outline_request.get("user"):
            st.markdown("**上次生成大纲请求:**")
            st.json(st.session_state.last_outline_request)
        if st.session_state.last_score_request.get("user"):
            st.markdown("**上次评分大纲请求:**")
            st.json(st.session_state.last_score_request)
            
    # --- Navigation or next step ---
    if st.session_state.outline_content:
        st.divider()
        if st.button("✅ 确认大纲并前往口播稿生成", type="primary"):
            st.success("大纲已确认！请从左侧导航栏选择“口播稿生成”。")
            st.page_link("pages/02_🗣️_口播稿生成.py", label="前往口播稿生成", icon="🗣️")


if __name__ == "__main__":
    outline_generation_page()