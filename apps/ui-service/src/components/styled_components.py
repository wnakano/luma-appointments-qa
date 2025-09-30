import streamlit as st
from streamlit.components.v1 import html as st_html
from datetime import date, datetime
from typing import Optional
import textwrap

from styles.design_system import DesignSystem


def H(s: str) -> str:
    """Dedent + strip helper to avoid Markdown code blocks from leading spaces."""
    return textwrap.dedent(s).strip()


class StyledComponents:
    """Reusable styled components for the chatbot interface"""

    @staticmethod
    def render_header():
        """Render the application header with design system styling
        Use components.html so Markdown never treats it as code.
        """
        # Prefer a dedicated header_html() if your DesignSystem has it.
        # Fallback to the header component string.
        try:
            header = DesignSystem.header_html()  # type: ignore[attr-defined]
        except Exception:
            header = DesignSystem.get_component_html("header")
        # Render with components.html (no Markdown parsing)
        # center header horizontally & vertically inside the component iframe
        centered_html = f'''
        
            {header}
        
        '''
        st_html(centered_html, height=220)

    @staticmethod
    def render_logo(size: str = "32px", css_class: str = "app-logo"):
        """Render the company logo with design system styling"""
        st.markdown(
            DesignSystem.get_logo_component(size, css_class),
            unsafe_allow_html=True
        )

    @staticmethod
    def get_logo_html(size: str = "32px"):
        """Get logo HTML for inline usage"""
        return DesignSystem.get_component_html("logo", size=size)

    @staticmethod
    def render_form_container(title: str, icon: str = "📝"):
        """Context manager for styled form containers"""
        class FormContainer:
            def __init__(self, title, icon):
                self.title = title
                self.icon = icon

            def __enter__(self):
                st.markdown(
                    H(f"""
                    <div class="input-form">
                        <div class="form-title">
                            {self.icon} {self.title}
                        </div>
                    </div>
                    """),
                    unsafe_allow_html=True
                )
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return FormContainer(title, icon)

    @staticmethod
    def show_success_message(message: str):
        """Display a success message with design system styling"""
        st.markdown(
            DesignSystem.get_component_html("success_message", message),
            unsafe_allow_html=True
        )

    @staticmethod
    def show_error_message(message: str):
        """Display an error message with design system styling"""
        st.markdown(
            DesignSystem.get_component_html("error_message", message),
            unsafe_allow_html=True
        )

    @staticmethod
    def show_warning_message(message: str):
        """Display a warning message with design system styling"""
        st.markdown(
            DesignSystem.get_component_html("warning_message", message),
            unsafe_allow_html=True
        )

    @staticmethod
    def show_loading(message: str = "Processing..."):
        """Display a loading indicator with design system styling"""
        st.markdown(
            DesignSystem.get_component_html("loading", message),
            unsafe_allow_html=True
        )


class StyledUserInputCollector:
    """Enhanced user input collector with design system styling"""

    @staticmethod
    def collect_full_name() -> Optional[str]:
        """Collect user's full name with styled form"""
        # Initialize session state for this form
        if "full_name_submitted" not in st.session_state:
            st.session_state.full_name_submitted = False
            
        logo = DesignSystem.get_logo_png()
        st.markdown(
            H(f"""
            <div class="input-form">
            <div class="form-title" style="display:flex;align-items:center;justify-content:center;gap:0.75rem;">
                <div class="app-logo" style="margin:0;display:flex;align-items:center;">{logo}</div>
                <div style="font-weight:600;">Please provide your full name</div>
            </div>
            </div>
            """),
            unsafe_allow_html=True,
            # width="content"
        )

        # Add button styling
        st.markdown("""
            <style>
            div.stFormSubmitButton > button {
                background-color: #1a4fa0 !important;
                color: white !important;
                font-weight: 600 !important;
                border: none !important;
            }
            div.stFormSubmitButton > button:hover:not(:disabled) {
                background-color: #0f3870 !important;
                color: white !important;
            }
            div.stFormSubmitButton > button:disabled {
                background-color: #94a3b8 !important;
                color: #e2e8f0 !important;
                cursor: not-allowed !important;
                opacity: 0.6 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # JavaScript to disable button on click
        st_html("""
            <script>
            (function() {
                const disableButton = () => {
                    const buttons = window.parent.document.querySelectorAll('button[kind="formSubmit"]');
                    buttons.forEach(button => {
                        if (button.innerText.includes('Submit Name') && !button.dataset.listenerAdded) {
                            button.dataset.listenerAdded = 'true';
                            button.addEventListener('click', function(e) {
                                setTimeout(() => {
                                    this.disabled = true;
                                    this.style.backgroundColor = '#94a3b8';
                                    this.style.color = '#e2e8f0';
                                    this.style.cursor = 'not-allowed';
                                    this.style.opacity = '0.6';
                                }, 10);
                            }, { once: false });
                        }
                    });
                };
                
                // Try multiple times to catch the button
                disableButton();
                setTimeout(disableButton, 100);
                setTimeout(disableButton, 300);
                setTimeout(disableButton, 500);
            })();
            </script>
        """, height=0)
        
        with st.form("full_name_form", clear_on_submit=True):
            
            full_name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
                help="Please enter your complete name as it appears on official documents",
                label_visibility="collapsed",
                width=600
            )

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button(
                    "Submit Name", 
                    use_container_width=True
                )

            if submitted:
                if full_name and len(full_name.strip()) >= 2:
                    st.session_state.full_name_submitted = True
                    StyledComponents.show_success_message(f"Thank you, {full_name.strip()}!")
                    return full_name.strip()
                else:
                    StyledComponents.show_error_message("Please enter a valid full name (at least 2 characters)")
                    return None
        return None

    @staticmethod
    def collect_mobile_number() -> Optional[str]:
        """Collect user's mobile number with styled form"""
        # Initialize session state for this form
        if "mobile_number_submitted" not in st.session_state:
            st.session_state.mobile_number_submitted = False
            
        logo = DesignSystem.get_logo_png()
        st.markdown(
            H(f"""
            <div class="input-form">
            <div class="form-title" style="display:flex;align-items:center;justify-content:center;gap:0.75rem;">
                <div class="app-logo" style="margin:0;display:flex;align-items:center;">{logo}</div>
                <div style="font-weight:600;">Please provide your mobile number</div>
            </div>
            </div>
            """),
            unsafe_allow_html=True
        )

        # Add button styling
        st.markdown("""
            <style>
            div.stFormSubmitButton > button {
                background-color: #1a4fa0 !important;
                color: white !important;
                font-weight: 600 !important;
                border: none !important;
            }
            div.stFormSubmitButton > button:hover:not(:disabled) {
                background-color: #0f3870 !important;
                color: white !important;
            }
            div.stFormSubmitButton > button:disabled {
                background-color: #94a3b8 !important;
                color: #e2e8f0 !important;
                cursor: not-allowed !important;
                opacity: 0.6 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # JavaScript to disable button on click
        st_html("""
            <script>
            (function() {
                const disableButton = () => {
                    const buttons = window.parent.document.querySelectorAll('button[kind="formSubmit"]');
                    buttons.forEach(button => {
                        if (button.innerText.includes('Submit Number') && !button.dataset.listenerAdded) {
                            button.dataset.listenerAdded = 'true';
                            button.addEventListener('click', function(e) {
                                setTimeout(() => {
                                    this.disabled = true;
                                    this.style.backgroundColor = '#94a3b8';
                                    this.style.color = '#e2e8f0';
                                    this.style.cursor = 'not-allowed';
                                    this.style.opacity = '0.6';
                                }, 10);
                            }, { once: false });
                        }
                    });
                };
                
                // Try multiple times to catch the button
                disableButton();
                setTimeout(disableButton, 100);
                setTimeout(disableButton, 300);
                setTimeout(disableButton, 500);
            })();
            </script>
        """, height=0)
        
        with st.form("mobile_form", clear_on_submit=True):
            mobile = st.text_input(
                "Mobile Number",
                placeholder="+1 (555) 123-4567",
                help="Enter your mobile number with country code for best results",
                label_visibility="collapsed",
                width=600
            )

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button(
                    "Submit Number", 
                    use_container_width=True
                )

            if submitted:
                import re
                cleaned_mobile = re.sub(r'[^\d+]', '', mobile)

                if re.match(r'^\+?[1-9][0-9]{7,14}$', cleaned_mobile):
                    if not cleaned_mobile.startswith('+'):
                        cleaned_mobile = '+1' + cleaned_mobile  # default if no country code
                    st.session_state.mobile_number_submitted = True
                    StyledComponents.show_success_message("Mobile number saved successfully!")
                    return cleaned_mobile
                else:
                    StyledComponents.show_error_message("Please enter a valid mobile number (e.g., +1234567890)")
                    return None
        return None

    @staticmethod
    def collect_birthday() -> Optional[date]:
        """Collect user's birthday with styled form"""
        # Initialize session state for this form
        if "birthday_submitted" not in st.session_state:
            st.session_state.birthday_submitted = False
            
        logo = DesignSystem.get_logo_png()
        st.markdown(
            H(f"""
            <div class="input-form">
            <div class="form-title" style="display:flex;align-items:center;justify-content:center;gap:0.75rem;">
                <div class="app-logo" style="margin:0;display:flex;align-items:center;">{logo}</div>
                <div style="font-weight:600;">Please provide your date of birth</div>
            </div>
            </div>
            """),
            unsafe_allow_html=True
        )

        # Add button styling
        st.markdown("""
            <style>
            div.stFormSubmitButton > button {
                background-color: #1a4fa0 !important;
                color: white !important;
                font-weight: 600 !important;
                border: none !important;
            }
            div.stFormSubmitButton > button:hover:not(:disabled) {
                background-color: #0f3870 !important;
                color: white !important;
            }
            div.stFormSubmitButton > button:disabled {
                background-color: #94a3b8 !important;
                color: #e2e8f0 !important;
                cursor: not-allowed !important;
                opacity: 0.6 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # JavaScript to disable button on click
        st_html("""
            <script>
            (function() {
                const disableButton = () => {
                    const buttons = window.parent.document.querySelectorAll('button[kind="formSubmit"]');
                    buttons.forEach(button => {
                        if (button.innerText.includes('Submit Date') && !button.dataset.listenerAdded) {
                            button.dataset.listenerAdded = 'true';
                            button.addEventListener('click', function(e) {
                                setTimeout(() => {
                                    this.disabled = true;
                                    this.style.backgroundColor = '#94a3b8';
                                    this.style.color = '#e2e8f0';
                                    this.style.cursor = 'not-allowed';
                                    this.style.opacity = '0.6';
                                }, 10);
                            }, { once: false });
                        }
                    });
                };
                
                // Try multiple times to catch the button
                disableButton();
                setTimeout(disableButton, 100);
                setTimeout(disableButton, 300);
                setTimeout(disableButton, 500);
            })();
            </script>
        """, height=0)
        
        with st.form("birthday_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                month = st.selectbox(
                    "Month",
                    range(1, 13),
                    format_func=lambda x: datetime(2000, x, 1).strftime('%B'),
                    index=0
                )

            with col2:
                day = st.selectbox("Day", range(1, 32), index=0)

            with col3:
                current_year = datetime.now().year
                year = st.selectbox(
                    "Year",
                    range(current_year - 100, current_year + 1),
                    index=50
                )

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button(
                    "Submit Date", 
                    use_container_width=True
                )

            if submitted:
                try:
                    birth_date = date(year, month, day)
                    today = date.today()
                    age = today.year - birth_date.year - (
                        (today.month, today.day) < (birth_date.month, birth_date.day)
                    )
                    dob = f"{year}-{month}-{day}"

                    if 0 <= age <= 120:
                        st.session_state.birthday_submitted = True
                        StyledComponents.show_success_message(
                            f"Date of birth saved: {birth_date.strftime('%B %d, %Y')}"
                        )
                        return dob
                    else:
                        StyledComponents.show_error_message("Please enter a valid date of birth")
                        return None
                except ValueError:
                    StyledComponents.show_error_message("Please enter a valid date")
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
