"""
Self-Healing SQL Re-Sensing Module
Autonomous SQL debugging and correction system
"""
import json
import re
import requests
from typing import Dict, List, Any, Tuple
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class SQLDebuggerAgent:
    """Specialized agent for autonomous SQL debugging and correction"""
    
    def __init__(self, db_endpoint: str = "http://172.16.17.18:8000/api/query/"):
        self.db_endpoint = db_endpoint
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.schema_cache = {}
        self.max_retries = 3
        
    def execute_with_healing(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL with autonomous self-healing capability
        Returns: {
            'success': bool,
            'data': list,
            'healing_log': list,
            'attempts': int,
            'final_query': str
        }
        """
        healing_log = []
        attempts = 0
        
        while attempts < self.max_retries:
            attempts += 1
            
            try:
                # Attempt execution
                result = self._execute_sql(sql_query)
                
                if result['success']:
                    return {
                        'success': True,
                        'data': result['data'],
                        'healing_log': healing_log,
                        'attempts': attempts,
                        'final_query': sql_query
                    }
                else:
                    # Error detected - activate healing
                    error_msg = result.get('error', 'Unknown error')
                    healing_log.append({
                        'attempt': attempts,
                        'query': sql_query,
                        'error': error_msg,
                        'action': 'analyzing'
                    })
                    
                    # Diagnose and fix
                    fixed_query = self._diagnose_and_fix(sql_query, error_msg)
                    
                    if fixed_query == sql_query:
                        # No fix found
                        healing_log.append({
                            'attempt': attempts,
                            'action': 'no_fix_found',
                            'message': 'Unable to automatically fix query'
                        })
                        break
                    
                    healing_log.append({
                        'attempt': attempts,
                        'action': 'rewritten',
                        'new_query': fixed_query
                    })
                    
                    sql_query = fixed_query
                    
            except Exception as e:
                healing_log.append({
                    'attempt': attempts,
                    'error': str(e),
                    'action': 'exception'
                })
                break
        
        return {
            'success': False,
            'data': [],
            'healing_log': healing_log,
            'attempts': attempts,
            'final_query': sql_query,
            'error': 'Max retries exceeded or unfixable error'
        }
    
    def _execute_sql(self, query: str) -> Dict[str, Any]:
        """Execute SQL query against the database"""
        try:
            response = requests.post(
                self.db_endpoint,
                json={'query': query},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data.get('query_results', data.get('data', []))
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _diagnose_and_fix(self, query: str, error: str) -> str:
        """Use AI to diagnose and fix SQL errors"""
        
        # Get schema information
        schema_info = self._get_schema_info(query)
        
        # Prepare prompt for Gemini
        prompt = f"""You are an expert SQL debugger. A query has failed with an error.

FAILED QUERY:
{query}

ERROR MESSAGE:
{error}

DATABASE SCHEMA INFORMATION:
{schema_info}

Your task:
1. Analyze the error
2. Identify the root cause
3. Rewrite the SQL query to fix the issue
4. Return ONLY the corrected SQL query, nothing else

CORRECTED QUERY:"""
        
        try:
            response = self.model.generate_content(prompt)
            fixed_query = response.text.strip()
            
            # Clean up the response (remove markdown, etc.)
            fixed_query = re.sub(r'```sql\s*', '', fixed_query)
            fixed_query = re.sub(r'```\s*', '', fixed_query)
            fixed_query = fixed_query.strip()
            
            return fixed_query
        except Exception as e:
            print(f"AI diagnosis failed: {e}")
            return query  # Return original if AI fails
    
    def _get_schema_info(self, query: str) -> str:
        """Extract and cache schema information for relevant tables"""
        
        # Extract table names from query
        table_pattern = r'FROM\s+(["\']?)(\w+)\1|JOIN\s+(["\']?)(\w+)\3'
        matches = re.findall(table_pattern, query, re.IGNORECASE)
        tables = [m[1] or m[3] for m in matches if m[1] or m[3]]
        
        schema_info = []
        
        for table in tables:
            if table not in self.schema_cache:
                # Fetch schema
                schema_query = f'SELECT * FROM "{table}" LIMIT 1'
                result = self._execute_sql(schema_query)
                
                if result['success'] and result['data']:
                    columns = list(result['data'][0].keys())
                    self.schema_cache[table] = columns
                else:
                    self.schema_cache[table] = []
            
            if self.schema_cache[table]:
                schema_info.append(f"Table '{table}': {', '.join(self.schema_cache[table])}")
        
        return '\n'.join(schema_info) if schema_info else "Schema information unavailable"


# Global instance
sql_healer = SQLDebuggerAgent()


def execute_self_healing_query(query: str) -> Dict[str, Any]:
    """
    Public interface for self-healing SQL execution
    """
    return sql_healer.execute_with_healing(query)
