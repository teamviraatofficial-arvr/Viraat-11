from typing import Dict, Optional, Tuple
from loguru import logger

class VisualController:
    """Controller for determining 3D visualization intent and asset mapping."""
    
    def __init__(self):
        # Map keywords to 3D asset IDs and types
        # Type: 'weapon', 'vehicle', 'structure'
        self.model_registry = {
            "ak-47": {"id": "ak47", "type": "weapon", "name": "AK-47 Assault Rifle"},
            "ak47": {"id": "ak47", "type": "weapon", "name": "AK-47 Assault Rifle"},
            "akm": {"id": "ak47", "type": "weapon", "name": "AKM Variant"},
            "m4a1": {"id": "m4a1", "type": "weapon", "name": "M4A1 Carbine"},
            "m4": {"id": "m4a1", "type": "weapon", "name": "M4A1 Carbine"},
            "cheytac": {"id": "dlq33", "type": "weapon", "name": "CheyTac M200 Intervention"},
            "dlq": {"id": "dlq33", "type": "weapon", "name": "DLQ-33 Sniper"},
            "l96a1": {"id": "l96a1", "type": "weapon", "name": "L96A1 Sniper"},
            "tank": {"id": "t90", "type": "vehicle", "name": "T-90 Main Battle Tank"},
            "bunker": {"id": "bunker", "type": "structure", "name": "Reinforced Bunker"},
        }
        
        # Keywords that strongly suggest a desire to SEE something
        self.visual_triggers = [
            "show me", "visual of", "3d model", "what does", "look like", 
            "display", "render", "view", "visualize"
        ]

    def analyze(self, query: str) -> Optional[Dict]:
        """
        Analyze query for visual intent.
        Returns a directive dict if a visual should be triggered, else None.
        """
        query_lower = query.lower()
        
        # 1. Check for explicit visual intent
        has_intent = any(trigger in query_lower for trigger in self.visual_triggers)
        
        # 2. Find mentioned entities
        matched_model = None
        for key, model_data in self.model_registry.items():
            if key in query_lower:
                matched_model = model_data
                break
        
        # 3. Decision Logic:
        # - If explicit intent + entity found -> SHOW
        # - If entity found but no explicit intent -> OPTIONAL (Frontend decides, usually hidden 'hint')
        # - For this implementation, we will be aggressive: if an entity is clearly the subject, show it.
        
        if matched_model:
            logger.info(f"Visual intent detected for: {matched_model['name']}")
            return {
                "type": "3d_view",
                "model_id": matched_model['id'],
                "model_type": matched_model['type'],
                "model_name": matched_model['name']
            }
            
        return None

# Global instance
visual_controller = VisualController()
