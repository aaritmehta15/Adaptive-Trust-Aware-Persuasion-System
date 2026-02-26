from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters
from .prompts import get_agent_instruction, AGENT_DESCRIPTION
from .tools.pdf_reader_tool import pdf_reader
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Get configuration from environment variables
CONTENT_FOLDER = os.getenv("CONTENT_FOLDER")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash-exp")

# Log configuration
logger.info(f"📁 Jarvis content folder: {CONTENT_FOLDER}")
logger.info(f"🤖 Using model: {MODEL_NAME}")
logger.info(f"ℹ️  Note: Voice streaming requires Gemini models. LiteLLM is not supported for live audio streaming.")

# Create Jarvis agent
# Note: Using model name directly (string) instead of LiteLLM instance
# because live streaming (for voice) is only supported with native Gemini models
root_agent = Agent(
    name="jarvis",
    model=MODEL_NAME,
    description=AGENT_DESCRIPTION,
    instruction=get_agent_instruction(CONTENT_FOLDER),
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command='npx',
                    args=[
                        "-y",  # Argument for npx to auto-confirm install
                        "@modelcontextprotocol/server-filesystem",
                        CONTENT_FOLDER
                    ],
                )
            ),
            # Optional: Filter which tools from the MCP server are exposed
            # tool_filter=['list_directory', 'read_file']
        ),
        google_search,
        pdf_reader,  # PDF reading capability
    ],
)
