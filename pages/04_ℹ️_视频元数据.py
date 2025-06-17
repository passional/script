import streamlit as st
import pandas as pd
from utils.api_utils import call_openai_api, get_prompt_content
from utils.config_loader import get_prompts
import json # For potential display or processing if AI returns JSON string
import re # For more robust parsing if needed

# Page Configuration
st.set_page_config(page_title="视频元数据生成", layout="wide", initial_sidebar_state="expanded")
st.sidebar.header("视频元数据生成")

PROMPTS_CONFIG = get_prompts()

def check_prerequisites():
    """Checks if API is configured, storyboard_data, and script_content exist."""
    if "api_config" not in st.session_state or not st.session_state.api_config.get("configured", False):
        st.warning("API 尚未配置。请先前往 🔑 API 配置页面进行设置。")
        st.page_link("pages/00_API_Configuration.py", label="前往 API 配置", icon="🔑")
        return False
    
    if "storyboard_data" not in st.session_state or not isinstance(st.session_state.storyboard_data, pd.DataFrame) or st.session_state.storyboard_data.empty:
        st.warning("尚未生成或确认分镜脚本。请先前往 🎬 分镜脚本页面完成。")
        st.page_link("pages/03_🎬_分镜脚本.py", label="前往分镜脚本生成", icon="🎬")
        return False

    if "script_content" not in st.session_state or not st.session_state.script_content or not st.session_state.script_content.strip():
        st.warning("尚未生成口播稿。请先前往 🗣️ 口播稿生成页面完成。")
        st.page_link("pages/02_🗣️_口播稿生成.py", label="前往口播稿生成", icon="🗣️")
        return False
    return True

# def get_storyboard_summary(storyboard_df: pd.DataFrame): # This function is no longer needed
#     """Creates a summary from the storyboard DataFrame for the AI prompt."""
#     if storyboard_df.empty:
#         return "分镜脚本为空。"
    
#     summary_parts = []
#     if "中文口播文案" in storyboard_df.columns:
#         all_speech = "\n".join(storyboard_df["中文口播文案"].dropna().astype(str).tolist())
#         if all_speech.strip():
#             summary_parts.append("口播文案概要：\n" + all_speech[:1000] + "...") # Limit length
    
#     if "画面描述" in storyboard_df.columns:
#         all_descriptions = "\n".join(storyboard_df["画面描述"].dropna().astype(str).tolist())
#         if all_descriptions.strip():
#             summary_parts.append("\n\n画面描述概要：\n" + all_descriptions[:1000] + "...")

#     if not summary_parts:
#         return "无法从分镜脚本生成有效概要（缺少'中文口播文案'或'画面描述'列，或内容为空）。"
        
#     return "\n".join(summary_parts)


def metadata_generation_page():
    st.title("步骤 3.5: ℹ️ 视频元数据生成")
    st.markdown("根据已确认的口播稿，AI 将为您生成视频标题、描述、缩略图提示词等。") # Updated markdown

    if not check_prerequisites():
        st.stop()

    # Initialize session state variables
    if "unified_metadata_text" not in st.session_state:
        st.session_state.unified_metadata_text = ""
    if "last_metadata_request" not in st.session_state:
        st.session_state.last_metadata_request = {}
    if "raw_ai_metadata_output_for_debug" not in st.session_state:
        st.session_state.raw_ai_metadata_output_for_debug = ""

    script_content_for_metadata = st.session_state.get("script_content", "口播稿内容尚未生成。") # Get script content

    st.subheader("口播稿内容预览") # Updated subheader
    with st.expander("点击查看/隐藏口播稿内容", expanded=False): # Updated expander label
        st.markdown(f"```\n{script_content_for_metadata}\n```") # Display script_content
    
    st.divider()

    if st.button("🚀 生成/重新生成视频元数据", type="primary", use_container_width=True):
        if not script_content_for_metadata or script_content_for_metadata == "口播稿内容尚未生成。": # Check script_content
            st.error("无法生成元数据，因为口播稿内容为空或尚未生成。")
        else:
            with st.spinner("AI 正在生成视频元数据中，请稍候..."):
                api_conf = st.session_state.api_config
                system_msg, user_msg_text_template, params = get_prompt_content(
                    "video_metadata_generation",
                    api_conf["selected_model"],
                    PROMPTS_CONFIG,
                    {"storyboard_summary_or_full_script": script_content_for_metadata, "target_audience_or_style": ""} # Use script_content
                )
                st.session_state.last_metadata_request = {"system": system_msg, "user": user_msg_text_template, "params": params}

                if user_msg_text_template is not None:
                    raw_metadata_output = call_openai_api(
                        api_key=api_conf["api_key"],
                        base_url=api_conf["base_url"],
                        model=api_conf["selected_model"],
                        system_message=system_msg,
                        user_message_text=user_msg_text_template, # Changed from user_message
                        temperature=params.get("temperature", 0.7),
                        max_tokens=params.get("max_tokens", 1500) 
                    )
                    st.session_state.raw_ai_metadata_output_for_debug = raw_metadata_output # Store for debugging
                    
                    if raw_metadata_output:
                        st.session_state.unified_metadata_text = raw_metadata_output # Store as single text
                        st.success("视频元数据已生成/更新！")
                    else:
                        st.error("未能生成视频元数据。请检查 API 配置或稍后再试。")
                        st.session_state.unified_metadata_text = "AI未能返回元数据。" # Placeholder on error
                else:
                    st.error("未能准备生成视频元数据的提示词。")
    
    st.divider()
    st.subheader("生成的视频元数据 (可编辑)")

    # Unified Metadata Text Area
    st.markdown("**统一视频元数据 (标题、描述、关键词等):**")
    st.session_state.unified_metadata_text = st.text_area(
        "编辑AI生成的元数据:",
        value=st.session_state.get("unified_metadata_text", ""),
        height=300,
        key="unified_metadata_edit_area"
    )


    # --- Optional: View AI Request & Raw Output ---
    with st.expander("🔍 查看上一次 AI 请求及原始输出 (仅供调试)", expanded=False):
        if st.session_state.last_metadata_request.get("user"):
            st.markdown("**上次生成元数据请求:**")
            st.json(st.session_state.last_metadata_request)
        if st.session_state.raw_ai_metadata_output_for_debug: # Check if it has content
            st.markdown("**AI原始返回内容:**")
            st.text(st.session_state.raw_ai_metadata_output_for_debug)
            
    # --- Navigation or next step ---
    # --- Navigation or next step ---
    # Check if the unified metadata text exists and is not empty
    metadata_exists = bool(st.session_state.get("unified_metadata_text", "").strip())
    if metadata_exists:
        st.divider()
        if st.button("✅ 确认元数据并前往后续步骤", type="primary"):
            st.success("视频元数据已确认！")
            st.info("您可以从左侧导航栏选择“图生视频提示词生成”或“多语言翻译”。")
            # Keep navigation links as they are, assuming they are still relevant next steps
            col_nav1, col_nav2 = st.columns(2)
            with col_nav1:
                st.page_link("pages/05_🖼️_图生视频提示词.py", label="前往图生视频提示词", icon="🖼️", use_container_width=True)
            with col_nav2:
                st.page_link("pages/06_🌍_多语言翻译.py", label="前往多语言翻译", icon="🌍", use_container_width=True)


if __name__ == "__main__":
    metadata_generation_page()