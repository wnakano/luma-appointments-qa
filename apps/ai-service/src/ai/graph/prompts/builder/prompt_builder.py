from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts import (
	PromptTemplate, 
	SystemMessagePromptTemplate, 
	HumanMessagePromptTemplate
)

from typing import (
	Any, 
	List, 
	Union
)

from .message_types import MessageTypes


class ChatPromptTemplateBuilder:
	"""
	A builder class to dynamically create a ChatPromptTemplate with customizable 
	system and human message templates.
	"""

	def __init__(self, metadata=None) -> None:
		"""
		Initialize the builder with optional metadata.

		Parameters
		----------
		metadata : dict, optional
			A dictionary containing metadata information, by default None.
		"""
		self.metadata = metadata if metadata is not None else {}
		self.messages = []

	def add_message(
		self, 
		message_type: str, 
		template: str, 
		input_variables: Union[List[str], None] = None, 
		input_types=None, 
		partial_variables=None, 
		additional_kwargs=None
		) -> None:
		"""
		Adds a message template (system or human) to the ChatPromptTemplate.

		Parameters
		----------
		message_type : str
			Type of message, either 'system' or 'human'.
		template : str
			Template string for the message.
		input_variables : list, optional
			List of input variables used in the template, by default an empty list.
		input_types : dict, optional
			Dictionary specifying the types of input variables, by default an empty dict.
		partial_variables : dict, optional
			Dictionary for any partial variables, by default an empty dict.
		additional_kwargs : dict, optional
			Additional arguments to pass to the message template, by default an empty dict.

		Raises
		------
		ValueError
			If `message_type` is not 'system' or 'human'.
		"""
		input_variables = input_variables if input_variables is not None else []
		input_types = input_types if input_types is not None else {}
		partial_variables = partial_variables if partial_variables is not None else {}
		additional_kwargs = additional_kwargs if additional_kwargs is not None else {}

		# Create the prompt template
		prompt_template = PromptTemplate(
			input_variables=input_variables,
			input_types=input_types,
			partial_variables=partial_variables,
			template=template
		)

		if message_type == MessageTypes.SYSTEM:
			message = SystemMessagePromptTemplate(prompt=prompt_template, additional_kwargs=additional_kwargs)
		elif message_type == MessageTypes.HUMAN:
			message = HumanMessagePromptTemplate(prompt=prompt_template, additional_kwargs=additional_kwargs)
		else:
			raise ValueError("message_type must be either 'system' or 'human'")

		self.messages.append(message)

	def build(self, input_variables: List[str]) -> ChatPromptTemplate:
		"""
		Builds and returns the ChatPromptTemplate with the defined messages.

		Parameters
		----------
		input_variables : list
			List of input variables for the ChatPromptTemplate.

		Returns
		-------
		ChatPromptTemplate
			An instance of ChatPromptTemplate with the configured messages and metadata.
		"""
		prompt_template = ChatPromptTemplate(
			input_variables=input_variables,
			messages=self.messages,
			metadata=self.metadata
		)
	
		self.messages.clear()

		return prompt_template

