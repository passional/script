import streamlit as st
from utils.api_utils import call_openai_api, get_prompt_content
from utils.config_loader import get_prompts
import pandas as pd
import time
import json

# Page Configuration
st.set_page_config(page_title="多语言MD报告生成", layout="wide", initial_sidebar_state="expanded")
st.sidebar.header("多语言MD报告生成")

PROMPTS_CONFIG = get_prompts()

SUPPORTED_LANGUAGES = {
    "简体中文 (Simplified Chinese)": "Simplified Chinese", # Should not be a target for this page usually
    "英语 (English)": "English",
    "法语 (Français)": "French",
    "德语 (Deutsch)": "German",
    "西班牙语 (Español)": "Spanish",
    "葡萄牙语 (Português)": "Portuguese",
    "日语 (日本語)": "Japanese"
}
DEFAULT_SOURCE_LANGUAGE = "Simplified Chinese" # Implicitly the source
TARGET_LANGUAGES_FOR_MD_REPORT = {k: v for k, v in SUPPORTED_LANGUAGES.items() if v != DEFAULT_SOURCE_LANGUAGE}


def check_prerequisites():
    if "api_config" not in st.session_state or not st.session_state.api_config.get("configured", False):
        st.warning("API 尚未配置。请先前往 🔑 API 配置页面进行设置。")
        st.page_link("pages/00_API_Configuration.py", label="前往 API 配置", icon="🔑")
        return False
    if "storyboard_data" not in st.session_state or st.session_state.storyboard_data.empty:
        st.warning("分镜脚本数据不存在。请先前往 🎬 分镜脚本页面生成。")
        st.page_link("pages/03_🎬_分镜脚本.py", label="前往分镜脚本生成", icon="🎬")
        return False
    # Check for the new unified_metadata_text
    if "unified_metadata_text" not in st.session_state or not st.session_state.unified_metadata_text.strip():
        st.warning("统一视频元数据不存在或为空。请先前往 ℹ️ 视频元数据页面生成并确认。")
        st.page_link("pages/04_ℹ️_视频元数据.py", label="前往视频元数据生成", icon="ℹ️")
        return False
    return True

def translation_md_report_page():
    st.title("步骤 5: 🌍 多语言MD报告生成")
    st.markdown("""
    AI 将根据您的分镜脚本和视频元数据，直接生成包含翻译和格式的完整MD报告。
    **注意：** 此过程将一次性完成翻译和格式化。精细的逐项编辑和评分功能在此模式下不可用。 
    最终输出的质量高度依赖于AI的理解和提示词的精确性。
    """)

    if not check_prerequisites():
        st.stop()

    # Prepare original data for initial population of text areas
    storyboard_df_initial = st.session_state.get("storyboard_data", pd.DataFrame())
    scenes_data_initial = []
    if not storyboard_df_initial.empty and "中文口播文案" in storyboard_df_initial.columns:
        for index, row in storyboard_df_initial.iterrows():
            scenes_data_initial.append({
                "scene_number": str(row.get('画面序号', index + 1)),
                "chinese_narration": str(row["中文口播文案"])
            })
    storyboard_scenes_json_initial = json.dumps({"scenes": scenes_data_initial}, ensure_ascii=False, indent=2)
    video_metadata_text_initial = st.session_state.get("unified_metadata_text", "")

    # Initialize session state for editable data if not already present
    if "editable_storyboard_json" not in st.session_state:
        st.session_state.editable_storyboard_json = storyboard_scenes_json_initial
    if "editable_metadata_text" not in st.session_state:
        st.session_state.editable_metadata_text = video_metadata_text_initial

    st.subheader("1. 预览和编辑翻译数据源")
    st.markdown("您可以在下方编辑分镜脚本和视频元数据，编辑后的内容将用于翻译。")

    expander_col1, expander_col2 = st.columns(2)
    with expander_col1:
        with st.expander("分镜脚本数据 (JSON)", expanded=True):
            st.text_area(
                "编辑分镜脚本 JSON:",
                value=st.session_state.editable_storyboard_json,
                height=300,
                key="editable_storyboard_json",
                help="编辑将用于翻译的分镜脚本JSON数据。"
            )
    with expander_col2:
        with st.expander("视频元数据 (文本)", expanded=True):
            st.text_area(
                "编辑视频元数据:",
                value=st.session_state.editable_metadata_text,
                height=300,
                key="editable_metadata_text",
                help="编辑将用于翻译的视频元数据。"
            )
    st.divider()

    # Initialize session state for generated MD reports and last request
    if "generated_md_reports" not in st.session_state:
        st.session_state.generated_md_reports = {} # Stores {lang_code: md_content}
    if "last_md_generation_request" not in st.session_state:
        st.session_state.last_md_generation_request = {}
    if "current_target_lang_for_preview" not in st.session_state:
        st.session_state.current_target_lang_for_preview = None

    st.subheader("2. 选择目标语言生成MD报告") # Changed subheader to reflect step
    
    cols = st.columns(3) # Adjust number of columns as needed
    col_idx = 0

    for lang_display_name, lang_code in TARGET_LANGUAGES_FOR_MD_REPORT.items():
        with cols[col_idx % len(cols)]:
            if st.button(f"🚀 生成 {lang_display_name} MD报告", key=f"generate_md_{lang_code}", use_container_width=True):
                st.session_state.current_target_lang_for_preview = lang_code
                st.session_state.generated_md_reports[lang_code] = None # Clear previous for this lang
                
                # Get edited data from session state
                storyboard_scenes_json_edited = st.session_state.get("editable_storyboard_json", "")
                video_metadata_text_edited = st.session_state.get("editable_metadata_text", "")

                # Input validation for the edited data
                scenes_data_from_json = []
                try:
                    parsed_storyboard = json.loads(storyboard_scenes_json_edited)
                    if isinstance(parsed_storyboard, dict) and "scenes" in parsed_storyboard and isinstance(parsed_storyboard["scenes"], list):
                        scenes_data_from_json = parsed_storyboard["scenes"]
                        # It's okay if scenes_data_from_json is empty, the prompt might handle it or it's intended.
                        # if not scenes_data_from_json:
                        #     st.warning("编辑后的分镜脚本数据中 'scenes' 列表为空。翻译可能不完整。")
                    else:
                        st.error("编辑后的分镜脚本数据格式不正确。顶层应为包含 'scenes' 列表的JSON对象。请修正后重试。")
                        st.stop()
                except json.JSONDecodeError:
                    st.error("编辑后的分镜脚本数据不是有效的JSON格式。请检查并修正后重试。")
                    st.stop()
                
                if not video_metadata_text_edited.strip():
                    st.error("编辑后的元数据不能为空。请检查并修正后重试。")
                    st.stop()

                # Use the edited (and validated) data for the API call
                storyboard_scenes_json_to_use = storyboard_scenes_json_edited
                video_metadata_text_to_use = video_metadata_text_edited

                with st.spinner(f"AI 正在为 {lang_display_name} 生成MD报告，请稍候... (这可能需要一些时间)"):
                    api_conf = st.session_state.api_config
                    prompt_name = "translate_and_format_to_md_zh" # Using the Chinese version of the prompt

                    prompt_vars = {
                        "target_language": lang_code,
                        "storyboard_scenes_json": storyboard_scenes_json_to_use,
                        "video_metadata_text": video_metadata_text_to_use
                    }
                    # Get the raw template first for debugging log
                    _, raw_user_template_for_log, _ = get_prompt_content(
                        prompt_name, api_conf["selected_model"], PROMPTS_CONFIG # No vars passed here
                    )

                    # Now get the formatted message by passing prompt_vars
                    system_msg, formatted_user_msg, params = get_prompt_content(
                        prompt_name, api_conf["selected_model"], PROMPTS_CONFIG, prompt_vars
                    )
                    
                    st.session_state.last_md_generation_request = {
                        "prompt_name": prompt_name, "target_language": lang_code,
                        "system_message": system_msg,
                        "user_message_template": raw_user_template_for_log,
                        "storyboard_scenes_json_input": storyboard_scenes_json_to_use,
                        "video_metadata_text_input": video_metadata_text_to_use,
                        "final_user_message": formatted_user_msg if formatted_user_msg is not None else "Error in template formatting",
                        "params": params
                    }

                    if formatted_user_msg is not None:
                        final_user_message = formatted_user_msg

                        md_output = call_openai_api(
                            api_key=api_conf["api_key"], base_url=api_conf["base_url"],
                            model=api_conf["selected_model"], system_message=system_msg,
                            user_message_text=final_user_message,
                            temperature=params.get("temperature", 0.4), # Slightly lower for more deterministic formatting
                            max_tokens=params.get("max_tokens", 65536) 
                        )
                        if md_output:
                            st.session_state.generated_md_reports[lang_code] = md_output
                            st.success(f"{lang_display_name} MD报告已生成！")
                        else:
                            st.error(f"未能为 {lang_display_name} 生成MD报告。AI未返回有效内容。")
                            st.session_state.generated_md_reports[lang_code] = f"## 生成失败\n\nAI未能为 {lang_display_name} 返回有效内容。"
                    else:
                        st.error(f"未能为 {lang_display_name} 准备生成MD报告的提示词。")
                        st.session_state.generated_md_reports[lang_code] = f"## 生成失败\n\n未能为 {lang_display_name} 准备提示词。"
                st.rerun() # To update preview
        col_idx += 1
    
    st.divider()
    st.subheader("3. MD报告预览与下载") # Changed subheader to reflect step

    if st.session_state.current_target_lang_for_preview and \
       st.session_state.current_target_lang_for_preview in st.session_state.generated_md_reports:
        
        lang_code_to_preview = st.session_state.current_target_lang_for_preview
        lang_display_name_preview = [k for k, v in TARGET_LANGUAGES_FOR_MD_REPORT.items() if v == lang_code_to_preview][0]
        
        md_content_to_preview = st.session_state.generated_md_reports[lang_code_to_preview]

        if md_content_to_preview:
            st.markdown(f"#### {lang_display_name_preview} MD报告预览:")
            with st.container(height=500, border=True): # Scrollable container
                st.markdown(md_content_to_preview)
            
            st.download_button(
                label=f"📥 下载 {lang_display_name_preview} MD文件",
                data=md_content_to_preview,
                file_name=f"video_script_report_{lang_code_to_preview}.md",
                mime="text/markdown",
                key=f"download_final_md_{lang_code_to_preview}"
            )
        else:
            st.info(f"尚未生成 {lang_display_name_preview} 的MD报告，或生成失败。请点击上方按钮生成。")
    else:
        st.info("请选择一个目标语言并点击生成按钮以预览和下载报告。")

    with st.expander("🔍 查看上一次AI请求详情 (仅供调试)", expanded=False):
        if st.session_state.last_md_generation_request:
            st.json(st.session_state.last_md_generation_request) # Removed expanded_keys


if __name__ == "__main__":
    translation_md_report_page()