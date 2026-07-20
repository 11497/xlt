from openai import OpenAI
from typing import List, Dict, Any, Optional, Generator

from config.ai_config import BASE_URL, CHAT_CONFIG


class ChatService:
    """聊天服务封装"""
    # TODO 敏感词过滤
    # TODO 拒绝回答配置
    # TODO 问题重写

    def __init__(
            self,
            chat_model: str = CHAT_CONFIG["CHAT_MODEL"],
            base_url: str = BASE_URL,
            temperature: float = CHAT_CONFIG["TEMPERATURE"],
            max_tokens: int = CHAT_CONFIG["MAX_TOKENS"],
            top_p: float = CHAT_CONFIG["TOP_P"],
            frequency_penalty: float = CHAT_CONFIG["FREQUENCY_PENALTY"],
            presence_penalty: float = CHAT_CONFIG["PRESENCE_PENALTY"]
    ):
        """
        初始化聊天服务
        :param chat_model: 聊天模型名称，默认取自 CHAT_CONFIG["CHAT_MODEL"]
        :param base_url: API基础URL
        :param temperature: 采样温度，控制生成随机性，默认取自 CHAT_CONFIG["TEMPERATURE"]
        :param max_tokens: 最大生成token数，默认取自 CHAT_CONFIG["MAX_TOKENS"]
        :param top_p: 核采样概率阈值，默认取自 CHAT_CONFIG["TOP_P"]
        :param frequency_penalty: 频率惩罚系数，降低重复词出现概率，默认取自 CHAT_CONFIG["FREQUENCY_PENALTY"]
        :param presence_penalty: 存在惩罚系数，鼓励模型讨论新话题，默认取自 CHAT_CONFIG["PRESENCE_PENALTY"]
        """
        self.client = OpenAI(base_url=base_url)
        self.chat_model = chat_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

    def _get_chat_params(self) -> Dict[str, Any]:
        """
        获取统一的聊天请求参数字典
        :return: 包含 temperature, max_tokens, top_p, frequency_penalty, presence_penalty 的参数字典
        """
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty
        }

    def chat_completion(
            self,
            messages: List[Dict[str, str]],
            stream: bool = False
    ) -> Any:
        """
        发送聊天请求并获取响应
        :param messages: 消息历史列表，格式: [{"role": "user/assistant/system", "content": "..."}]
        :param stream: 是否流式返回
        :return: 响应内容或流式生成器
        注: temperature, max_tokens, top_p, frequency_penalty, presence_penalty 均使用初始化时设定的 CHAT_CONFIG 配置值
        """
        response = self.client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            stream=stream,
            **self._get_chat_params()
        )

        if stream:
            return response
        return response.choices[0].message.content

    def stream_chat(
            self,
            messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """
        流式聊天，逐块返回响应
        :param messages: 消息历史列表
        :return: 生成器，逐块返回文本
        注: temperature, max_tokens, top_p, frequency_penalty, presence_penalty 均使用初始化时设定的 CHAT_CONFIG 配置值
        """
        response = self.chat_completion(messages, stream=True)
        for chunk in response:
            # 安全检查API响应数据结构
            if hasattr(chunk, 'choices') and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, 'delta') and hasattr(choice.delta, 'content') and choice.delta.content:
                    yield choice.delta.content

    def build_prompt_with_context(
            self,
            user_query: str,
            context: Optional[str] = None,
            system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        构建带有上下文的消息列表
        :param user_query: 用户查询
        :param context: 知识库上下文（可选）
        :param system_prompt: 系统提示词（可选）
        :return: 格式化的消息列表
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if context:
            context_prompt = f"参考以下上下文信息回答问题：\n{context}\n\n"
            messages.append({"role": "user", "content": context_prompt + user_query})
        else:
            messages.append({"role": "user", "content": user_query})

        return messages

    def chat_with_context(
            self,
            user_query: str,
            context: Optional[str] = None,
            system_prompt: Optional[str] = None,
            stream: bool = False
    ) -> Any:
        """
        基于上下文的聊天
        :param user_query: 用户查询
        :param context: 知识库上下文
        :param system_prompt: 系统提示词
        :param stream: 是否流式返回
        :return: 响应内容或流式生成器
        注: temperature, max_tokens, top_p, frequency_penalty, presence_penalty 均使用初始化时设定的 CHAT_CONFIG 配置值
        """
        messages = self.build_prompt_with_context(user_query, context, system_prompt)
        return self.chat_completion(messages, stream=stream)

    def stream_chat_with_context(
            self,
            user_query: str,
            context: Optional[str] = None,
            system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        流式聊天（带上下文）
        :param user_query: 用户查询
        :param context: 知识库上下文
        :param system_prompt: 系统提示词
        :return: 生成器，逐块返回文本
        注: temperature, max_tokens, top_p, frequency_penalty, presence_penalty 均使用初始化时设定的 CHAT_CONFIG 配置值
        """
        messages = self.build_prompt_with_context(user_query, context, system_prompt)
        return self.stream_chat(messages)

    def summarize_conversation(
            self,
            messages: List[Dict[str, str]]
    ) -> str:
        """
        总结对话历史
        :param messages: 消息历史列表
        :return: 总结内容
        注: temperature, max_tokens, top_p, frequency_penalty, presence_penalty 均使用初始化时设定的 CHAT_CONFIG 配置值
        """
        summary_prompt = """
请总结以下对话内容，保持简洁明了，总结后需要在2-20个字符之间：
---
{conversation}
---
总结：
"""
        conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        summary_messages = [
            {"role": "user", "content": summary_prompt.format(conversation=conversation_text)}
        ]
        return self.chat_completion(summary_messages)