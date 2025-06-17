import streamlit as st
import pandas as pd
import json
from utils.api_utils import call_openai_api, get_prompt_content
from utils.config_loader import get_prompts
from utils.parsing_utils import parse_markdown_table_to_df

# Page Configuration
st.set_page_config(page_title="分镜脚本生成", layout="wide", initial_sidebar_state="expanded")
st.sidebar.header("分镜脚本生成")

PROMPTS_CONFIG = get_prompts()

def check_prerequisites():
    """Checks if API is configured and script content exists."""
    if "api_config" not in st.session_state or not st.session_state.api_config.get("configured", False):
        st.warning("API 尚未配置。请先前往 🔑 API 配置页面进行设置。")
        st.page_link("pages/00_API_Configuration.py", label="前往 API 配置", icon="🔑")
        return False
    
    if "script_content" not in st.session_state or not st.session_state.script_content.strip():
        st.warning("尚未生成或确认口播稿。请先前往 🗣️ 口播稿生成页面完成。")
        st.page_link("pages/02_🗣️_口播稿生成.py", label="前往口播稿生成", icon="🗣️")
        return False
    return True

def storyboard_generation_page():
    st.title("步骤 3: 🎬 分镜脚本生成")
    st.markdown("根据已确认的口播稿，AI 将为您生成分镜脚本。")

    if not check_prerequisites():
        st.stop()

    # Initialize session state variables
    if "storyboard_data" not in st.session_state: # Will store list of dicts or DataFrame
        st.session_state.storyboard_data = pd.DataFrame(columns=['画面序号', '中文口播文案', '文生图提示词 (英文)', '画面描述'])
    if "last_storyboard_request" not in st.session_state:
        st.session_state.last_storyboard_request = {}

    st.subheader("已确认口播稿预览")
    with st.expander("点击查看/隐藏口播稿内容", expanded=False):
        st.markdown(f"```markdown\n{st.session_state.script_content}\n```")
    
    st.divider()

    if st.button("🚀 生成/重新生成分镜脚本", type="primary", use_container_width=True):
        with st.spinner("AI 正在生成分镜脚本中，请稍候..."):
            api_conf = st.session_state.api_config
            system_msg, user_msg_text_template, params = get_prompt_content( # Renamed for clarity
                "storyboard_generation",
                api_conf["selected_model"],
                PROMPTS_CONFIG,
                {"script_content": st.session_state.script_content}
            )
            st.session_state.last_storyboard_request = {"system": system_msg, "user": user_msg_text_template, "params": params}

            if user_msg_text_template is not None: # Check if prompt text was successfully prepared
                markdown_table_output = call_openai_api(
                    api_key=api_conf["api_key"],
                    base_url=api_conf["base_url"],
                    model=api_conf["selected_model"],
                    system_message=system_msg,
                    user_message_text=user_msg_text_template, # Changed from user_message
                    temperature=params.get("temperature", 0.6), 
                    max_tokens=params.get("max_tokens", 2500) 
                )
                if markdown_table_output:
                    parsed_df = parse_markdown_table_to_df(markdown_table_output)
                    if not parsed_df.empty:
                        st.session_state.storyboard_data = parsed_df
                        st.success("分镜脚本已生成！")
                    else:
                        st.error("未能从 AI 返回内容中解析出有效的分镜表格数据。请检查 AI 返回或提示词。")
                        st.text_area("AI原始返回内容（供调试）：", value=markdown_table_output, height=200)
                else:
                    st.error("未能生成分镜脚本。请检查 API 配置或稍后再试。")
            else:
                st.error("未能准备生成分镜脚本的提示词。")
    
    st.divider()
    st.subheader("分镜脚本表格 (可编辑)")

    if isinstance(st.session_state.storyboard_data, pd.DataFrame) and not st.session_state.storyboard_data.empty:
        edited_df = st.data_editor(
            st.session_state.storyboard_data, 
            num_rows="dynamic", 
            use_container_width=True,
            key="storyboard_editor"
        )
        if edited_df is not None: 
            if not st.session_state.storyboard_data.equals(edited_df):
                 st.session_state.storyboard_data = edited_df
                 st.caption("更改已在编辑器中反映。")


        # Export to JSON
        if not edited_df.empty: 
            storyboard_json = edited_df.to_json(orient="records", indent=4, force_ascii=False)
            st.download_button(
                label="📥 下载分镜脚本 (JSON)",
                data=storyboard_json,
                file_name="storyboard_script.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.info("尚未生成分镜脚本，或生成的数据为空。请点击上方按钮生成。")

    # --- Optional: View AI Request ---
    with st.expander("🔍 查看上一次 AI 请求内容 (仅供调试)", expanded=False):
        if st.session_state.last_storyboard_request.get("user"):
            st.markdown("**上次生成分镜脚本请求:**")
            st.json(st.session_state.last_storyboard_request)
            
    # --- Navigation or next step ---
    # Corrected the spelling of storyboard_data here
    if isinstance(st.session_state.storyboard_data, pd.DataFrame) and not st.session_state.storyboard_data.empty:
        st.divider()
        if st.button("✅ 确认分镜并前往视频元数据生成", type="primary"):
            st.success("分镜脚本已确认！请从左侧导航栏选择“视频元数据”。")
            st.page_link("pages/04_ℹ️_视频元数据.py", label="前往视频元数据生成", icon="ℹ️")


if __name__ == "__main__":
    storyboard_generation_page()