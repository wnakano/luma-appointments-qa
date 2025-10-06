

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