# YouTube 视频脚本制作工具 - 开发计划

## 1. 项目目标

开发一个基于 Streamlit 的 YouTube 视频脚本制作工具，帮助用户从主题输入到最终的多语言脚本、视频元数据和素材提示词生成，实现高效的内容创作流程。

## 2. 核心功能与流程

```mermaid
graph TD
    A[0. 用户输入 API 配置] --> B{API配置完成?};
    B -- 是 --> C[1. 输入视频主题];
    C --> D[AI 生成大纲];
    D --> D_Rate[AI 评分大纲];
    D_Rate --> E{大纲满意?};
    E -- 修改/重评 --> D;
    E -- 是 --> F[2. 输入口播稿字数];
    F --> G[AI 生成口播稿];
    G --> G_Rate[AI 评分口播稿];
    G_Rate --> H{口播稿满意?};
    H -- 修改/重评 --> G;
    H -- 是 --> I[3. AI 生成分镜脚本];
    I --> J{分镜脚本满意?};
    J -- 修改/重生成 --> I;
    J -- 是 --> K[保存分镜脚本到 Session State];
    K --> L_EXPORT(用户可选: 导出分镜脚本 JSON);
    K --> M[3.5 AI 生成视频元数据 (标题/描述/缩略图提示词/文字)];
    M --> N[保存元数据到 Session State];
    N --> O_EXPORT(用户可选: 导出元数据 JSON);

    subgraph MainWorkflow
        direction LR
        K_Data[分镜数据] --> P[4. 图生视频提示词生成];
        N_Data[元数据] -.-> P; subgraph 图生视频提示词
            direction TB
            P_Start[开始] --> P_Check{有分镜数据?};
            P_Check -- 否 --> P_Import[提示导入分镜JSON];
            P_Import --> P_Load[加载分镜数据];
            P_Load --> P_UI;
            P_Check -- 是 --> P_UI[按分镜显示单元];
            P_UI --> P_Upload[用户上传图片];
            P_Upload --> P_AI[AI生成图生视频提示词];
            P_AI --> P_Save[保存提示词到Session State];
        end

        K_Data2[分镜数据] --> S[5. 多语言翻译];
        N_Data2[元数据] --> S; subgraph 多语言翻译
            direction TB
            S_Start[开始] --> S_Check{有分镜和元数据?};
            S_Check -- 否 --> S_Import[提示导入分镜/元数据JSON];
            S_Import --> S_Load[加载数据];
            S_Load --> S_UI;
            S_Check -- 是 --> S_UI[显示待翻译内容];
            S_UI --> S_AI[AI进行多语言翻译 (口播/标题/描述/缩略图文字)];
            S_AI --> S_Rate[AI翻译校准评分];
            S_Rate --> S_Save[保存翻译结果];
            S_Save --> S_Export[用户导出7份MD翻译文件];
        end
    end

    S_Export --> V[6. 新任务?];
    P_Save --> V;
    V -- 是 --> C;

    classDef step fill:#e6f2ff,stroke:#337ab7,stroke-width:2px,color:#333;
    classDef decision fill:#fff0e6,stroke:#ff8c1a,stroke-width:2px,color:#333;
    classDef io fill:#e6ffe6,stroke:#33cc33,stroke-width:2px,color:#333;
    classDef process fill:#f9f2ff,stroke:#9933ff,stroke-width:2px,color:#333;
    classDef substep fill:#fafafa,stroke:#ccc,stroke-width:1px,color:#333;

    class A,C,F,L_EXPORT,O_EXPORT,S_Export,V io;
    class B,E,H,J,P_Check,S_Check decision;
    class D,G,I,M,P_AI,S_AI,D_Rate,G_Rate,S_Rate process;
    class K,N,P_Save substep;
    class P_Start,P_Import,P_Load,P_UI,P_Upload,S_Start,S_Import,S_Load,S_UI step;
```

**流程步骤详解:**

1.  **API 配置 (步骤 0)**: 用户配置兼容 OpenAI 格式的 API Key 和 Base URL。
2.  **大纲生成 (步骤 1)**: 用户输入主题，AI 生成大纲。提供预览、修改、AI 评分（切题性、完整性、吸引力 -> 详细文本建议）、查看 AI 请求功能。
3.  **口播稿生成 (步骤 2)**: 根据确认后的大纲和用户选择的字数，AI 生成口播文案。功能同上。
4.  **分镜脚本生成 (步骤 3)**: 根据口播文案自动生成分镜脚本表格（画面序号, 中文口播, 文生图提示词 (英文), 画面描述）。用户可修改、重新生成，并可**导出为 JSON 文件**。
5.  **视频元数据生成 (步骤 3.5)**: 根据分镜脚本内容，AI 生成 YouTube 视频标题、描述、缩略图AI文生图提示词 (英文)、缩略图文字建议。用户可编辑。此部分可与分镜脚本一同导出。
6.  **图生视频提示词生成 (步骤 4)**:
    *   正常流程: 自动加载已生成的分镜脚本。
    *   恢复流程: 用户可上传之前导出的分镜脚本 JSON 文件。
    *   在新页面，按分镜单元处理。用户为每个分镜上传参考图片，AI 结合画面描述和图片生成图生视频提示词（可编辑、复制）。
7.  **多语言翻译 (步骤 5)**:
    *   正常流程: 自动加载已生成的分镜脚本和视频元数据。
    *   恢复流程: 用户可上传之前导出的分镜脚本和元数据 JSON 文件。
    *   将分镜脚本中的口播文案、视频标题、视频描述、缩略图文字翻译成英文、法语、德语、西班牙语、葡萄牙语、日语（共7种语言）。缩略图AI文生图提示词不翻译。
    *   提供 AI 翻译校准评分（准确性、流畅性、文化适应性 -> 等级+文字说明）和重新翻译功能。
    *   最终**导出7份独立的MD格式文件**。每份文件包含：
        *   分镜口播文案中英对照列表。
        *   汇总的翻译后口播文案。
        *   翻译后的视频标题、描述、原文缩略图提示词、翻译后的缩略图文字。
8.  **新任务 (步骤 6)**: 提供清除缓存（不清除API配置）并开始新任务的按钮。

## 3. AI 模型与提示词

*   **模型交互**: 支持用户为每个主要 AI 任务步骤选择不同的、兼容 OpenAI API 格式的模型。
*   **提示词管理**:
    *   通过 `prompts.yaml` 文件进行管理，用户可编辑。
    *   提示词内容支持 Markdown 格式，增强可读性和表达力。
    *   按功能模块（如大纲生成、翻译等）组织。
    *   模块内可为不同模型定义特定的提示词和可选的默认参数（如 `temperature`）。API 调用参数主要由用户在 UI 上按需配置。

## 4. 数据流与持久化

*   **Session State**: 在 Streamlit 应用的单次会话中，所有生成的数据（大纲、脚本、分镜、元数据等）将保存在 `st.session_state` 中，并在步骤间自动传递。
*   **文件导入/导出**:
    *   分镜脚本和视频元数据可导出为 JSON 文件，作为用户备份和跨会话恢复工作的手段。
    *   翻译结果导出为多个 MD 文件。
    *   后续步骤（如图生视频、翻译）在需要时可以导入这些 JSON 文件来恢复工作。

## 5. 开发阶段计划

**Phase 1: 项目设置与基础架构**
    1. 项目结构搭建 (`app.py`, `prompts.yaml`, `utils/`, `requirements.txt`)。
    2. API 配置界面 (UI, 模型选择, `st.session_state` 存储)。
    3. 核心 AI 调用逻辑封装 (通用 API 调用函数)。
    4. Streamlit 页面导航/多页面结构。

**Phase 2: 核心脚本生成流程**
    1. 大纲生成模块 (UI, AI 调用, 评分, `st.session_state` 数据管理)。
    2. 口播稿生成模块 (UI, AI 调用, 评分, `st.session_state` 数据管理)。
    3. 分镜脚本生成模块 (UI, AI 调用, 表格编辑, JSON 导出, `st.session_state` 数据管理)。

**Phase 3: 扩展功能与导出**
    1. 视频元数据生成模块 (UI, AI 调用, `st.session_state` 数据管理, 可选导出)。
    2. 图生视频提示词生成模块 (UI, 图片上传, AI 调用, 分镜JSON导入, `st.session_state` 数据管理)。
    3. 翻译模块 (UI, AI 调用, 评分, MD导出, 分镜/元数据JSON导入, `st.session_state` 数据管理)。

**Phase 4: 完善与收尾**
    1. “新任务”按钮逻辑。
    2. 全面错误处理与用户反馈机制。
    3. UI/UX 优化 (加载提示, 流程引导)。
    4. 代码整理、注释、README。
    5. 测试 (单元测试、集成测试)。

## 6. 技术栈与关键库

*   **UI**: Streamlit
*   **AI API**: OpenAI (或任何兼容 OpenAI API 格式的服务)
*   **HTTP Client**: `openai` Python library
*   **YAML Parsing**: PyYAML
*   **Data Handling**: Pandas (可选, 用于表格数据处理)

## 7. 用户界面注意事项

*   每个 AI 生成步骤后，提供清晰的预览、编辑、重新生成选项。
*   AI 评分反馈应直接展示给用户。
*   允许用户查看原始的 AI 请求内容（例如，在一个可展开的区域内）。
*   在长时间操作时提供加载指示。
*   确保导入/导出功能易于使用。