"""
Multi-Agent Negotiation System - "Agentic Boardroom"
Specialized agents debate and make strategic decisions
"""
import json
from typing import Dict, List, Any
from datetime import datetime
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class AgentPersona:
    """Base class for specialized business agents"""
    
    def __init__(self, name: str, role: str, priorities: List[str]):
        self.name = name
        self.role = role
        self.priorities = priorities
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze situation from agent's perspective"""
        raise NotImplementedError


class LogisticsAgent(AgentPersona):
    """Focuses on operational efficiency and delivery"""
    
    def __init__(self):
        super().__init__(
            name="Logistics Commander",
            role="Operations & Supply Chain",
            priorities=["delivery_time", "route_optimization", "warehouse_capacity"]
        )
    
    def analyze(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        prompt = """You are the Logistics Commander for a major e-commerce company.

SITUATION:
""" + json.dumps(situation, indent=2) + """

Your priorities: """ + ', '.join(self.priorities) + """

Analyze this situation from a LOGISTICS perspective and provide:
1. Your assessment (max 2 sentences)
2. Top 3 primary recommendations
3. Implementation timeline
4. Critical risk factors (max 3)

Respond in JSON format:
{
    "assessment": "concise executive summary",
    "recommendations": ["Action 1 (short)", "Action 2 (short)", "Action 3 (short)"],
    "timeline": "e.g., immediate, 24-48h",
    "risks": ["Risk 1", "Risk 2", "Risk 3"],
    "confidence": 0.0-1.0
}"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            text = text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            return {
                "assessment": "Analysis synchronization error.",
                "recommendations": ["Manual supply chain audit required"],
                "timeline": "TBD",
                "risks": ["Information gap"],
                "confidence": 0.0
            }


class FinanceAgent(AgentPersona):
    """Focuses on cost optimization and revenue protection"""
    
    def __init__(self):
        super().__init__(
            name="Finance Director",
            role="Financial Analysis & Cost Management",
            priorities=["cost_reduction", "revenue_protection", "roi_maximization"]
        )
    
    def analyze(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        prompt = """You are the Finance Director.

SITUATION:
""" + json.dumps(situation, indent=2) + """

Analyze this situation from a FINANCIAL perspective and provide:
1. Cost-benefit summary (max 2 sentences)
2. Revenue impact (short string)
3. One key budget recommendation
4. Top 2 financial risks

Respond in JSON format:
{
    "cost_analysis": "concise profit/loss summary",
    "revenue_impact": "-$X.XM risk or +$X.XM potential",
    "budget_recommendation": "specific budget action",
    "financial_risks": ["Risk 1", "Risk 2"],
    "confidence": 0.0-1.0
}"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            text = text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            return {
                "cost_analysis": "Financial data stream interrupted.",
                "revenue_impact": "Undetermined",
                "budget_recommendation": "Hold current position",
                "financial_risks": ["Data integrity risk"],
                "confidence": 0.0
            }


class ExecutiveAgent(AgentPersona):
    """Makes final decisions based on overall business strategy"""
    
    def __init__(self):
        super().__init__(
            name="Chief Executive",
            role="Strategic Decision Making",
            priorities=["customer_satisfaction", "brand_reputation", "long_term_growth"]
        )
    
    def decide(self, situation: Dict[str, Any], logistics_view: Dict, finance_view: Dict) -> Dict[str, Any]:
        prompt = """You are the CEO. Final decision required.

SITUATION:
""" + json.dumps(situation, indent=2) + """

LOGISTICS SUMMARY: """ + str(logistics_view.get('assessment')) + """
FINANCE SUMMARY: """ + str(finance_view.get('cost_analysis')) + """

Make a high-stakes decision. Provide:
1. Decision (Approve / Reject / Pivot)
2. Rationale (max 2 hard-hitting sentences)
3. 3 Strategic directives
4. 2 KPIs to track

Respond in JSON format:
{
    "decision": "APPROVE / REJECT / PIVOT",
    "rationale": "strategic reasoning",
    "directives": ["Directive 1", "Directive 2", "Directive 3"],
    "success_metrics": ["KPI 1", "KPI 2"],
    "confidence": 0.0-1.0
}"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            text = text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            return {
                "decision": "defer",
                "rationale": f"Decision analysis failed: {str(e)}",
                "directives": ["Escalate to human oversight"],
                "success_metrics": [],
                "confidence": 0.0
            }


class AgenticBoardroom:
    """Orchestrates multi-agent negotiation and decision making"""
    
    def __init__(self):
        self.logistics_agent = LogisticsAgent()
        self.finance_agent = FinanceAgent()
        self.executive_agent = ExecutiveAgent()
        self.session_history = []
    
    def convene(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convene the boardroom to analyze and decide on a situation
        
        Returns: {
            'session_id': str,
            'situation': dict,
            'logistics_analysis': dict,
            'finance_analysis': dict,
            'executive_decision': dict,
            'timestamp': str,
            'debate_summary': str
        }
        """
        session_id = f"boardroom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Each agent analyzes the situation
        logistics_analysis = self.logistics_agent.analyze(situation)
        finance_analysis = self.finance_agent.analyze(situation)
        
        # Executive makes final decision
        executive_decision = self.executive_agent.decide(
            situation, 
            logistics_analysis, 
            finance_analysis
        )
        
        # Create debate summary
        debate_summary = self._generate_debate_summary(
            situation,
            logistics_analysis,
            finance_analysis,
            executive_decision
        )
        
        session = {
            'session_id': session_id,
            'situation': situation,
            'logistics_analysis': logistics_analysis,
            'finance_analysis': finance_analysis,
            'executive_decision': executive_decision,
            'timestamp': datetime.now().isoformat(),
            'debate_summary': debate_summary
        }
        
        self.session_history.append(session)
        
        return session
    
    def _generate_debate_summary(self, situation, logistics, finance, decision) -> str:
        """Generate a human-readable summary of the debate"""
        summary = f"""
BOARDROOM SESSION SUMMARY
========================

SITUATION: {situation.get('type', 'Unknown')} - {situation.get('description', '')}

LOGISTICS COMMANDER:
{logistics.get('assessment', 'No assessment')}
Recommendations: {', '.join(logistics.get('recommendations', []))}

FINANCE DIRECTOR:
{finance.get('cost_analysis', 'No analysis')}
Revenue Impact: {finance.get('revenue_impact', 'Unknown')}

EXECUTIVE DECISION:
{decision.get('decision', 'No decision').upper()}
Rationale: {decision.get('rationale', 'No rationale provided')}

IMPLEMENTATION:
{chr(10).join(['- ' + d for d in decision.get('directives', [])])}
"""
        return summary.strip()
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent boardroom sessions"""
        return self.session_history[-limit:]


# Global boardroom instance
boardroom = AgenticBoardroom()


def convene_boardroom(situation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Public interface to convene the agentic boardroom
    """
    return boardroom.convene(situation)


def get_boardroom_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent boardroom sessions
    """
    return boardroom.get_session_history(limit)
