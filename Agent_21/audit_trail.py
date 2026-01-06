"""
Immutable Audit Trail - Proof of Agency
Tamper-evident logging of all agent decisions and actions
"""
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
import os


class AuditBlock:
    """Represents a single immutable audit entry"""
    
    def __init__(self, cycle_id: str, sense_data: Dict, think_data: Dict, 
                 act_data: Dict, previous_hash: str = "0"):
        self.cycle_id = cycle_id
        self.timestamp = datetime.now().isoformat()
        self.sense_data = sense_data
        self.think_data = think_data
        self.act_data = act_data
        self.previous_hash = previous_hash
        self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block"""
        block_string = json.dumps({
            'cycle_id': self.cycle_id,
            'timestamp': self.timestamp,
            'sense': self.sense_data,
            'think': self.think_data,
            'act': self.act_data,
            'previous_hash': self.previous_hash
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary"""
        return {
            'cycle_id': self.cycle_id,
            'timestamp': self.timestamp,
            'sense': self.sense_data,
            'think': self.think_data,
            'act': self.act_data,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }
    
    def verify(self) -> bool:
        """Verify block integrity"""
        return self.hash == self._calculate_hash()


class ImmutableAuditTrail:
    """Blockchain-inspired immutable audit log"""
    
    def __init__(self, storage_path: str = "audit_trail.json"):
        self.storage_path = storage_path
        self.chain: List[AuditBlock] = []
        self._load_chain()
    
    def log_cycle(self, sense_data: Dict, think_data: Dict, act_data: Dict) -> str:
        """
        Log a complete Sense-Think-Act cycle
        
        Args:
            sense_data: Raw data sensed (queries, API calls, etc.)
            think_data: LLM prompts, reasoning, decisions
            act_data: Actions taken and their results
            
        Returns:
            cycle_id: Unique identifier for this cycle
        """
        cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        previous_hash = self.chain[-1].hash if self.chain else "0"
        
        block = AuditBlock(
            cycle_id=cycle_id,
            sense_data=sense_data,
            think_data=think_data,
            act_data=act_data,
            previous_hash=previous_hash
        )
        
        self.chain.append(block)
        self._save_chain()
        
        return cycle_id
    
    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify the integrity of the entire audit trail
        
        Returns:
            {
                'valid': bool,
                'total_blocks': int,
                'corrupted_blocks': list,
                'chain_breaks': list
            }
        """
        if not self.chain:
            return {
                'valid': True,
                'total_blocks': 0,
                'corrupted_blocks': [],
                'chain_breaks': []
            }
        
        corrupted_blocks = []
        chain_breaks = []
        
        for i, block in enumerate(self.chain):
            # Verify block hash
            if not block.verify():
                corrupted_blocks.append({
                    'index': i,
                    'cycle_id': block.cycle_id,
                    'reason': 'Hash mismatch'
                })
            
            # Verify chain linkage
            if i > 0:
                if block.previous_hash != self.chain[i-1].hash:
                    chain_breaks.append({
                        'index': i,
                        'cycle_id': block.cycle_id,
                        'reason': 'Previous hash mismatch'
                    })
        
        return {
            'valid': len(corrupted_blocks) == 0 and len(chain_breaks) == 0,
            'total_blocks': len(self.chain),
            'corrupted_blocks': corrupted_blocks,
            'chain_breaks': chain_breaks
        }
    
    def get_cycle(self, cycle_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific cycle by ID"""
        for block in self.chain:
            if block.cycle_id == cycle_id:
                return block.to_dict()
        return None
    
    def get_recent_cycles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit cycles"""
        return [block.to_dict() for block in self.chain[-limit:]]
    
    def search_cycles(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search audit trail with filters
        
        Filters:
            - start_time: ISO timestamp
            - end_time: ISO timestamp
            - action_type: string
            - contains_text: string to search in think/act data
        """
        results = []
        
        for block in self.chain:
            match = True
            
            if 'start_time' in filters:
                if block.timestamp < filters['start_time']:
                    match = False
            
            if 'end_time' in filters:
                if block.timestamp > filters['end_time']:
                    match = False
            
            if 'action_type' in filters:
                if block.act_data.get('type') != filters['action_type']:
                    match = False
            
            if 'contains_text' in filters:
                text = filters['contains_text'].lower()
                block_text = json.dumps(block.to_dict()).lower()
                if text not in block_text:
                    match = False
            
            if match:
                results.append(block.to_dict())
        
        return results
    
    def export_audit_report(self, start_time: Optional[str] = None, 
                           end_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive audit report
        """
        filters = {}
        if start_time:
            filters['start_time'] = start_time
        if end_time:
            filters['end_time'] = end_time
        
        cycles = self.search_cycles(filters) if filters else [b.to_dict() for b in self.chain]
        
        # Analyze cycles
        total_cycles = len(cycles)
        action_types = {}
        
        for cycle in cycles:
            action_type = cycle['act'].get('type', 'unknown')
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        integrity = self.verify_integrity()
        
        return {
            'report_generated': datetime.now().isoformat(),
            'period': {
                'start': start_time or (cycles[0]['timestamp'] if cycles else None),
                'end': end_time or (cycles[-1]['timestamp'] if cycles else None)
            },
            'summary': {
                'total_cycles': total_cycles,
                'action_breakdown': action_types,
                'integrity_status': 'VALID' if integrity['valid'] else 'COMPROMISED'
            },
            'integrity_check': integrity,
            'cycles': cycles
        }
    
    def _save_chain(self):
        """Persist chain to disk"""
        try:
            data = [block.to_dict() for block in self.chain]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving audit trail: {e}")
    
    def _load_chain(self):
        """Load chain from disk"""
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for block_data in data:
                block = AuditBlock(
                    cycle_id=block_data['cycle_id'],
                    sense_data=block_data['sense'],
                    think_data=block_data['think'],
                    act_data=block_data['act'],
                    previous_hash=block_data['previous_hash']
                )
                # Restore original timestamp and hash
                block.timestamp = block_data['timestamp']
                block.hash = block_data['hash']
                self.chain.append(block)
        except Exception as e:
            print(f"Error loading audit trail: {e}")


# Global audit trail instance
audit_trail = ImmutableAuditTrail()


def log_agent_cycle(sense: Dict, think: Dict, act: Dict) -> str:
    """
    Public interface to log an agent cycle
    
    Example:
        log_agent_cycle(
            sense={'query': 'SELECT * FROM anomalies', 'result': [...]},
            think={'prompt': '...', 'llm_response': '...', 'decision': '...'},
            act={'type': 'email_alert', 'result': 'success'}
        )
    """
    return audit_trail.log_cycle(sense, think, act)


def verify_audit_integrity() -> Dict[str, Any]:
    """
    Verify the integrity of the audit trail
    """
    return audit_trail.verify_integrity()


def get_audit_cycles(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent audit cycles
    """
    return audit_trail.get_recent_cycles(limit)


def search_audit_trail(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Search the audit trail
    """
    return audit_trail.search_cycles(filters)


def generate_audit_report(start_time: Optional[str] = None, 
                         end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive audit report
    """
    return audit_trail.export_audit_report(start_time, end_time)


def get_cycle_details(cycle_id: str) -> Optional[Dict[str, Any]]:
    """
    Get details of a specific cycle
    """
    return audit_trail.get_cycle(cycle_id)
