import streamlit as st

from datetime import datetime
from typing import Optional
from database.connection import db_manager
from database.models import (
    Conversation, 
    Message, 
    MenuChoices, 
    Patient
)
from services.chatbot_api import ChatbotAPIClient
from components.styled_components import (
    StyledUserInputCollector, 
    StyledComponents
)
from styles.design_system import DesignSystem
from constants import Constants

from utils import (
    Logger, 
    UUIDHandler
)

logger = Logger(__name__)


class ChatbotApp:
    """Main chatbot application class that handles the entire chat interface"""
    
    def __init__(self):
        """Initialize the chatbot application"""
        self.configure_page()
        self.apply_styles()

        self.uuid_handler = UUIDHandler()

        self.initialize_session_state()

        self.db_manager = DatabaseManager()
        self.conversation_handler = ConversationHandler(self.db_manager)
        self.chat_interface = ChatInterface(self.conversation_handler)

        logger.info("Chatbot application is being initialized")

    def configure_page(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title=Constants.PAGE_TITLE,
            page_icon=Constants.logo_png_path,
            layout="wide",
            initial_sidebar_state="collapsed"
        )
    
    def apply_styles(self):
        """Apply design system styles"""
        st.markdown(DesignSystem.get_base_styles(), unsafe_allow_html=True)
        st.markdown(DesignSystem.apply_button_styling(), unsafe_allow_html=True)
        st.markdown(DesignSystem.apply_message_styling(), unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "conversation_id" not in st.session_state:
            st.session_state.conversation_id = str(self.uuid_handler.generate_uuid())
        if "user_id" not in st.session_state:
            st.session_state.user_id = str(self.uuid_handler.generate_uuid())
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(self.uuid_handler.generate_uuid())
        if "awaiting_input" not in st.session_state:
            st.session_state.awaiting_input = None
        if "user_data" not in st.session_state:
            st.session_state.user_data = {}
    
    def run(self):
        """Run the chatbot application"""
        try:
            self.db_manager.initialize_database()
            self.chat_interface.render()
            
        except Exception as e:
            st.error(f"Application error: {str(e)}")
            st.stop()


class DatabaseManager:
    """Handles all database operations for the chatbot"""
    def __init__(self):
        self.uuid_handler = UUIDHandler()

    def initialize_database(self):
        """Initialize database tables"""
        # try:
        #     db_manager.create_tables()
        # except Exception as e:
        #     raise Exception(f"Database initialization error: {str(e)}")
        pass

    def save_message(self, user_message: str, system_message: str, latency_ms: int, menu_choice: MenuChoices):
        """Save message to database"""
        try:
            session = db_manager.get_session()
            
            conversation = session.query(Conversation).filter_by(id=st.session_state.conversation_id).first()
            if not conversation:
                conversation = Conversation(
                    id=st.session_state.conversation_id,
                    session_id=st.session_state.session_id,
                    qa_system="Healthcare Chatbot"
                )
                session.add(conversation)
            
            message = Message(
                conversation_id=st.session_state.conversation_id,
                request_id=str(self.uuid_handler.generate_uuid()),
                user_message=user_message,
                system_message=system_message,
                latency_ms=latency_ms,
                menu_choice=menu_choice,
                completed_at=datetime.now()
            )
            
            session.add(message)
            session.commit()
            session.close()
            
        except Exception as e:
            st.error(f"Error saving to database: {str(e)}")


class ConversationHandler:
    """Handles conversation flow and message processing"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.uuid_handler = UUIDHandler()
        self.chatbot_client = ChatbotAPIClient()
    
    def display_messages(self):
        """Display all messages in the conversation with enhanced styling"""
        for message in st.session_state.messages:
            print(message)
            with st.chat_message(message["role"]):
                if message["role"] == "assistant":
                    formatted_content = self._format_assistant_message(message['content'])
                else:
                    formatted_content = message['content']
                
                st.markdown(
                    f"<div style='color: black;'>{formatted_content}</div>",
                    unsafe_allow_html=True
                )
    
    def handle_user_input_collection(self) -> Optional[str]:
        """Handle collection of specific user inputs when requested with styled forms"""
        if st.session_state.awaiting_input == "full_name":
            full_name = StyledUserInputCollector.collect_full_name()
            if full_name:
                logger.info(f"Collected full name: {full_name}")
                st.session_state.user_data["full_name"] = full_name
                st.session_state.awaiting_input = None
                return f"My full name is: {full_name}"

        elif st.session_state.awaiting_input == "mobile_number":
            mobile = StyledUserInputCollector.collect_mobile_number()
            if mobile:
                logger.info(f"Collected mobile number: {mobile}")
                st.session_state.user_data["mobile_number"] = mobile
                st.session_state.awaiting_input = None
                return f"My mobile number is: {mobile}"

        elif st.session_state.awaiting_input == "birthday":
            birthday = StyledUserInputCollector.collect_birthday()
            if birthday:
                logger.info(f"Collected birthday: {birthday}")
                st.session_state.user_data["birthday"] = birthday
                st.session_state.awaiting_input = None
                return f"My date of birth is: {birthday}"

        return None
    
    def _format_assistant_message(self, text: str) -> str:
        """Format assistant message for proper markdown rendering with preserved styling"""
        import re
        
        # Handle escaped newlines first
        text = text.replace("\\n", "\n")
        
        # Split into lines for processing
        lines = text.split("\n")
        formatted_lines = []
        
        for line in lines:
            # Skip empty lines (preserve them as-is)
            if not line.strip():
                formatted_lines.append(line)
                continue
            
            # Handle different formatting patterns
            formatted_line = self._format_line(line)
            formatted_lines.append(formatted_line)
        
        # Rejoin lines and clean up spacing
        formatted = "\n".join(formatted_lines)
        
        # Clean up excessive spacing while preserving intentional breaks
        formatted = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted)
        
        return formatted
    
    def _format_line(self, line: str) -> str:
        """Format individual line with appropriate markdown"""
        import re
        
        # Preserve leading whitespace for indentation
        leading_space = len(line) - len(line.lstrip())
        indent = line[:leading_space]
        content = line[leading_space:]
        
        # Handle bullet points with • character
        if "•" in content:
            bullet_pos = content.find("•")
            if bullet_pos == 0:
                # Bullet at start of content
                bullet_content = content[1:].strip()
                return f"{indent}- {bullet_content}"
            else:
                # Bullet with some prefix
                prefix = content[:bullet_pos]
                bullet_content = content[bullet_pos + 1:].strip()
                return f"{indent}{prefix}- {bullet_content}"
        
        # Handle bold numbered lists like "**  1. Text**" or "**1. Text**" - convert to bullet list
        bold_numbered_match = re.match(r'^\*\*\s*(\d+\.\s+.*?)\*\*', content)
        if bold_numbered_match:
            numbered_content = bold_numbered_match.group(1)
            return f"{indent}- **{numbered_content}**"
        
        # Handle regular numbered lists (e.g., "1. ", "2. ", etc.)
        number_match = re.match(r'^(\d+\.\s+)', content)
        if number_match:
            return line  # Keep numbered lists as-is, they're already markdown
        
        # Handle bold text patterns like "**text**" - clean up extra spaces
        if "**" in content:
            # Clean up extra spaces around bold text while preserving the bold formatting
            cleaned = re.sub(r'\*\*\s+', '**', content)  # Remove spaces after opening **
            cleaned = re.sub(r'\s+\*\*', '**', cleaned)   # Remove spaces before closing **
            return f"{indent}{cleaned}"
        
        # Handle patterns like "Do you want to:" followed by options
        if content.endswith(":") and any(keyword in content.lower() for keyword in ["do you want", "choose", "select", "options", "regarding"]):
            return line  # Keep option headers as-is
        
        # Default: return the line unchanged
        return line
    
    def process_user_message(self, prompt: str):
        """Process user message and get chatbot response"""
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt, width="content")
        
        with st.chat_message("assistant", avatar=None, width="content"):
            with st.spinner(""):
                st.markdown(
                    "<span style='color: black; font-weight: bold;'>Thinking...</span>",
                    unsafe_allow_html=True,
                    width="content"
                )
                context = {
                    "user_data": st.session_state.user_data,
                    "conversation_history": st.session_state.messages[-5:]  # Last 5 messages for context
                }
                
                response = self.chatbot_client.send_message(
                    request_id=self.uuid_handler.generate_uuid(),
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id,
                    message=prompt,
                    conversation_context=context
                )
                logger.info(f"response = {response}")
                
                if "error" in response:
                    assistant_message = response["message"]
                    menu_choice = MenuChoices.ROUTING
                else:
                    assistant_message = response.get("system_answer", "I'm sorry, I didn't understand that.")
                    menu_choice = MenuChoices.ROUTING
                    
                # Render assistant message preserving markdown styling and line breaks

                formatted = self._format_assistant_message(assistant_message)

                st.markdown(
                    f"<div style='color: black;'>{formatted}</div>", 
                    unsafe_allow_html=True, 
                    width="content"
                )
                
                # Save to database
                # self.db_manager.save_message(
                #     user_message=prompt,
                #     system_message=assistant_message,
                #     latency_ms=response.get("latency_ms", 0),
                #     menu_choice=menu_choice
                # )
        
        # Add assistant message to chat
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        
        # Check if chatbot is requesting specific input
        input_needed = StyledUserInputCollector.needs_user_input(assistant_message)
        if input_needed:
            st.session_state.awaiting_input = input_needed
            st.rerun()


class ChatInterface:
    """Handles the main chat interface rendering and interaction"""
    
    def __init__(self, conversation_handler: ConversationHandler):
        self.conversation_handler = conversation_handler
        self.uuid_handler = UUIDHandler()
    
    def render(self):
        """Render the main chat interface"""
        queued_prompt = self.render_sidebar()
        StyledComponents.render_header()
        
        # Chat container wrapper
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        if not st.session_state.messages and not st.session_state.awaiting_input:
            st.markdown(
                f"<div class=\"empty-state\">{Constants.EMPTY_STATE_MESSAGE}</div>",
                unsafe_allow_html=True,
            )

        # Display conversation
        self.conversation_handler.display_messages()
        
        if queued_prompt:
            self.conversation_handler.process_user_message(queued_prompt)
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Handle special input collection
        if st.session_state.awaiting_input:
            prompt = self.conversation_handler.handle_user_input_collection()
            if prompt:
                self.conversation_handler.process_user_message(prompt)
                st.markdown('</div>', unsafe_allow_html=True)
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            self.conversation_handler.process_user_message(prompt)
        
        st.markdown('</div>', unsafe_allow_html=True)

    def render_sidebar(self) -> Optional[str]:
        """Render the contextual sidebar controls inspired by streamlit-agent"""
        st.sidebar.title(Constants.APP_NAME)
        st.sidebar.caption(f"Version {Constants.VERSION}")
        st.sidebar.write(Constants.SIDEBAR_DESCRIPTION)

        if st.sidebar.button("Start new conversation", use_container_width=True):
            self.reset_conversation()
            st.rerun()

        st.sidebar.divider()
        st.sidebar.subheader("Session overview")
        with st.sidebar.expander("Identifiers", expanded=False):
            st.markdown(
                f"**Conversation ID**\n\n`{st.session_state.conversation_id}`"
            )
            st.markdown(f"**Session ID**\n\n`{st.session_state.session_id}`")
            st.markdown(f"**User ID**\n\n`{st.session_state.user_id}`")

        st.sidebar.subheader("Patient details shared")
        if st.session_state.user_data:
            for key, value in st.session_state.user_data.items():
                st.sidebar.markdown(f"- **{key.replace('_', ' ').title()}**: {value}")
        else:
            st.sidebar.caption("No patient information has been captured yet.")


        return None

    def reset_conversation(self):
        """Reset the chat session while preserving the configured API credentials."""
        st.session_state.messages = []
        st.session_state.awaiting_input = None
        st.session_state.user_data = {}
        st.session_state.conversation_id = str(self.uuid_handler.generate_uuid())
        st.session_state.session_id = str(self.uuid_handler.generate_uuid())
        st.session_state.user_id = str(self.uuid_handler.generate_uuid())
