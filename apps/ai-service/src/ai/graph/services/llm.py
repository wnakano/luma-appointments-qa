
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate 
from langchain_core.runnables import Runnable
from langchain.tools import Tool
from pydantic import BaseModel
from typing import (
    List, 
    Sequence
)

from ..prompts.builder.prompt_builder import (
    ChatPromptTemplateBuilder, 
    MessageTypes
)


class LLMService:
    """Thin wrapper over ChatOpenAI to manage two temperatures and structured outputs."""
    def __init__(
        self, 
        model: str = "gpt-4o-mini", 
        temp: float = 0.2, 
    ):
        self.llm = ChatOpenAI(model=model, temperature=temp)
        self.prompt_builder = ChatPromptTemplateBuilder()

    def build_structured_chain(
        self, 
        template: PromptTemplate,
        schema: BaseModel,
        use_extract: bool = True
    ) -> Runnable:
        return template | self.llm.with_structured_output(
            schema=schema
        )

    def bind_tools(self, tools: Sequence[Tool]) -> None:
        return self.llm.bind_tools(tools=tools)

    def build_chain(
        self, 
        template: PromptTemplate,
        ) -> Runnable:
        return template | self.llm
    
    def build_prompt_template(
        self, 
        system_prompt: str, 
        human_prompt: str, 
        system_input_variables: List[str] = [],
        human_input_variables: List[str] = []
    ) -> PromptTemplate:
        
        self.prompt_builder.add_message(
            message_type=MessageTypes.SYSTEM,
            template=system_prompt,
            input_variables=system_input_variables,
        )
        self.prompt_builder.add_message(
            message_type=MessageTypes.HUMAN,
            template=human_prompt,
            input_variables=human_input_variables,
        )

        input_variables = list(set(system_input_variables + human_input_variables))

        prompt = self.prompt_builder.build(input_variables=input_variables)

        return prompt

