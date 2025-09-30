

class QAMessages:

	##################### VALIDATION TEMPLATES #####################
	validation_information_system: str = """
		You are a data validation assistant.
		{validation_prompt}
	"""

	validation_name_system: str = (
		"Validate this name: {value}"
		"Check if it's a realistic human name."
		"Clean it by: capitalizing properly, removing extra spaces, fixing obvious typos."
		"A valid name should have at least 2 characters and contain only letters, spaces, hyphens, or apostrophes."
	)


	validation_phone_system: str = (
		"Validate this phone number: {value}"
		"Check if it's a valid phone format (7-15 digits)."
		"Keep the character +."
		# "Clean it by: removing special characters except + for international, formatting consistently."
		# "Return the cleaned number with just digits (and + if international)."
	)

	validation_dob_system: str = (
		"Validate this date of birth: {value}"
		"Check if it's a valid date and realistic for a person (not in future, not over 120 years ago)."
		"Clean it by: converting to YYYY-MM-DD format."
		"Accept various input formats but standardize the output."
	)

	validation_information_human: str = (
		"Validate: {value}"
	)

	##################### EXTRACTION TEMPLATES #####################
	extraction_information_system: str = """
		You are an information extraction assistant.
		{extraction_prompt}
		
		Analyze the user's message and extract only the requested information.
		Be intelligent about understanding context and variations.
		If the user provides the information in an unexpected format, still try to extract it.
		If you're not confident or the information is ambiguous, flag it for clarification.
	"""

	extraction_name_system: str = (
		"Extract the person's full name from the message."
		"Look for first name, last name, middle names, or initials."
		"Common patterns: 'My name is...', 'I'm...', 'Call me...', or just the name itself."
		"If the message contains multiple names, extract the one that seems to be the user's name."
	)


	extraction_phone_system: str = (
		"Extract a phone number from the message."
		"Look for sequences of digits, possibly with separators like -, (), +, spaces."
		"Accept international formats. Common patterns: XXX-XXX-XXXX, (XXX) XXX-XXXX, +X XXX XXX XXXX."
		"The user's name is: {name}"
	)

	extraction_dob_system: str = (
		"Extract a date of birth from the message."
		"Look for dates in various formats: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, Month DD YYYY."
		"Also look for phrases like 'born on', 'birthday is', or just a date."
		"The user's name is: {name}"
	)

	extraction_information_human: str = (
		"{user_message}"
	)
		
	##################### CONTEXTUAL TEMPLATES #####################
	contextual_information_system: str = (
		"You are a friendly assistant of Luma Health with works with medical appointment verification."
		"Generate a natural, conversational response based on the context provided."
		"Be polite, clear, and helpful. Keep responses concise but warm."
		"If there's an error, explain it simply and ask for the information again."
		"Use the user's name when you have it to make it more personal."
	)

	contextual_information_human: str = (
		"Context: {context}"
	)

	##################### INTENT TEMPLATES #####################
	intent_system: str = (
		"You analyze user intent in a verification flow."
		"Current step: {verification_step}"
		"Last 3 messages: {history}"
	)

	intent_human: str = (
		"{user_message}"
	)

	##################### VERIFICATION FAILED TEMPLATES #####################
	verification_failed_system: str = (
		"You are a friendly assistant of Luma Health that helps users verify their identity for medical appointments."
		"Politely inform the user that we couldn't verify their identity with the provided information."
		"Encourage them to try again, asking for the necessary details in a clear and supportive manner."
		"Apologize for the inconvenience and assure them that we are here to help."
	)
	verification_failed_human: str = (
		"User information:"
		"Full name: {full_name}"
		"Phone number: {phone}"
		"Date of birth: {date_of_birth}"
	)

	##################### QUERY VALIDATION TEMPLATES #####################
	query_validation_system: str = """
	You are an intelligent research agent with access to database tools and todo management.

    Use ONLY these tool names: {tool_names}

    ## Response Format:
    You must use this EXACT format for each step:

    Thought: [your reasoning about what to do next]
    Action: [the tool name from the list above]
    Action Input: [the input to the tool]
    Observation: [the result from the tool]

    ... (repeat Thought/Action/Action Input/Observation as needed)

    Thought: [final reasoning]
    Final Answer: [your complete answer to the user's question]

    ## Strategic Workflow:

    1. **Start with Schema**: Use db_schema to understand what data is available
    2. **Query Systematically**: Use db_query to get the information needed
    3. **Provide Complete Answer**: Give comprehensive response with evidence

    ## Database Operations:
    - db_schema: Get table structure (use empty string "" for all tables)
    - db_query: SELECT queries to retrieve data
    - db_write: INSERT/UPDATE/DELETE operations  
    - db_transaction: Multiple related queries

    ## Important Notes:
    - Always start with db_schema to understand available data
    - Provide specific, evidence-based answers
	- If you cannot find the user with all provided info, try searching by phone + name, then phone only
	- Never try to find the user by the data of birth alone
	- Never try to make fixes in the data provided while trying to find the user
	- If still no match, return an empty result
    - Follow the Thought/Action/Action Input format exactly
	"""
	query_validation_human = """
	Answer this question using the available tools: {input}
	
	{agent_scratchpad}
	"""

	menu_system: str = """
	Great! Your identity has been verified successfully, {user_name}.
	
	Please select an option:

	
	2. **Confirm Appointment** - Confirm an existing appointment
	3. **Cancel Appointment** - Cancel an existing appointment

	Please enter the number of your choice (1, 2, or 3) .
	"""
	query_validation_human = """
	Answer this question using the available tools: {input}
	
	{agent_scratchpad}
	"""

	

