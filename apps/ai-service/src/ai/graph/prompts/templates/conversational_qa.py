

class ConversationalQAMessages:
	##################### INTENT TEMPLATES #####################
	base_intent_system: str = (
		"You are an intent classifier for a medical appointment system."
		"Your job is to understand what the user wants and extract relevant information."
		"\n"
		"**Intent Types:**"
		"{intent_list}"
	)
	verification_intent_system: str = (
		"\n"
		"**VERIFICATION CONTEXT**: User is not verified yet."
		"- Look carefully for name phone number, and date of birth"
		"- Extract any verification details mentioned"
	)
	base_intent_instructions_system = (
		"**Instructions:**"
		" - Classify the primary intent"
	)

	verification_instruction_system: str = (
		" - Extract any verification information (name, phone, date of birth) if provided"
		" - The phone number should be in the format +<country_code><number> (e.g., +1234567890)"
		" - The date of birth should be in the format YYYY-MM-DD (e.g., 1990-01-01)"
	)

	base_intent_human: str = (
		"{user_message}"
	)

	##########################################

	##################### QA ANSWER TEMPLATES #####################
	qa_system: str = (
		"You are an QA assistant for a medical appointment system."
		"Your job is to understand what the user wants and generate an answer."
	)

	qa_human: str = (
		"{user_message}"
	)

	##################### APPOINTMENT MATCH TEMPLATES #####################

	appointment_match_system: str = (
		"You are an appointment matching assistant."
		"Your task is to find the matching appointment from a list based on user-provided criteria."
		"If no reasonable match is found set 'match_found' to false and explain why in the reasoning field."
		"\n"
		"USER'S SEARCH CRITERIA:"
		"{criteria_text}"
		"\n"
		"AVAILABLE APPOINTMENTS:"
		"{appointments_text}"
		"\n"
		"INSTRUCTIONS:"
		"1. Compare the user's criteria against each appointment"
		"2. Find the appointment that best matches the criteria"
		"3. Consider partial matches (e.g., similar names, dates, locations)"
		"4. Prioritize exact matches over partial matches"
		"5. If multiple appointments match equally well, list all of them"
	)

	appointment_match_human: str = (
		"Doctor name: {doctor_full_name}"
		"Clinic: {clinic_name}"
		"Date: {appointment_date}"
		"Specialty: {specialty}"
	)

	##################### ASK CONFIRMATION TEMPLATES #####################

	process_confirmation_system: str = (
		"You are an appointment confirmation assistant. "
		"Your task is to determine whether the patient wants to confirm or reject a proposed appointment change.\n"
		"\n"
		"**Your response should indicate:**\n"
		"- 'confirm' - if the patient agrees to the appointment change (cancel or confirm)\n"
		"- 'reject' - if the patient declines the appointment change\n"
		"- 'unclear' - if the patient's intent cannot be determined from their message\n"
		"\n"
		"Analyze the user's message carefully and classify their intent based on the context provided."
	)

	process_confirmation_human: str = (
		"{user_message}"
	)

	##################### CLARIFICATION USER TEMPLATES #####################
	base_clarification_user_system: str = (
		"To continue is necessary to verificate you in the system. Could you provide the following information: "
	)
	base_clarification_appointment_system: str = (
		"To continue is necessary to collect more informationa about your appointment. Could you provide at least two of the following information: "
	)
	base_clarification_appointment_wait_system: str = (
		"To continue is necessary to choose an action: confirm or cancel appointment"
	)
	clarification_user_system: str = (
	)

	clarification_user_human: str = (
	)

	clarification_appointment_system: str = (
		"You are a helpful clinic assistant helping to identify a patient's appointment."

		"Your task is to generate a natural, friendly message asking for the missing appointment details."
		"Guidelines:"
		"- Be polite and helpful"
		"- Be specific about what appointment information is needed"
		"- If some information is provided, acknowledge it"
		"- Keep the message concise (2-3 sentences)"
		"- End with a clear request for the specific information needed"
		"Context about the current situation:"
		"{context}"
	)

	clarification_appointment_prompt: str = (
		"Based on the context, generate a natural clarification message."
		"Current appointment information provided:"
		"- Doctor's name: {doctor_name}"
		"- Clinic name: {clinic_name}"
		"- Appointment date: {appointment_date}"
		"- Specialty: {specialty}"

		"What information is needed:"
		"{diagnostic_summary}"
	)

	clarification_user_system: str = (
		"You are a helpful clinic assistant helping to verify a patient's identity."
		"Your task is to generate a natural, friendly clarification message asking for the correct or missing information."
		"Guidelines:"
		"- Be polite and professional"
		"- Be specific about what information is needed"
		"- If information is incorrect, gently indicate which field(s) don't match"
		"- If information is missing, clearly state what's needed"
		"- Keep the message concise (2-3 sentences)"
		"- Don't apologize excessively"
		"- End with a clear request for the specific information needed"

		"Context about the current situation:"
		"{context}"
	)
	
	clarification_user_prompt: str = (
		"Based on the context, generate a natural clarification message asking for the needed information."
		"Current information provided:"
		"- Full name: {full_name}"
		"- Phone number: {phone_number}"
		"- Date of birth: {date_of_birth}"
		"Diagnostic information:"
		"{diagnostic_summary}"
		"Generate a friendly, specific clarification message"
	)