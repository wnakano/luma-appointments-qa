from pathlib import Path
import textwrap
from utils import Logger
import base64

logger = Logger(__name__)


class DesignSystem:
		"""Lumahealth-inspired design system with professional healthcare aesthetics and accessibility-first approach."""

		# ---------- Helpers ----------
		@staticmethod
		def _dedent(s: str) -> str:
			"""Normalize multiline strings so they don't render as Markdown code blocks."""
			return textwrap.dedent(s).strip()

		# ---------- Assets ----------

		@staticmethod
		def get_logo_svg() -> str:
			try:
				p = Path("/app/static/logo/logo.svg")
				# p = Path("./src/static/logo/logo.svg")
				if p.exists():
					svg_content = p.read_text(encoding="utf-8")
					# Make the SVG white by adding fill="white" or stroke="white" attributes
					# This is a simple approach - for more complex SVGs, you might need more sophisticated parsing
					if 'fill=' not in svg_content and 'stroke=' not in svg_content:
						# Add white fill to the svg tag
						svg_content = svg_content.replace('<svg', '<svg fill="white"')
					return svg_content
				else:
					return '<svg width="32" height="32" viewBox="0 0 32 32" fill="white"><text y="20" fill="white">🏥</text></svg>'
			except FileNotFoundError:
				return '<svg width="32" height="32" viewBox="0 0 32 32" fill="white"><text y="20" fill="white">🏥</text></svg>'
			except Exception:
				return '<svg width="32" height="32" viewBox="0 0 32 32" fill="white"><text y="20" fill="white">Logo</text></svg>'

		@staticmethod
		def get_logo_png(size: str = "32px") -> str:
			"""Return an <img> tag with the logo.png embedded as a base64 data URI (falls back to an SVG emoji)."""
			try:
				# p = Path("./src/static/logo/logo.png")
				p = Path("/app/static/logo/logo.png")
				if p.exists():
					b = p.read_bytes()
					b64 = base64.b64encode(b).decode("ascii")
					return f'<img src="data:image/png;base64,{b64}" alt="logo" style="height:{size}; width:auto; display:block;" />'
				else:
					return f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" fill="white" style="display:block;"><text y="20" fill="white">🏥</text></svg>'
			except FileNotFoundError:
				return f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" fill="white" style="display:block;"><text y="20" fill="white">🏥</text></svg>'
			except Exception:
				return f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" fill="white" style="display:block;"><text y="20" fill="white">Logo</text></svg>'


		# ---------- Styles & Script ----------
		@staticmethod
		def get_base_styles() -> str:
			"""Provide a lightweight but branded styling layer."""
			return DesignSystem._dedent("""
			<style>
				:root {
					--font-family: 'Inter', 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
					--primary: #1a4fa0;
					--secondary: #06b6d4;
					--surface: #ffffff;
					--surface-alt: #f4f6fb;
					--border: #d7deee;
					--text: #1f2937;
					--muted: #64748b;
					--success: #059669;
					--error: #dc2626;
					--warning: #d97706;
				}

				body, .stApp {
					margin: 0;
					font-family: var(--font-family);
					background: var(--surface);
					color: var(--text);
					line-height: 1.5;
				}

				.app-header {
					display: flex;
					flex-direction: column;
					align-items: center;
					justify-content: center;
					text-align: center;
					padding: 2.5rem 1.25rem 2rem;
					background: var(--surface-alt);
					border-bottom: 1px solid var(--border);
					margin: 0 auto 2rem;
					max-width: 760px;
				}

				.app-logo {
					display: block;
					height: 48px;
					width: auto;
					margin: 0 auto 0.75rem;
				}

				.app-title {
					margin: 0;
					font-size: 2.25rem;
					font-weight: 700;
					color: var(--primary);
					text-align: center;
				}

				.app-subtitle {
					margin: 0.5rem auto 0;
					max-width: 520px;
					color: var(--muted);
					font-weight: 500;
					text-align: center;
				}

				.chat-container {
					max-width: 760px;
					margin: 0 auto;
					padding: 0 1.5rem;
				}

				.empty-state {
					border: 1px dashed var(--border);
					border-radius: 16px;
					padding: 1.5rem;
					margin: 2rem 0;
					text-align: center;
					background: var(--surface-alt);
					color: var(--muted);
				}

				.input-form {
					border: 1px solid var(--border);
					border-radius: 12px;
					padding: 1.5rem;
					margin: 1.5rem 0;
					background: var(--surface);
				}

				.form-title {
					font-weight: 600;
					color: var(--primary);
					display: flex;
					gap: 0.5rem;
					align-items: center;
					margin-bottom: 1rem;
				}

				.status-success,
				.status-error,
				.status-warning {
					padding: 0.75rem 1rem;
					border-radius: 12px;
					margin: 1rem 0;
					font-weight: 500;
				}

				.status-success { background: #ecfdf5; color: var(--success); }
				.status-error { background: #fef2f2; color: var(--error); }
				.status-warning { background: #fffbeb; color: var(--warning); }

				.loading-spinner {
					display: inline-block;
					width: 16px;
					height: 16px;
					border: 2px solid var(--border);
					border-top-color: var(--primary);
					border-radius: 50%;
					animation: rotate 1s linear infinite;
				}

				@keyframes rotate {
					to { transform: rotate(360deg); }
				}

				/* Streamlit Form Submit Button Styling */
				.stFormSubmitButton > button,
				button[type="submit"],
				div[data-testid="stFormSubmitButton"] > button,
				div.stFormSubmitButton > button {
					background-color: var(--primary) !important;
					color: white !important;
					border: none !important;
					font-weight: 600 !important;
					padding: 0.5rem 1rem !important;
					border-radius: 8px !important;
					transition: all 0.2s ease !important;
				}

				.stFormSubmitButton > button:hover,
				button[type="submit"]:hover,
				div[data-testid="stFormSubmitButton"] > button:hover,
				div.stFormSubmitButton > button:hover {
					background-color: #0f3870 !important;
					color: white !important;
					transform: translateY(-1px) !important;
					box-shadow: 0 4px 12px rgba(26, 79, 160, 0.3) !important;
				}

				.stFormSubmitButton > button:active,
				div[data-testid="stFormSubmitButton"] > button:active {
					transform: translateY(0) !important;
				}

				@media (max-width: 640px) {
					.app-title { font-size: 1.75rem; }
					.chat-container { padding: 0 1rem; }
					.input-form { padding: 1.25rem; }
				}
			</style>
			""")

		@staticmethod
		def get_theme_toggle_script() -> str:
			"""Returns empty script since theme toggle is removed."""
			return ""

		# ---------- Components ----------
		@staticmethod
		def get_logo_component(size: str = "32px", css_class: str = "app-logo") -> str:
			"""Return a styled logo span that inlines the SVG."""
			return DesignSystem._dedent(f"""
			<span class="{css_class}" style="height:{size}; width:auto; display:inline-block;">
				{DesignSystem.get_logo_svg()}
			</span>
			""")

		@staticmethod
		def header_html() -> str:
			"""Return a Lumahealth-inspired, professional header block."""
			logo = DesignSystem.get_logo_svg()
			return (
				'<div style="width:100%;height:100%;display:flex;justify-content:center;align-items:center;">'
					'<header class="app-header" style="text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:center;">'
					f'<div class="app-logo" style="margin:0 auto 0.75rem;display:flex;justify-content:center;">{logo}</div>'
					'<h1 class="app-title" style="margin:0; text-align:center;">Health Assistant</h1>'
					'<p class="app-subtitle" style="margin:0.5rem auto 0; text-align:center; max-width:520px;">Your AI-powered companion for appointment support.</p>'
					'</header>'
				'</div>'
			)
				
		@staticmethod
		def get_component_html(component_type: str, content: str = "", **kwargs) -> str:
			"""Generate HTML for styled components (dedented to avoid Markdown code blocks)."""
			H = DesignSystem._dedent  # alias

			components = {
				"header": H(f"""
				<div class="app-header">
				<div class="app-logo" style="margin-bottom: 0.75rem;">
					{DesignSystem.get_logo_svg()}
				</div>
				<h1 class="app-title">Luma Health Assistant</h1>
				<p class="app-subtitle">Your AI-powered companion for appointment support.</p>
				</div>
				"""),

				"form_container": H(f"""
				<div class="input-form" style="margin-left:auto; margin-right:auto; max-width:760px;">
					<div class="form-title">{kwargs.get('icon', '📝')} {kwargs.get('title', 'Please provide information')}</div>
					{content}
				</div>
				"""),

				"success_message": H(f"""<div class="status-success">✅ {content}</div>"""),
				"error_message":   H(f"""<div class="status-error">❌ {content}</div>"""),
				"warning_message": H(f"""<div class="status-warning">⚠️ {content}</div>"""),

				"loading": H(f"""
				<div style="display:flex; align-items:center; gap:.5rem; color: var(--muted);">
					<div class="loading-spinner"></div>
					{content or 'Processing...'}
				</div>
				"""),

				"logo": H(f"""
				<span class="app-logo" style="height:{kwargs.get('size', '32px')}; width:auto; display:block; margin:0 auto;">
					{DesignSystem.get_logo_svg()}
				</span>
				"""),

				"center": H(f"""
				<div style="display:flex; justify-content:center; align-items:center; width:100%;">
					{content}
				</div>
				"""),
			}
			return components.get(component_type, "")

		@staticmethod
		def apply_button_styling() -> str:
			"""Returns style tags specifically for button customization."""
			return DesignSystem._dedent("""
				<style>
					/* Force button styling with high specificity */
					.stFormSubmitButton button,
					button[kind="formSubmit"],
					.stForm button[kind="primary"] {
						background-color: #1a4fa0 !important;
						color: #ffffff !important;
						border: none !important;
						font-weight: 600 !important;
						padding: 0.5rem 1.5rem !important;
						border-radius: 8px !important;
						transition: all 0.2s ease !important;
					}

					.stFormSubmitButton button:hover,
					button[kind="formSubmit"]:hover,
					.stForm button[kind="primary"]:hover {
						background-color: #0f3870 !important;
						color: #ffffff !important;
						box-shadow: 0 4px 12px rgba(26, 79, 160, 0.3) !important;
						transform: translateY(-1px) !important;
					}

					.stFormSubmitButton button:active {
						transform: translateY(0) !important;
					}
				</style>
			""")

		@staticmethod
		def apply_message_styling() -> str:
			"""Returns additional style tags for message rendering."""
			return DesignSystem._dedent("""
				<style>
					.stChatMessage {
						max-width: 90% !important;
					}

					.stChatMessage[data-testid="chat-message-user"] {
						background: #f0f2f6 !important;
						color: var(--text) !important;
						border-radius: 16px !important;
						padding: 0.85rem 1rem !important;
						margin: 0.75rem 0 0.75rem auto !important;
						border: 1px solid rgba(0, 0, 0, 0.05) !important;
						box-shadow: none !important;
					}

					.stChatMessage[data-testid="chat-message-assistant"] {
						background: #ffffff !important;
						color: var(--text) !important;
						border-radius: 16px !important;
						padding: 0.85rem 1rem !important;
						margin: 0.75rem auto 0.75rem 0 !important;
						border: 1px solid rgba(0, 0, 0, 0.08) !important;
						box-shadow: none !important;
					}

					.stChatMessage .stMarkdown p {
						margin: 0 !important;
						font-size: 1rem !important;
						line-height: 1.55 !important;
					}

					@media (max-width: 640px) {
						.stChatMessage {
							max-width: 100% !important;
						}
					}
				</style>
			""")
