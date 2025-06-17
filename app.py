import streamlit as st

# Set wide layout by default
st.set_page_config(layout="wide", page_title="YouTube 脚本工具")

st.sidebar.title("导航")

# --- Function to clear project-specific session state ---
def clear_project_data():
    """Clears all project-related data from session_state, preserving API config."""
    keys_to_preserve = ["api_config", "user_logged_in"] # Add other global keys if any
    
    # Create a list of keys to delete to avoid issues with modifying dict during iteration
    keys_to_delete = [key for key in st.session_state.keys() if key not in keys_to_preserve]
    
    for key in keys_to_delete:
        del st.session_state[key]
    st.success("项目数据已清除！您可以开始一个新任务了。")
    # Optionally, navigate to the first page or refresh
    # st.switch_page("pages/01_📝_大纲生成.py") # This causes issues if called directly in callback sometimes
    # A simple rerun might be enough, or let user navigate.
    st.rerun()


# --- Sidebar Navigation ---
# Using st.page_link for Streamlit 1.30+ style navigation
# Ensure your pages are in a 'pages' subdirectory.

# Manually list pages in the desired order for the sidebar
# This also allows us to control the display names and icons more easily.
PAGES = {
    "API 配置": {"path": "pages/00_API_Configuration.py", "icon": "🔑"},
    "大纲生成": {"path": "pages/01_📝_大纲生成.py", "icon": "📝"},
    "口播稿生成": {"path": "pages/02_🗣️_口播稿生成.py", "icon": "🗣️"},
    "分镜脚本": {"path": "pages/03_🎬_分镜脚本.py", "icon": "🎬"},
    "视频元数据": {"path": "pages/04_ℹ️_视频元数据.py", "icon": "ℹ️"},
    "图生视频提示词": {"path": "pages/05_🖼️_图生视频提示词.py", "icon": "🖼️"},
    "多语言翻译": {"path": "pages/06_🌍_多语言翻译.py", "icon": "🌍"}
}

# Display page links in the sidebar
for page_name, page_info in PAGES.items():
    st.sidebar.page_link(page_info["path"], label=page_name, icon=page_info["icon"])

st.sidebar.divider()
if st.sidebar.button("🔄 清除项目数据并开始新任务", use_container_width=True, type="secondary"):
    clear_project_data()


# --- Main Page Content (app.py) ---
st.title("欢迎使用 YouTube 视频脚本辅助工具! 🚀")
st.markdown("""
这是一个多页面应用，旨在帮助您完成从视频主题构思到多语言内容准备的全流程。

**请从左侧导航栏选择一个功能模块开始。**

### 主要功能模块：
1.  **🔑 API 配置**: 设置您的大语言模型 API Key 和 Base URL。
2.  **📝 大纲生成**: 根据主题生成视频大纲，并支持 AI 评分。
3.  **🗣️ 口播稿生成**: 基于大纲生成详细的口播文案，并支持 AI 评分。
4.  **🎬 分镜脚本**: 将口播稿自动拆分为分镜，并为每个分镜生成文生图提示词和画面描述。
5.  **ℹ️ 视频元数据**: 为您的视频生成多个备选标题、详细描述、缩略图AI提示词及缩略图文字。
6.  **🖼️ 图生视频提示词**: (多模态) 上传参考图和画面描述，生成图生视频的英文提示词。
7.  **🌍 多语言翻译**: 将口播稿、标题、描述等批量翻译成多种语言，并导出MD文件。

---
*您可以在任何时候点击侧边栏底部的“清除项目数据并开始新任务”按钮来重置当前项目的所有中间结果（API配置将保留）。*
""")

# Initialize API config in session state if it doesn't exist
if "api_config" not in st.session_state:
    st.session_state.api_config = {
        "selected_provider_name": None,
        "api_key": "",
        "base_url": "",
        "selected_model": None,
        "configured": False
    }

# Simple check to guide user if API is not configured on the main page
if not st.session_state.api_config.get("configured", False):
    st.warning("提醒：您尚未配置 API。请先前往“API 配置”页面进行设置，以便使用各项 AI 功能。")
    if st.button("前往 API 配置"):
        st.switch_page("pages/00_API_Configuration.py")