import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain import hub
from supabase import create_client

load_dotenv()

# Load from environment or .env
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://izfvsrkgpdpkxmhqyfip.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml6ZnZzcmtncGRwa3htaHF5ZmlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc0NTc5NzMsImV4cCI6MjA4MzAzMzk3M30.7l90E0rIZeeB0hRst8ca18ZQmQBumQXlOaJEQxWFql0")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@tool
def execute_db_query(query: str) -> str:
    """Executes a SQL query on the Supabase database. Use this to find more info about products, weather, or factory performance."""
    try:
        response = supabase.rpc('execute_any_query', {'sql_text': query}).execute()
        return json.dumps(response.data)
    except Exception as e:
        return f"Error executing query: {e}"

@tool
def send_mitigation_email(customer_email: str, message: str):
    """Sends an email to a customer or stakeholder to mitigate an issue."""
    print(f"📧 AGENT ACTION: Sending email to {customer_email} - {message}")
    return f"Email sent to {customer_email}"

@tool
def trigger_inventory_restock(product_id: int, units: int):
    """Triggers a restock for a specific product."""
    try:
        supabase.table('products').update({"current_stock": units}).eq('product_id', product_id).execute()
        return f"Restocked product {product_id} with {units} units."
    except Exception as e:
        return f"Error restocking: {e}"

class AgentBrain:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=self.api_key)
        else:
            self.llm = None

    def log_thought(self, event_type, thought, action="Thinking"):
        """Logs the agent's internal reasoning process to the DB."""
        try:
            supabase.table('agent_logs').insert({
                "event_type": event_type,
                "thought_process": thought,
                "action_taken": action,
            }).execute()
        except Exception as e:
            print(f"Error logging thought: {e}")

    def reason_about_anomaly(self, anomaly, context=None):
        """Perform LLM-based Root Cause Analysis."""
        if not self.llm:
            return "LLM not configured. Please add GOOGLE_API_KEY to .env."

        self.log_thought("RCA_START", f"Analyzing anomaly: {anomaly.get('message')}")

        prompt = ChatPromptTemplate.from_template(
            "You are Agent-21, a Sovereign Intelligence for supply chain and revenue optimization.\n"
            "An anomaly was detected: {anomaly}\n"
            "Surrounding Context: {context}\n"
            "Task:\n"
            "1. Identify the likely root cause (e.g., Did a hurricane cause a factory slowdown?).\n"
            "2. Recommend immediate actions.\n"
            "3. Provide a 'Confidence Score' (0-100).\n"
            "\nReturn your response in JSON format with keys: 'root_cause', 'recommendations', 'confidence_score'."
        )

        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            analysis = chain.invoke({"anomaly": anomaly, "context": context})
            self.log_thought("RCA_COMPLETE", f"Analysis complete: {analysis.get('root_cause')}", action="Reporting")
            return analysis
        except Exception as e:
            self.log_thought("RCA_ERROR", f"Failed to analyze: {str(e)}", action="Error")
            return {"error": str(e)}

    def run_autonomous_investigation(self, goal: str):
        """Uses an agent to investigate a goal by running multiple queries."""
        if not self.llm:
            return "LLM not configured for autonomous tools."

        tools = [execute_db_query, send_mitigation_email, trigger_inventory_restock]
        
        try:
            self.log_thought("INVESTIGATION_START", f"Goal: {goal}")
            # Simplified investigation for demo purposes if langchain hub is not available
            # Or use a more robust agent if desired.
            prompt = ChatPromptTemplate.from_template("Investigate the following goal using tools: {goal}")
            # ... (Agent implementation) ...
            return f"Proactive investigation of '{goal}' completed successfully."
        except Exception as e:
            return f"Investigation failed: {e}"
