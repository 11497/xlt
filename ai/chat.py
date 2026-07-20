from typing import List

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI

from config.ai_config import BASE_URL, CHAT_CONFIG, SUMMARY_PROMPT


class ChatService:
    """聊天服务封装（基于 ChatOpenAI）"""

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
        :param chat_model: 聊天模型名称
        :param base_url: API基础URL
        :param temperature: 采样温度
        :param max_tokens: 最大生成token数
        :param top_p: 核采样概率阈值
        :param frequency_penalty: 频率惩罚系数
        :param presence_penalty: 存在惩罚系数
        """
        self.llm = ChatOpenAI(
            model=chat_model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )

    def send_message(self, messages: List[BaseMessage]) -> str:
        """
        向AI发送消息并获取完整回复
        :param messages: LangChain消息对象列表，如 [SystemMessage(...), HumanMessage(...)]
        :return: AI回复内容字符串
        """
        response = self.llm.invoke(messages)
        print("messages:")
        for msg in messages:
            print(msg)
        return response.content.strip()

    def summarize_conversation(self, messages: List[BaseMessage]) -> str:
        """
        总结对话历史作为会话标题
        :param messages: 消息历史列表，格式: [{"role": "user/assistant/system", "content": "..."}]
        :return: 总结内容字符串
        """
        # 将 BaseMessage 列表转换为 prompt 所需的对话文本格式
        conversation_text = "\n".join(
            [f"{m.type}: {m.content}" for m in messages]
        )

        # 使用 ai_config 中预定义的 SUMMARY_PROMPT 填充对话内容
        prompt = SUMMARY_PROMPT.format(conversation=conversation_text)

        response = self.llm.invoke([HumanMessage(content=prompt)])

        return response.content.strip()