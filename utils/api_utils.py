import streamlit as st
from openai import OpenAI, APIConnectionError, AuthenticationError, RateLimitError, APIError
from typing import Optional, List, Dict, Any # Added for type hinting
import base64 # For image encoding

def call_openai_api(
    api_key: str,
    base_url: str,
    model: str,
    system_message: Optional[str],
    user_message_text: Optional[str], # Renamed from user_message
    image_data_base64: Optional[str] = None, # New parameter for base64 image data
    image_media_type: str = "image/jpeg", # Default media type
    temperature: float = 1,
    max_tokens: int = 5000
) -> Optional[str]: # Added return type hint
    """
    Calls an OpenAI-compatible API, potentially with image input.

    Args:
        api_key (str): The API key.
        base_url (str): The base URL for the API.
        model (str): The model name to use (should be a multimodal model if image_data is provided).
        system_message (Optional[str]): The system message content.
        user_message_text (Optional[str]): The text part of the user message.
        image_data_base64 (Optional[str]): Base64 encoded string of the image data.
        image_media_type (str): The media type of the image (e.g., "image/jpeg", "image/png").
        temperature (float): Sampling temperature.
        max_tokens (int): Maximum tokens to generate.

    Returns:
        str: The content of the assistant's response, or None if an error occurs.
    """
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        messages: List[Dict[str, Any]] = [] # Type hint for messages
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Construct user message content (text + optional image)
        user_content_parts: List[Dict[str, Any]] = []
        if user_message_text: # Ensure user_message_text is not None or empty before adding
            user_content_parts.append({"type": "text", "text": user_message_text})
        
        if image_data_base64:
            # Basic check for model compatibility, can be improved
            is_likely_multimodal = "gpt-4o" in model or "vision" in model or "gpt-4-turbo" in model
            if not is_likely_multimodal:
                 st.warning(
                    f"警告：模型 '{model}' 可能不是一个已知的多模态模型。图像可能不会被处理。"
                    "请确保您选择的模型支持图像输入。"
                )
            
            user_content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{image_media_type};base64,{image_data_base64}"}
            })

        if not user_content_parts: # If no text and no image
            st.error("错误：用户消息文本和图像数据均为空，无法构造用户消息。")
            return None
        
        messages.append({"role": "user", "content": user_content_parts})
        
        st.info(f"正在使用模型 '{model}' 调用 API (Base URL: {base_url})...")
        if image_data_base64:
            st.caption("包含图像数据进行调用。")
        
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        response_content = chat_completion.choices[0].message.content
        
        if hasattr(chat_completion, 'usage') and chat_completion.usage:
            prompt_tokens = chat_completion.usage.prompt_tokens
            completion_tokens = chat_completion.usage.completion_tokens
            total_tokens = chat_completion.usage.total_tokens
            st.caption(f"Token 使用: Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
        
        return response_content

    except AuthenticationError:
        st.error("API 认证失败：请检查您的 API Key 是否正确且有效。")
        return None
    except APIConnectionError:
        st.error("API 连接错误：无法连接到指定的 Base URL。请检查网络连接和 Base URL 是否正确。")
        return None
    except RateLimitError:
        st.error("API 请求频率超限：请稍后再试或检查您的账户用量限制。")
        return None
    except APIError as e:
        st.error(f"API 返回错误：{e}")
        return None
    except Exception as e:
        st.error(f"调用 API 时发生未知错误：{e}")
        return None

def get_prompt_content(task_name: str, model_name: str, prompts_config: dict, variable_dict: dict = None):
    """
    Retrieves and formats system and user messages for a given task and model.

    Args:
        task_name (str): The name of the task (e.g., "outline_generation").
        model_name (str): The name of the selected model.
        prompts_config (dict): The loaded prompts configuration (from prompts.yaml).
        variable_dict (dict, optional): Dictionary of variables to format into the user message.

    Returns:
        tuple: (system_message, formatted_user_message_text, parameters) or (None, None, None) if not found.
               Note: formatted_user_message_text is the text part, image data is handled separately.
    """
    if not prompts_config or task_name not in prompts_config:
        st.error(f"错误：在 prompts.yaml 中未找到任务 '{task_name}' 的提示词配置。")
        return None, None, None

    task_prompts = prompts_config[task_name]
    
    prompt_details = task_prompts.get(model_name)

    if not prompt_details:
        # Try to get the "default" prompt set for the task
        prompt_details = task_prompts.get("default")

    if not prompt_details:
        # If specific model and "default" are not found,
        # try to find *any* available model prompt within the task
        # This is a fallback for tasks like image_to_video_prompt_generation
        # which might only define prompts for specific capable models (e.g., gpt-4o)
        if isinstance(task_prompts, dict) and task_prompts:
            # Get the first available model configuration in the task
            first_available_model_key = next(iter(task_prompts))
            prompt_details = task_prompts.get(first_available_model_key)
            if prompt_details:
                st.info(f"提示：任务 '{task_name}' 未找到模型 '{model_name}' 或 'default' 的提示词。"
                        f"将使用该任务下找到的第一个可用模型 '{first_available_model_key}' 的提示词。")
            else: # Should not happen if task_prompts is not empty
                 st.error(f"错误：任务 '{task_name}' 配置为空或无效。")
                 return None, None, None
        else:
            st.error(f"错误：未找到任务 '{task_name}' (模型: '{model_name}' 或 default) 的具体提示词内容，且任务下无其他可用模型提示词。")
            return None, None, None

    if not prompt_details: # Final check, if still no details after fallback
        st.error(f"错误：最终未能为任务 '{task_name}' (模型: '{model_name}') 加载任何提示词。")
        return None, None, None

    system_message = prompt_details.get("system_message", "")
    user_message_template = prompt_details.get("user_message_template", "")
    parameters = prompt_details.get("parameters", {})

    formatted_user_message_text = user_message_template
    if variable_dict:
        try:
            # Only format if the template is not empty
            if user_message_template and user_message_template.strip():
                 formatted_user_message_text = user_message_template.format(**variable_dict)
            elif not user_message_template and variable_dict: # If template is empty but vars provided, it's odd
                st.caption(f"提示：任务 '{task_name}' 的用户消息模板为空，但提供了变量。变量将不会被使用。")
                formatted_user_message_text = "" # Ensure it's an empty string
            else: # Template is empty, no vars
                formatted_user_message_text = ""

        except KeyError as e:
            st.error(f"格式化用户消息时出错：模板中缺少变量 {e}。请检查 prompts.yaml 和代码。")
            return system_message, None, parameters
        except Exception as e: # Catch other formatting errors
            st.error(f"格式化用户消息时发生未知错误: {e}")
            return system_message, None, parameters


    return system_message, formatted_user_message_text, parameters