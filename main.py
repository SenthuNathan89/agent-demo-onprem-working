import os
import operator
import phoenix as px
from dotenv import load_dotenv  
from phoenix.otel import register  
from pathlib import Path   
from typing import TypedDict, Annotated, Sequence
from typing_extensions import TypedDict

from langchain_openai import AzureChatOpenAI
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from persistent_memory.memory import get_session_history, clear_session_history   
from toolsuite.toolkit import calculate, summarize_text, search_knowledge_base, web_search
from pii_guardrail import OutputGuardrails
from prompt_guardrail import InputGuardrails

# PII Guardrail Initialization---------------------------------------------------------------------------------------------------------------
output_guardrails = OutputGuardrails()
input_guardrails = InputGuardrails()

# Monitoring Setup ----------------------------------------------------------------------------------------------------------------------------
DB_PATH = Path("./phoenix_data/phoenix.db").absolute()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

os.environ["PHOENIX_SQL_DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["PHOENIX_WORKING_DIR"] = str(DB_PATH.parent)

session = px.launch_app(
    host="0.0.0.0",
    port=6006
)

tracer_provider = register(
    project_name="Onpremise_LLM_Agent",
    endpoint="http://localhost:6006/v1/traces",
    auto_instrument=True,
)

# =============================================================================================================================================
load_dotenv()
SQLITE_DB_PATH ="chat_history.db"
FAISS_INDEX_PATH = "faiss_index"

#Azure Components Initialization - LLM, Embeddings, Vector Store, Memory----------------------------------------------------------------------
# Initialize Azure OpenAI LLM
llm = AzureChatOpenAI(
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature = 0.7
)

# On prem LLM via Ollama - for TESTING purposes only------------------------------------------------------------------------------------------------
# Start ollama server in another terminal before running this script
# llm = ChatOllama(
#     model="qwen3:4b",  
#     base_url="http://localhost:11434",  
#     temperature=0.7,
#     max_tokens=2048
# )

# Else for PRODUCTION use gemma3:13b or gemma3:70b models if you have sufficient resources via vllm
# Start vllm server in another terminal before running this script
# python -m vllm.entrypoints.openai.api_server --model gemma3:13b --port 8030

# llm = ChatOpenAI(
#     base_url="http://localhost:8030/v1",
#     model_name="gemma3:4b",
#     api_key="EMPTY",
#     temperature=0.7,
#     max_tokens=2048
# )

#-----------------------------------------------------------------------------------------------------------------------------------------------
# Initialize Embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",  
    model_kwargs={'device': 'cpu'}, 
    encode_kwargs={'normalize_embeddings': True}
)
            
# SQLite-based chat history management----------------------------------------------------------------------------------------------------------
chat_histories = {}

# Create tools list
tools = [calculate, summarize_text, search_knowledge_base, web_search]

# Create ToolNode - this replaces ToolExecutor and individual tool nodes
tool_node = ToolNode(tools)
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are a helpful AI assistant specializing in {domain}."),
#     ("human", "{user_input}")
# ])
# LangGraph State Definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# Define LangGraph workflow nodes
def call_model(state: AgentState):
    # Calls the LLM on what to do next
    messages = state["messages"]
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    # Determines if we should continue to tools or end
    last_message = state["messages"][-1]
    
    # Check if the LLM made a tool call
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return "end"

# Build LangGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)  #ToolNode handles all tools
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, { "tools": "tools", "end": END })
workflow.add_edge("tools", "agent")

app = workflow.compile()

# Main execution function of agent with memory------------------------------------------------------------------------------------------------------
def run_agent(user_input: str, session_id: str = "defaultUser"):
    # Get conversation history
    chat_history = get_session_history(session_id)
    # Load previous messages
    previous_messages = chat_history.messages
    # Create initial state
    initial_state = {
        "messages": previous_messages + [HumanMessage(content=user_input)]
    }
    # Run the workflow
    result = app.invoke(initial_state)
    # Save to memory
    chat_history.add_user_message(user_input)
    final_message = result["messages"][-1]

    # Get the final AI message ( No guardrail for testing purposes )--------------------------------------------------------------------------------
    # if hasattr(final_message, 'content'):
    #     chat_history.add_ai_message(final_message.content)
    #     return final_message.content

    # Post-processing with PII Guardrail-------------------------------------------------------------------------------------------------------------
    if hasattr(final_message, 'content'):
        response_content = final_message.content

        # Check response for high-risk PII
        if not output_guardrails.is_safe(response_content):
            blocked_message = "Response blocked as it includes sensitive information that cannot be shared."
            chat_history.add_ai_message(blocked_message)
            final_message=blocked_message
           
        # Mask any remaining PII or Secret Keys 
        safe_response, detected_pii = output_guardrails.mask_pii(response_content)
        safe_response, detected_secrets = output_guardrails.mask_secret(safe_response)

        # if PII or Secret was detected and masked
        if detected_pii:
            safe_response = f"Note: {', '.join(detected_pii).upper()} information masked for privacy and safety reasons."
        if detected_secrets:
            safe_response = f"Note: {', '.join(detected_secrets).upper()} information masked for security reasons (secrets)."

        # Save safe response to memory
        chat_history.add_ai_message(safe_response)
        final_message=safe_response

    return str(final_message)

# ==================================================================================================================================================
# INTERACTIVE CLI INTERFACE

def interactive_cli():
    # Main interactive CLI loop
    print("\n" + "="*70)
    print("   INTERACTIVE AGENT CLI")
    print("="*70)
    print("\nCommands:")
    print("  - Type your query and press Enter to talk to the agent")
    print("  - 'status' - Show agent status")
    print("  - 'clear' - Clear current session history")
    print("  - 'sessions' - List all available sessions")
    print("  - 'session <name>' - Switch to a different session")
    print("\nAvailable Tools:")
    print("  - calculate(expression) - Perform math calculations")
    print("  - summarize_text(text) - Summarize long text")
    print("  - search knowledge base(query) - Search the knowledge base")
    print("  - web search(query) - Search the web via Tavily")
    print("\n" + "="*70 + "\n")

    print("Enter your username to start:")
    username = input(f"").strip()
    current_session = username
    print(f"Starting session: {current_session}")

    while True:
        try:
            # Get user input
            user_input = input(f"\n[{current_session}] You: ").strip()
            
            # Handle empty input
            if not user_input:
                continue    
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n Goodbye! Your are on your own now!\n")
                break          
            elif user_input.lower() == 'clear':
                if clear_session_history(current_session):
                    print(f"\n Cleared history for session '{current_session}'\n")
                else:
                    print(f"\n No history to clear for session '{current_session}'\n")
                continue          
            elif user_input.lower().startswith('session '):
                new_session = user_input.split(' ', 1)[1].strip()
                if new_session:
                    current_session = new_session
                    print(f"\n Switched to session: {current_session}\n")
                else:
                    print("\n Please provide a session name\n")
                continue
            elif user_input.lower() == 'sessions':
                result = get_session_history()
                continue
            
            # Run the agent
            print(f"\n[{current_session}] Agent: ", end="", flush=True)

            passed, results = input_guardrails.check_all(user_input)
            print(f"Overall Input Guardrail Result: {'PASSED' if passed else 'FAILED'}")
            for result in results:
                print(f" - {result['cause']} (Risk: {result['risk_level']})")
            if not passed:
                print("Input blocked due to guardrail violations.")
                continue
            else:
                response = run_agent(user_input, session_id=current_session)
                print(response)
        
        except KeyboardInterrupt:
            print("\n\n Interrupted. Goodbye! Stupid of me or beyond my control!\n")
            break
        
        except Exception as e:
            print(f"\n Error: {e}\n")

if __name__ == "__main__":
    interactive_cli()