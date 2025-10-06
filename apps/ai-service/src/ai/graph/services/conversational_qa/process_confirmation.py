from langchain.prompts import PromptTemplate
from typing import Optional

from ...types.conversational_qa import ConfirmationIntent
from ...models.conversational_qa import AppointmentConfirmationResponse
from ...prompts.templates.conversational_qa import ConversationalQAMessages
from ..llm import LLMService
from utils import Logger

logger = Logger(__name__)


class ProcessConfirmationService(LLMService):
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temp: float = 0.0,
    ) -> None:
        super().__init__(model=model, temp=temp)

    def run(
        self,
        user_message: str,
    ) -> AppointmentConfirmationResponse:
        try:
            logger.info("[SERVICE] ProcessConfirmationService")

            if not user_message or not user_message.strip():
                logger.warning("Empty user message, returning fallback")
                return self._get_fallback_response(user_message)

            template = self._build_prompt_template()

            chain = self.build_structured_chain(
                template=template,
                schema=AppointmentConfirmationResponse
            )

            result: AppointmentConfirmationResponse = chain.invoke({
                "user_message": user_message
            })

            logger.info(
                f" ... Confirmation intent: {result.intent} "
                f"(confidence: {result.confidence:.2f})"
            )

            if result.extracted_concerns:
                logger.info(f" ... Extracted concerns: {result.extracted_concerns}")

            return result

        except Exception as e:
            logger.error(
                f"[SERVICE] ProcessConfirmationService ERROR: {e}",
                exc_info=True
            )
            return self._get_fallback_response(user_message)

    def _build_prompt_template(self) -> PromptTemplate:
        system_prompt = ConversationalQAMessages.process_confirmation_system
        human_prompt = ConversationalQAMessages.process_confirmation_human

        template = self.build_prompt_template(
            system_prompt=system_prompt,
            human_prompt=human_prompt,
            system_input_variables=[],
            human_input_variables=["user_message"]
        )

        return template

    def _get_fallback_response(
        self,
        user_message: str
    ) -> AppointmentConfirmationResponse:
        logger.warning("Returning fallback response: UNCLEAR")

        return AppointmentConfirmationResponse(
            intent=ConfirmationIntent.UNCLEAR,
            confidence=0.0,
            reasoning="Unable to process confirmation due to service error or unclear response",
            extracted_concerns=""
        )