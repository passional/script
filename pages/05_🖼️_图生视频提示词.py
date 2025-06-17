import streamlit as st
import pandas as pd
from utils.api_utils import call_openai_api, get_prompt_content
from utils.config_loader import get_prompts
import base64 # For encoding image data
import io # For image handling

# Page Configuration
st.set_page_config(page_title="图生视频提示词", layout="wide", initial_sidebar_state="expanded")
st.sidebar.header("图生视频提示词")

PROMPTS_CONFIG = get_prompts()

def check_prerequisites():
    """Checks if API is configured and storyboard_data exists."""
    if "api_config" not in st.session_state or not st.session_state.api_config.get("configured", False):
        st.warning("API 尚未配置。请先前往 🔑 API 配置页面进行设置。")
        st.page_link("pages/00_API_Configuration.py", label="前往 API 配置", icon="🔑")
        return False
    
    if "storyboard_data" not in st.session_state or not isinstance(st.session_state.storyboard_data, pd.DataFrame) or st.session_state.storyboard_data.empty:
        st.warning("尚未生成或确认分镜脚本。请先前往 🎬 分镜脚本页面完成。")
        st.page_link("pages/03_🎬_分镜脚本.py", label="前往分镜脚本生成", icon="🎬")
        return False
    return True

def image_to_video_prompt_page():
    st.title("步骤 4: 🖼️ 图生视频提示词生成")
    st.markdown("为每个分镜上传参考图片，并结合画面描述生成图生视频的 AI 提示词。")

    if not check_prerequisites():
        st.stop()

    # Initialize session state
    if "image_to_video_prompts" not in st.session_state:
        st.session_state.image_to_video_prompts = {} 
    if "uploaded_files_info" not in st.session_state:
        st.session_state.uploaded_files_info = {}


    storyboard_df = st.session_state.storyboard_data
    
    if '画面序号' not in storyboard_df.columns:
        st.error("分镜脚本中缺少 '画面序号' 列。无法继续。")
        st.stop()

    for idx, row in storyboard_df.iterrows():
        scene_id = str(row['画面序号']) 
        scene_description = row.get('画面描述', '无画面描述')
        scene_narration = row.get('中文口播文案', '无口播文案') # 新增获取口播文案

        with st.container(border=True):
            st.subheader(f"分镜 {scene_id}")
            
            col1, col2 = st.columns([0.6, 0.4])
            
            with col1:
                st.markdown(f"**口播文案:** {scene_narration}") # 新增显示口播文案
                st.markdown(f"**画面描述:** {scene_description}")

                uploaded_file = st.file_uploader(
                    f"上传分镜 {scene_id} 的参考图片 (可选)", 
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"uploader_{scene_id}" # Unique key for each uploader
                )

                image_base64_data = None
                image_media_type = None

                if uploaded_file is not None:
                    st.session_state.uploaded_files_info[scene_id] = uploaded_file.name
                    st.image(uploaded_file, caption=f"参考图: {uploaded_file.name}", width=200)
                    try:
                        image_bytes = uploaded_file.getvalue()
                        image_base64_data = base64.b64encode(image_bytes).decode("utf-8")
                        image_media_type = uploaded_file.type
                    except Exception as e:
                        st.error(f"处理上传的图片时出错: {e}")
                        image_base64_data = None # Ensure it's None if error
                
                elif scene_id in st.session_state.uploaded_files_info and uploaded_file is None: 
                    # File was previously uploaded but now removed by user
                    del st.session_state.uploaded_files_info[scene_id]
                    # image_base64_data and image_media_type remain None


                if st.button(f"🤖 为分镜 {scene_id} 生成提示词", key=f"generate_btn_{scene_id}", use_container_width=True):
                    with st.spinner(f"AI 正在为分镜 {scene_id} 生成提示词..."):
                        api_conf = st.session_state.api_config
                        
                        prompt_vars = {"scene_description": scene_description}
                        system_msg, user_msg_text_template, params = get_prompt_content(
                            "image_to_video_prompt_generation",
                            api_conf["selected_model"],
                            PROMPTS_CONFIG,
                            prompt_vars
                        )
                        
                        # Ensure user_msg_text_template is not None before proceeding
                        if user_msg_text_template is not None:
                            generated_prompt = call_openai_api(
                                api_key=api_conf["api_key"],
                                base_url=api_conf["base_url"],
                                model=api_conf["selected_model"],
                                system_message=system_msg,
                                user_message_text=user_msg_text_template, # Text part of the prompt
                                image_data_base64=image_base64_data,     # Base64 image data
                                image_media_type=image_media_type,       # Media type of the image
                                temperature=params.get("temperature", 0.7),
                                max_tokens=params.get("max_tokens", 300) 
                            )
                            if generated_prompt:
                                st.session_state.image_to_video_prompts[scene_id] = generated_prompt
                            else:
                                st.error(f"未能为分镜 {scene_id} 生成提示词。")
                        else:
                             st.error(f"未能为分镜 {scene_id} 准备提示词文本。")
            
            with col2:
                current_prompt = st.session_state.image_to_video_prompts.get(scene_id, "")
                edited_prompt = st.text_area(
                    f"图生视频提示词 (分镜 {scene_id}):",
                    value=current_prompt,
                    height=200,
                    key=f"prompt_edit_{scene_id}",
                    help="AI生成的提示词，您可以编辑和复制。"
                )
                if edited_prompt != current_prompt: 
                    st.session_state.image_to_video_prompts[scene_id] = edited_prompt
                
                if edited_prompt:
                    st.code(edited_prompt, language=None)

    st.divider()
    st.subheader("所有图生视频提示词概览 (JSON)")
    if st.session_state.image_to_video_prompts:
        st.json(st.session_state.image_to_video_prompts)
    else:
        st.info("尚未为任何分镜生成提示词。")

    if st.session_state.image_to_video_prompts: 
        st.divider()
        if st.button("✅ 完成提示词生成，前往多语言翻译", type="primary"):
            st.success("图生视频提示词已生成/编辑！")
            st.page_link("pages/06_🌍_多语言翻译.py", label="前往多语言翻译", icon="🌍")

if __name__ == "__main__":
    image_to_video_prompt_page()