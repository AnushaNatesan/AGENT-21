# Agent-21: Sovereign Supply Chain & Revenue Intelligence

# DEMO-VIDEO 👉: https://drive.google.com/file/d/1Dcekf53jha9UOHM3BMccHCI6i7e2AgrC/view?usp=sharing

Agent-21 is a high-performance, AI-driven platform designed for supply chain optimization, revenue intelligence, and executive decision-making. It combines real-time data from a sovereign database with the power of Large Language Models (LLMs) to provide actionable insights, autonomous investigations, and multilingual support.

## 🚀 Key Features

### 1. Sovereign Intelligence (Agent-21)
The core of the platform is an autonomous AI agent capable of:
- **Retrieval-Augmented Generation (RAG)**: Querying company-specific data (weather, products, logistics) to provide accurate answers.
- **Autonomous Tools**: Restocking inventory, sending mitigation emails, and executing database queries without human intervention.
- **Multilingual Support**: Real-time bi-directional translation (powered by specialized APIs) allowing users to interact in their native language while the agent processes data in English.

### 2. Executive War Room
A high-stakes boardroom simulator where AI personas (CEO, Chief Risk Officer, Head of Logistics, etc.) debate complex business scenarios.
- **Animated Discussion**: Visual representation of the boardroom debate.
- **Executive Reports**: Automatically generated reports with mitigation plans and recommended automations.

### 3. ML Anomaly Detection
A multi-layered anomaly detection engine that monitors every facet of the supply chain using advanced statistical and machine learning techniques:
- **Revenue Intelligence**: Uses `IsolationForest` to identify non-linear revenue spikes or drops.
- **Logistics & Delivery**: Employs **Modified Z-Score (MAD)** for robust outlier detection in delivery delays.
- **Factory & Inventory**: Data-driven thresholding (IQR-based) to detect throughput bottlenecks and stock instabilities.
- **Market & Sentiment**: Tracks price volatility, sentiment drift, and sudden market share shifts using rolling gradients and standard deviation analysis.

### 4. Proactive Notification System
A dedicated autonomous agent (`run_ml_proactive_agent`) that continuously scans for the anomalies described above.
- **Automated Alerts**: Instantly dispatches detailed email notifications to stakeholders upon detection.
- **Contextual Details**: Emails include specific IDs (Product, Order, Factory) and the exact statistical deviance found.
- **Live Feed Integration**: Anomalies are streamed in real-time to the Business Dashboard for immediate executive action.

### 5. Supply Chain Twin & Business Dashboard
Comprehensive visualization of company assets:
- **Factory Performance**: Real-time tracking of efficiency and health.
- **Logistics Monitoring**: Weather impact analysis on delivery routes.
- **Market Insights**: Revenue leaderboards and category-wise market share distribution.

### 6. Advanced Resilience Features
- **Self-Healing SQL**: AI-driven correction of failed database queries.
- **Audit Trail**: Verifiable logs of every agent action and thought process for compliance.

### 7. Market Intelligence & Survey Platform
A specialized environment for deep-dive market research:
- **Product Analysis**: Automated research into product-market fit, competitor benchmarks, and success probability.
- **Pricing Insights**: AI-driven recommendation of optimal price points based on regional demand and competitor positioning.
- **Competitive Landscape**: Visual breakdown of competitor strengths and vulnerabilities.

### 8. Agentic Advertisement Automation
Sovereign intelligence applied to growth marketing:
- **Poster Generating**: Advertise the newly launched product by generating posters and sending to the target audience via emails to market it. 

### 9. Omni-channel Engagement (Telegram & Social)
Ensuring the AI is reachable where the customers are:
- **Multilingual Telegram Bots**: Direct integration with Telegram for instant support and order tracking in any language.
- **Social Media Presence**: Autonomous monitoring and engagement across major social platforms to maintain brand sentiment.

## 🛠️ Tech Stack

- **Backend**: Django (Python), Django REST Framework
- **Frontend**: Vanilla HTML5, Modern CSS (Glassmorphism), JavaScript
- **AI/LLM**: Google Gemini (gemini-1.5-flash), LangChain
- **Database**: Supabase (PostgreSQL with real-time capabilities)
- **Deployment**: Local dev server with external API integration

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Agent-21
```

### 2. Set Up Virtual Environment
```bash
python -m venv env
source env/Scripts/activate  # Windows
# or
source env/bin/activate      # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory and add:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
GEMINI_API_KEY=your_google_gemini_api_key
```

### 5. Run the Server
```bash
python manage.py runserver
```

## 🌐 API Integrations
The project relies on several key endpoints:
- **Agent API**: `http://172.16.10.134:3000/agent/query`
- **Translation Request**: `http://172.16.6.83:8000/api/translate/request/`
- **Translation Response**: `http://172.16.6.83:8000/api/translate/response/`

## 📂 Project Structure
- `/App`: Core Django application logic, views, and templates.
- `/Agent_21`: Project configuration and URL routing.
- `/App/templates`: High-fidelity dashboards (Customer, Business, War Room).
- `views_scenario.py`: Logic for the Executive War Room simulation.

For detailed information on technical implementations like Audit Trails and Digital Twins, see [ADVANCED_FEATURES_README.md](./ADVANCED_FEATURES_README.md).

## 🛡️ License
Proprietary Intelligence - Designed for SSN Trust HackSymmetric.


# AGENT-21 Advanced Features Implementation

## Overview
This document describes the four advanced features implemented in the Agent-21 system:

1. **Self-Healing SQL Re-Sensing**
2. **Multi-Agent Negotiation (Agentic Boardroom)**
3. **Predictive Digital Twin (What-If Simulator)**
4. **Immutable Audit Trail (Proof of Agency)**

---

## 1. Self-Healing SQL Re-Sensing

### Description
An autonomous SQL debugging and correction system that automatically detects, diagnoses, and fixes SQL query errors without human intervention.

### Key Features
- **Automatic Error Detection**: Identifies syntax errors, schema mismatches, and other SQL issues
- **AI-Powered Diagnosis**: Uses Gemini AI to analyze errors and understand root causes
- **Schema Inspection**: Automatically fetches and caches table schemas for context
- **Iterative Correction**: Attempts up to 3 fixes before giving up
- **Detailed Logging**: Provides complete healing logs for transparency

### How It Works
1. User submits a SQL query
2. System attempts execution
3. If error occurs, AI agent analyzes the error and schema
4. AI rewrites the query to fix the issue
5. System retries with corrected query
6. Process repeats up to 3 times
7. Returns results with complete healing log

### API Endpoint
```
POST /api/advanced/sql/healing/
Body: {"query": "SELECT * FROM..."}
```

### UI Location
Navigate to: **Advanced Features → SQL Healer**

---

## 2. Multi-Agent Negotiation (Agentic Boardroom)

### Description
A system where specialized AI agents debate and negotiate to make strategic business decisions, simulating a corporate boardroom.

### Agents
1. **Logistics Commander**
   - Focus: Operational efficiency, delivery, supply chain
   - Analyzes: Route optimization, warehouse capacity, delivery times
   
2. **Finance Director**
   - Focus: Cost optimization, revenue protection, ROI
   - Analyzes: Cost-benefit, budget impact, financial risks
   
3. **Chief Executive**
   - Focus: Overall strategy, customer satisfaction, brand reputation
   - Makes: Final decisions based on all perspectives

### How It Works
1. Critical situation is detected (e.g., hurricane, supply disruption)
2. Logistics Agent analyzes operational impact
3. Finance Agent analyzes financial impact
4. Both agents provide recommendations
5. Executive Agent reviews both perspectives
6. Executive makes final decision with rationale
7. Implementation directives are generated

### Predefined Scenarios
- Weather Risk / Natural Disaster
- Supply Chain Disruption
- Unexpected Demand Surge
- Competitor Action
- Custom Situation

### API Endpoints
```
POST /api/advanced/boardroom/convene/
Body: {"situation": {...}}

GET /api/advanced/boardroom/history/?limit=10
```

### UI Location
Navigate to: **Advanced Features → Boardroom**

---

## 3. Predictive Digital Twin (What-If Simulator)

### Description
A virtual replica of the business that simulates "what-if" scenarios to forecast impacts and provide proactive recommendations.

### Simulation Parameters
- **Raw Material Price Changes**: +/- percentage
- **Demand Surges**: +/- percentage
- **Supply Chain Disruptions**: percentage reduction
- **Simulation Duration**: days to forecast

### Metrics Simulated
- Revenue & Costs
- Profit & Profit Margin
- Inventory Levels
- Production Rate
- Demand Rate
- Customer Satisfaction
- Delivery Times

### How It Works
1. User defines scenario parameters
2. System applies changes to baseline metrics
3. AI predicts cascading effects over time
4. Impact analysis compares baseline vs. predicted
5. Risk level is assessed (LOW/MEDIUM/HIGH/CRITICAL)
6. Actionable recommendations are generated

### Risk Assessment
- **LOW**: Manageable impact, minimal intervention needed
- **MEDIUM**: Notable impact, monitoring recommended
- **HIGH**: Significant impact, action required
- **CRITICAL**: Severe impact, immediate action required

### API Endpoints
```
POST /api/advanced/simulation/run/
Body: {"scenario": {...}, "duration_days": 30}

GET /api/advanced/simulation/history/?limit=10

POST /api/advanced/simulation/compare/
Body: {"scenarios": [{...}, {...}]}
```

### UI Location
Navigate to: **Advanced Features → Digital Twin**

---

## 4. Immutable Audit Trail (Proof of Agency)

### Description
A blockchain-inspired tamper-evident logging system that records every agent decision with cryptographic integrity.

### Architecture
- **Blockchain Structure**: Each audit entry is a block linked to the previous
- **SHA-256 Hashing**: Every block has a unique hash
- **Chain Verification**: Previous hash links ensure integrity
- **Immutability**: Any tampering breaks the chain

### What Gets Logged
Every "Sense-Think-Act" cycle:
- **Sense**: Raw data collected (queries, API calls, sensors)
- **Think**: LLM prompts, reasoning process, decisions made
- **Act**: Actions taken and their results

### Integrity Verification
- Verifies each block's hash
- Checks chain linkage between blocks
- Identifies corrupted blocks
- Detects chain breaks

### Features
- **Cycle Search**: Filter by time, action type, or content
- **Audit Reports**: Generate comprehensive reports
- **Export**: Download audit trails as JSON
- **Real-time Verification**: Check integrity at any time

### API Endpoints
```
GET /api/advanced/audit/verify/
GET /api/advanced/audit/cycles/?limit=50
POST /api/advanced/audit/search/
Body: {"filters": {...}}

GET /api/advanced/audit/report/?start_time=...&end_time=...
GET /api/advanced/audit/cycle/<cycle_id>/
```

### UI Location
Navigate to: **Advanced Features → Audit Trail**

---

## Integration with Existing System

### Automatic Logging
All advanced features automatically log to the audit trail:
- SQL Healer logs healing attempts and results
- Boardroom logs agent analyses and decisions
- Digital Twin logs simulations and predictions

### Seamless UI Integration
- New "Advanced Features" section in sidebar
- Consistent design with existing dashboard
- Same color scheme and typography
- Responsive and mobile-friendly

### Backend Architecture
```
App/
├── self_healing_sql.py      # SQL healing logic
├── agentic_boardroom.py     # Multi-agent system
├── digital_twin.py          # Simulation engine
├── audit_trail.py           # Immutable logging
└── views.py                 # API endpoints
```

---

## Configuration

### Environment Variables Required
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### Dependencies
All required dependencies are already in the project:
- `google-generativeai` for AI capabilities
- `django` for web framework
- `requests` for HTTP calls
- Standard Python libraries (json, hashlib, datetime, etc.)

---

## Usage Examples

### 1. Self-Healing SQL
```javascript
// Execute a potentially broken query
const result = await fetch('/api/advanced/sql/healing/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        query: 'SELECT * FROM prodcuts WHERE price > 100'  // Typo: prodcuts
    })
});

// System automatically detects typo, fixes to 'products', and executes
```

### 2. Agentic Boardroom
```javascript
// Convene boardroom for hurricane scenario
const session = await fetch('/api/advanced/boardroom/convene/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        situation: {
            type: 'weather_risk',
            description: 'Category 5 hurricane approaching Florida hub',
            severity: 9,
            timeline: '24 hours'
        }
    })
});

// Returns: Logistics analysis, Finance analysis, Executive decision
```

### 3. Digital Twin
```javascript
// Simulate 20% raw material price increase
const simulation = await fetch('/api/advanced/simulation/run/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        scenario: {
            raw_material_price_increase: 20
        },
        duration_days: 30
    })
});

// Returns: Impact analysis, risk level, recommendations
```

### 4. Audit Trail
```javascript
// Verify audit integrity
const integrity = await fetch('/api/advanced/audit/verify/');

// Search audit trail
const results = await fetch('/api/advanced/audit/search/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        filters: {
            start_time: '2026-01-01T00:00:00',
            action_type: 'simulation'
        }
    })
});
```

---

## Security Considerations

### Audit Trail
- **Immutable**: Once written, cannot be modified
- **Tamper-Evident**: Any changes break the cryptographic chain
- **Persistent**: Stored in `audit_trail.json` file
- **Exportable**: Can be backed up and archived

### SQL Healer
- **Sandboxed**: Only executes against configured database
- **Logged**: All healing attempts are audited
- **Limited Retries**: Maximum 3 attempts to prevent infinite loops

### Boardroom
- **Deterministic**: Same situation yields consistent analysis
- **Transparent**: All agent reasoning is logged
- **Auditable**: Every decision is recorded

### Digital Twin
- **Read-Only**: Simulations don't affect real data
- **Isolated**: Runs in virtual environment
- **Validated**: Results are sanity-checked

---

## Performance Considerations

### SQL Healer
- Schema caching reduces database queries
- Maximum 3 retry attempts
- Typical healing time: 2-5 seconds

### Boardroom
- Parallel agent analysis
- Typical session time: 5-10 seconds
- Results cached for history

### Digital Twin
- Lightweight calculations
- AI predictions cached
- Typical simulation time: 3-7 seconds

### Audit Trail
- Append-only operations
- Efficient hash calculations
- Periodic integrity checks recommended

---

## Troubleshooting

### SQL Healer Not Working
- Check GEMINI_API_KEY is set
- Verify database connection
- Check healing logs for details

### Boardroom Timeout
- Increase AI timeout settings
- Check network connectivity
- Simplify situation description

### Digital Twin Inaccurate
- Update baseline metrics
- Provide more scenario details
- Increase simulation duration

### Audit Trail Corrupted
- Check file permissions
- Verify disk space
- Restore from backup

---

## Future Enhancements

### Planned Features
1. **Multi-SQL Batch Healing**: Heal multiple queries simultaneously
2. **Boardroom Voting**: Add more agents with voting mechanism
3. **Digital Twin ML**: Use machine learning for better predictions
4. **Audit Trail Blockchain**: Distribute across multiple nodes

### Potential Integrations
- Real-time alerting for critical decisions
- Slack/Teams notifications for boardroom sessions
- Automated simulation scheduling
- Audit trail compliance reporting

---

## Support

For issues or questions:
1. Check the audit trail for error logs
2. Review API endpoint responses
3. Examine browser console for frontend errors
4. Check Django logs for backend errors

---

## License

Part of the Agent-21 system. All rights reserved.

---

## Changelog

### Version 1.0.0 (2026-01-06)
- Initial implementation of all four advanced features
- Complete UI integration
- Full API documentation
- Comprehensive testing

---

**Built with ❤️ for HackSymmetric Agent-21**

