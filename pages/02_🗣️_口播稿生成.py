import streamlit as st
from utils.api_utils import call_openai_api, get_prompt_content
from utils.config_loader import get_prompts

# Page Configuration
st.set_page_config(page_title="口播稿生成", layout="wide", initial_sidebar_state="expanded")
st.sidebar.header("口播稿生成")

PROMPTS_CONFIG = get_prompts()

def check_prerequisites():
    """Checks if API is configured and outline exists."""
    if "api_config" not in st.session_state or not st.session_state.api_config.get("configured", False):
        st.warning("API 尚未配置。请先前往 🔑 API 配置页面进行设置。")
        st.page_link("pages/00_API_Configuration.py", label="前往 API 配置", icon="🔑")
        return False
    
    if "outline_content" not in st.session_state or not st.session_state.outline_content.strip():
        st.warning("尚未生成或确认大纲。请先前往 📝 大纲生成页面完成大纲。")
        st.page_link("pages/01_📝_大纲生成.py", label="前往大纲生成", icon="📝")
        return False
    return True

def script_generation_page():
    st.title("步骤 2: 🗣️ 口播稿生成")
    st.markdown("根据已确认的视频大纲，AI 将为您生成初步的口播文案。")

    if not check_prerequisites():
        st.stop()

    # Initialize session state variables for this page
    if "word_count_target" not in st.session_state:
        st.session_state.word_count_target = 1000 # Default word count
    if "script_content" not in st.session_state:
        st.session_state.script_content = ""
    if "script_score_feedback" not in st.session_state:
        st.session_state.script_score_feedback = ""
    if "last_script_request" not in st.session_state:
        st.session_state.last_script_request = {}
    if "last_script_score_request" not in st.session_state:
        st.session_state.last_script_score_request = {}

    st.subheader("已确认大纲预览")
    with st.expander("点击查看/隐藏大纲内容", expanded=False):
        st.markdown(f"```markdown\n{st.session_state.outline_content}\n```")
    
    st.divider()

    # --- UI Elements ---
    st.session_state.word_count_target = st.number_input(
        "期望口播稿字数:", 
        min_value=100, 
        max_value=10000, 
        value=st.session_state.word_count_target, 
        step=100
    )

    if st.button("🚀 生成口播稿", type="primary", use_container_width=True):
        with st.spinner("AI 正在生成口播稿中，请稍候..."):
            api_conf = st.session_state.api_config
            system_msg, user_msg_text_template, params = get_prompt_content( # Renamed for clarity
                "script_generation",
                api_conf["selected_model"],
                PROMPTS_CONFIG,
                {
                    "outline": st.session_state.outline_content,
                    "word_count": st.session_state.word_count_target
                }
            )
            st.session_state.last_script_request = {"system": system_msg, "user": user_msg_text_template, "params": params}

            if user_msg_text_template is not None: # Check if prompt text was successfully prepared
                generated_script = call_openai_api(
                    api_key=api_conf["api_key"],
                    base_url=api_conf["base_url"],
                    model=api_conf["selected_model"],
                    system_message=system_msg,
                    user_message_text=user_msg_text_template, # Changed from user_message
                    temperature=params.get("temperature", 0.7),
                    max_tokens=params.get("max_tokens", 3000) 
                )
                if generated_script:
                    st.session_state.script_content = generated_script
                    st.session_state.script_score_feedback = "" # Clear previous score
                else:
                    st.error("未能生成口播稿。请检查 API 配置或稍后再试。")
            else:
                st.error("未能准备生成口播稿的提示词。")
    
    st.divider()
    st.subheader("AI 生成的口播稿")
    st.session_state.script_content = st.text_area(
        "预览和编辑口播稿:",
        value=st.session_state.script_content,
        height=400,
        key="script_edit_area"
    )

    if st.session_state.script_content:
        if st.button("🧐 AI 评分口播稿", use_container_width=True):
            with st.spinner("AI 正在对口播稿进行评分，请稍候..."):
                api_conf = st.session_state.api_config
                system_msg, user_msg_text_template, params = get_prompt_content( # Renamed for clarity
                    "script_scoring",
                    api_conf["selected_model"],
                    PROMPTS_CONFIG,
                    {"script_content": st.session_state.script_content}
                )
                st.session_state.last_script_score_request = {"system": system_msg, "user": user_msg_text_template, "params": params}

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
                        st.session_state.script_score_feedback = score_feedback
                    else:
                        st.error("未能获取口播稿评分。")
                else:
                    st.error("未能准备评分口播稿的提示词。")

    if st.session_state.script_score_feedback:
        st.subheader("AI 评分反馈")
        st.markdown(st.session_state.script_score_feedback)

    # --- Optional: View AI Request ---
    with st.expander("🔍 查看上一次 AI 请求内容 (仅供调试)", expanded=False):
        if st.session_state.last_script_request.get("user"):
            st.markdown("**上次生成口播稿请求:**")
            st.json(st.session_state.last_script_request)
        if st.session_state.last_script_score_request.get("user"):
            st.markdown("**上次评分口播稿请求:**")
            st.json(st.session_state.last_script_score_request)
            
    # --- Navigation or next step ---
    if st.session_state.script_content:
        st.divider()
        if st.button("✅ 确认口播稿并前往分镜脚本生成", type="primary"):
            st.success("口播稿已确认！请从左侧导航栏选择“分镜脚本”。")
            st.page_link("pages/03_🎬_分镜脚本.py", label="前往分镜脚本生成", icon="🎬")

if __name__ == "__main__":
    script_generation_page()