import streamlit as st
from datetime import date, datetime
import re
from typing import Optional, Dict, Any


class UserInputCollector:
    @staticmethod
    def collect_full_name() -> Optional[str]:
        """Collect user's full name with validation"""
        with st.form("full_name_form", clear_on_submit=True):
            st.write("**Please provide your full name:**")
            full_name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
                help="Please enter your first and last name"
            )
            
            submitted = st.form_submit_button("Submit", use_container_width=True)
            
            if submitted:
                if full_name and len(full_name.strip()) >= 2:
                    return full_name.strip()
                else:
                    st.error("Please enter a valid full name (at least 2 characters)")
                    return None
        return None
    
    @staticmethod
    def collect_mobile_number() -> Optional[str]:
        """Collect user's mobile number with validation"""
        with st.form("mobile_form", clear_on_submit=True):
            st.write("**Please provide your mobile number:**")
            mobile = st.text_input(
                "Mobile Number",
                placeholder="+1234567890 or 1234567890",
                help="Enter your mobile number with or without country code"
            )
            
            submitted = st.form_submit_button("Submit", use_container_width=True)
            
            if submitted:
                # Clean the input
                cleaned_mobile = re.sub(r'[^\d+]', '', mobile)
                
                # Validate format
                if re.match(r'^\+?[1-9][0-9]{7,14}$', cleaned_mobile):
                    # Ensure it starts with + for E.164 format
                    if not cleaned_mobile.startswith('+'):
                        cleaned_mobile = '+1' + cleaned_mobile  # Default to US if no country code
                    return cleaned_mobile
                else:
                    st.error("Please enter a valid mobile number")
                    return None
        return None
    
    @staticmethod
    def collect_birthday() -> Optional[date]:
        """Collect user's birthday with validation"""
        with st.form("birthday_form", clear_on_submit=True):
            st.write("**Please provide your date of birth:**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                month = st.selectbox("Month", range(1, 13), format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
            with col2:
                day = st.selectbox("Day", range(1, 32))
            with col3:
                current_year = datetime.now().year
                year = st.selectbox("Year", range(current_year - 100, current_year + 1), index=50)
            
            submitted = st.form_submit_button("Submit", use_container_width=True)
            
            if submitted:
                try:
                    birth_date = date(year, month, day)
                    # Validate age (must be reasonable)
                    today = date.today()
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    
                    if 0 <= age <= 120:
                        return birth_date
                    else:
                        st.error("Please enter a valid date of birth")
                        return None
                except ValueError:
                    st.error("Please enter a valid date")
                    return None
        return None
    
    @staticmethod
    def needs_user_input(message: str) -> Optional[str]:
        """
        Determine if the chatbot is requesting specific user input
        Returns the type of input needed or None
        """
        message_lower = message.lower()
        
        if any(phrase in message_lower for phrase in ["full name", "your name", "what's your name"]):
            return "full_name"
        elif any(phrase in message_lower for phrase in ["mobile number", "phone number", "contact number"]):
            return "mobile_number"
        elif any(phrase in message_lower for phrase in ["birthday", "date of birth", "birth date", "when were you born"]):
            return "birthday"
        
        return None
