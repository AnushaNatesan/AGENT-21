"""
Predictive Digital Twin - "What-If" Simulator
Virtual replica of business processes for scenario simulation
"""
import json
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class BusinessMetrics:
    """Current state of business metrics"""
    
    def __init__(self, data: Dict[str, Any]):
        self.revenue = data.get('revenue', 1000000)
        self.costs = data.get('costs', 750000)
        self.inventory_level = data.get('inventory_level', 5000)
        self.production_rate = data.get('production_rate', 1000)
        self.demand_rate = data.get('demand_rate', 950)
        self.pricing_multiplier = data.get('pricing_multiplier', 1.0)
        self.customer_satisfaction = data.get('customer_satisfaction', 0.85)
        self.delivery_time_avg = data.get('delivery_time_avg', 3.5)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'revenue': self.revenue,
            'costs': self.costs,
            'profit': self.revenue - self.costs,
            'profit_margin': ((self.revenue - self.costs) / self.revenue) * 100 if self.revenue > 0 else 0,
            'inventory_level': self.inventory_level,
            'production_rate': self.production_rate,
            'demand_rate': self.demand_rate,
            'pricing_multiplier': self.pricing_multiplier,
            'customer_satisfaction': self.customer_satisfaction,
            'delivery_time_avg': self.delivery_time_avg
        }


class DigitalTwin:
    """Virtual replica of the business for scenario simulation"""
    
    def __init__(self, baseline_metrics: BusinessMetrics):
        self.baseline = baseline_metrics
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.simulation_history = []
    
    def simulate_scenario(self, scenario: Dict[str, Any], duration_days: int = 30) -> Dict[str, Any]:
        """
        Simulate a what-if scenario
        
        Args:
            scenario: Dict describing the scenario (e.g., {'raw_material_price_increase': 20})
            duration_days: Simulation duration
            
        Returns: Simulation results with predictions
        """
        simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create a copy of baseline metrics
        current_state = BusinessMetrics(self.baseline.to_dict())
        
        # Apply scenario changes
        modified_state = self._apply_scenario(current_state, scenario)
        
        # Use AI to predict cascading effects
        predictions = self._predict_cascading_effects(scenario, modified_state, duration_days)
        
        # Calculate impact metrics
        impact_analysis = self._calculate_impact(
            self.baseline.to_dict(),
            predictions['final_state']
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(scenario, impact_analysis)
        
        result = {
            'simulation_id': simulation_id,
            'scenario': scenario,
            'duration_days': duration_days,
            'baseline_state': self.baseline.to_dict(),
            'predicted_state': predictions['final_state'],
            'timeline': predictions['timeline'],
            'impact_analysis': impact_analysis,
            'recommendations': recommendations,
            'risk_level': self._assess_risk_level(impact_analysis),
            'timestamp': datetime.now().isoformat()
        }
        
        self.simulation_history.append(result)
        
        return result
    
    def _apply_scenario(self, state: BusinessMetrics, scenario: Dict[str, Any]) -> BusinessMetrics:
        """Apply scenario changes to business state"""
        
        # Raw material price increase
        if 'raw_material_price_increase' in scenario:
            increase_pct = scenario['raw_material_price_increase']
            state.costs *= (1 + increase_pct / 100)
        
        # Demand surge
        if 'demand_surge' in scenario:
            surge_pct = scenario['demand_surge']
            state.demand_rate *= (1 + surge_pct / 100)
        
        # Supply chain disruption
        if 'supply_chain_disruption' in scenario:
            disruption_pct = scenario['supply_chain_disruption']
            state.production_rate *= (1 - disruption_pct / 100)
            state.delivery_time_avg *= (1 + disruption_pct / 50)
        
        # Competitor pricing
        if 'competitor_price_drop' in scenario:
            drop_pct = scenario['competitor_price_drop']
            state.pricing_multiplier *= (1 - drop_pct / 100)
            state.demand_rate *= (1 + drop_pct / 200)  # Some demand increase
        
        # Weather event
        if 'weather_severity' in scenario:
            severity = scenario['weather_severity']
            state.delivery_time_avg *= (1 + severity / 10)
            state.customer_satisfaction *= (1 - severity / 20)
        
        return state
    
    def _predict_cascading_effects(self, scenario: Dict[str, Any], initial_state: BusinessMetrics, days: int) -> Dict[str, Any]:
        """Use AI to predict cascading business effects"""
        
        prompt = f"""You are a business simulation AI. Predict the cascading effects of this scenario over {days} days.

SCENARIO:
{json.dumps(scenario, indent=2)}

INITIAL STATE AFTER SCENARIO:
{json.dumps(initial_state.to_dict(), indent=2)}

Predict:
1. How metrics will evolve over time
2. Secondary and tertiary effects
3. Critical inflection points
4. Final state after {days} days

Respond in JSON format:
{{
    "timeline": [
        {{"day": 1, "key_events": ["event1"], "metrics_snapshot": {{}}}},
        {{"day": 7, "key_events": ["event2"], "metrics_snapshot": {{}}}},
        {{"day": 30, "key_events": ["event3"], "metrics_snapshot": {{}}}}
    ],
    "final_state": {{
        "revenue": number,
        "costs": number,
        "inventory_level": number,
        "production_rate": number,
        "demand_rate": number,
        "customer_satisfaction": 0.0-1.0,
        "delivery_time_avg": number
    }},
    "cascading_effects": ["effect1", "effect2"]
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            text = text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            # Fallback to simple projection
            final_state = initial_state.to_dict()
            return {
                "timeline": [
                    {"day": days, "key_events": ["Simulation completed"], "metrics_snapshot": final_state}
                ],
                "final_state": final_state,
                "cascading_effects": [f"Prediction error: {str(e)}"]
            }
    
    def _calculate_impact(self, baseline: Dict, predicted: Dict) -> Dict[str, Any]:
        """Calculate impact metrics comparing baseline to prediction"""
        
        impacts = {}
        
        for key in baseline:
            if isinstance(baseline[key], (int, float)) and isinstance(predicted.get(key), (int, float)):
                baseline_val = baseline[key]
                predicted_val = predicted[key]
                
                if baseline_val != 0:
                    change_pct = ((predicted_val - baseline_val) / baseline_val) * 100
                else:
                    change_pct = 0
                
                impacts[key] = {
                    'baseline': baseline_val,
                    'predicted': predicted_val,
                    'change': predicted_val - baseline_val,
                    'change_percent': round(change_pct, 2)
                }
        
        return impacts
    
    def _generate_recommendations(self, scenario: Dict, impact: Dict) -> List[str]:
        """Generate actionable recommendations based on simulation"""
        
        recommendations = []
        
        # Check profit impact
        if 'profit' in impact and impact['profit']['change_percent'] < -10:
            recommendations.append("⚠️ Significant profit decline predicted. Consider cost reduction measures.")
        
        # Check inventory
        if 'inventory_level' in impact and impact['inventory_level']['predicted'] < 1000:
            recommendations.append("📦 Low inventory predicted. Increase production or safety stock.")
        
        # Check customer satisfaction
        if 'customer_satisfaction' in impact and impact['customer_satisfaction']['predicted'] < 0.7:
            recommendations.append("😟 Customer satisfaction at risk. Improve service quality or communication.")
        
        # Check delivery time
        if 'delivery_time_avg' in impact and impact['delivery_time_avg']['change_percent'] > 20:
            recommendations.append("🚚 Delivery delays expected. Consider alternative logistics routes.")
        
        if not recommendations:
            recommendations.append("✅ Scenario impact appears manageable with current operations.")
        
        return recommendations
    
    def _assess_risk_level(self, impact: Dict) -> str:
        """Assess overall risk level of the scenario"""
        
        risk_score = 0
        
        # Profit impact
        if 'profit' in impact:
            if impact['profit']['change_percent'] < -20:
                risk_score += 3
            elif impact['profit']['change_percent'] < -10:
                risk_score += 2
            elif impact['profit']['change_percent'] < 0:
                risk_score += 1
        
        # Customer satisfaction
        if 'customer_satisfaction' in impact:
            if impact['customer_satisfaction']['predicted'] < 0.6:
                risk_score += 3
            elif impact['customer_satisfaction']['predicted'] < 0.75:
                risk_score += 2
        
        # Inventory
        if 'inventory_level' in impact:
            if impact['inventory_level']['predicted'] < 500:
                risk_score += 2
        
        if risk_score >= 6:
            return "CRITICAL"
        elif risk_score >= 4:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_simulation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent simulations"""
        return self.simulation_history[-limit:]
    
    def compare_scenarios(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple scenarios side-by-side"""
        
        results = []
        for scenario in scenarios:
            result = self.simulate_scenario(scenario)
            results.append(result)
        
        comparison = {
            'scenarios': results,
            'best_scenario': None,
            'worst_scenario': None,
            'comparison_matrix': {}
        }
        
        # Find best and worst by profit impact
        if results:
            sorted_by_profit = sorted(
                results,
                key=lambda x: x['impact_analysis'].get('profit', {}).get('predicted', 0),
                reverse=True
            )
            comparison['best_scenario'] = sorted_by_profit[0]['simulation_id']
            comparison['worst_scenario'] = sorted_by_profit[-1]['simulation_id']
        
        return comparison


# Initialize with default baseline
default_baseline = BusinessMetrics({
    'revenue': 1250000,
    'costs': 875000,
    'inventory_level': 5000,
    'production_rate': 1000,
    'demand_rate': 950,
    'pricing_multiplier': 1.25,
    'customer_satisfaction': 0.87,
    'delivery_time_avg': 2.4
})

digital_twin = DigitalTwin(default_baseline)


def run_simulation(scenario: Dict[str, Any], duration_days: int = 30) -> Dict[str, Any]:
    """
    Public interface to run a what-if simulation
    """
    return digital_twin.simulate_scenario(scenario, duration_days)


def get_simulation_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent simulations
    """
    return digital_twin.get_simulation_history(limit)


def compare_scenarios(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare multiple scenarios
    """
    return digital_twin.compare_scenarios(scenarios)
