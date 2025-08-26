"""Production execution filtering service"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProductionExecutionFilter:
    """Service for filtering production executions from test/dev runs"""
    
    def __init__(self):
        # Default patterns for identifying test/dev workflows
        self.test_workflow_patterns = [
            r".*test.*",
            r".*dev.*", 
            r".*debug.*",
            r".*sample.*",
            r".*demo.*",
            r".*example.*",
            r".*staging.*",
            r".*temp.*",
            r".*experimental.*"
        ]
        
        # Default patterns for production workflows
        self.production_workflow_patterns = [
            r".*prod.*",
            r".*production.*",
            r".*live.*",
            r".*main.*",
            r".*master.*"
        ]
        
        # Execution modes that are typically not production
        self.non_production_modes = {
            "manual",  # Manual executions are typically for testing
            "retry"    # Retries might be included or excluded based on policy
        }
        
        # Workflow tags that indicate test/dev environments
        self.test_tags = {
            "test", "dev", "development", "debug", "staging", 
            "demo", "sample", "experimental", "temp", "temporary"
        }
        
        # Production indicators in workflow tags
        self.production_tags = {
            "production", "prod", "live", "main", "stable", "release"
        }
    
    def is_production_execution(
        self,
        execution: Dict[str, Any],
        workflow: Optional[Dict[str, Any]] = None,
        custom_filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Determine if an execution should be considered production
        
        Args:
            execution: n8n execution data
            workflow: n8n workflow data (optional)
            custom_filters: Custom filtering rules (optional)
        
        Returns:
            True if execution is production, False otherwise
        """
        # Apply custom filters if provided
        if custom_filters:
            custom_result = self._apply_custom_filters(execution, workflow, custom_filters)
            if custom_result is not None:
                return custom_result
        
        # Check execution mode
        if not self._is_production_mode(execution):
            return False
        
        # Check workflow indicators if workflow data is available
        if workflow:
            if not self._is_production_workflow(workflow):
                return False
        
        # Check execution timing patterns (business hours vs off-hours)
        if not self._is_production_timing(execution):
            return False
        
        # Check for test/debug indicators in execution data
        if self._has_test_indicators(execution):
            return False
        
        # Default to production if no test indicators found
        return True
    
    def _apply_custom_filters(
        self,
        execution: Dict[str, Any],
        workflow: Optional[Dict[str, Any]],
        custom_filters: Dict[str, Any]
    ) -> Optional[bool]:
        """Apply custom filtering rules"""
        
        # Exclude manual executions if specified
        if custom_filters.get("exclude_manual", False):
            execution_mode = execution.get("mode", "").lower()
            if execution_mode == "manual":
                return False
        
        # Check workflow name patterns
        if workflow:
            workflow_name = workflow.get("name", "").lower()
            
            # Exclude patterns
            exclude_patterns = custom_filters.get("exclude_workflow_patterns", [])
            for pattern in exclude_patterns:
                if re.search(pattern.lower(), workflow_name):
                    return False
            
            # Include patterns (if specified, only these are considered production)
            include_patterns = custom_filters.get("include_workflow_patterns", [])
            if include_patterns:
                for pattern in include_patterns:
                    if re.search(pattern.lower(), workflow_name):
                        return True
                # If include patterns specified but none matched, exclude
                return False
        
        # Exclude test workflows if specified
        if custom_filters.get("exclude_test_workflows", False) and workflow:
            if not self._is_production_workflow(workflow):
                return False
        
        return None  # No custom filter applied
    
    def _is_production_mode(self, execution: Dict[str, Any]) -> bool:
        """Check if execution mode indicates production usage"""
        execution_mode = execution.get("mode", "").lower()
        
        # Manual executions are typically for testing
        if execution_mode in self.non_production_modes:
            return False
        
        # Webhook and trigger executions are typically production
        if execution_mode in ["webhook", "trigger"]:
            return True
        
        return True  # Default to production for unknown modes
    
    def _is_production_workflow(self, workflow: Dict[str, Any]) -> bool:
        """Check if workflow indicates production usage"""
        workflow_name = workflow.get("name", "").lower()
        
        # Check for explicit production patterns first
        for pattern in self.production_workflow_patterns:
            if re.search(pattern, workflow_name):
                return True
        
        # Check for test patterns
        for pattern in self.test_workflow_patterns:
            if re.search(pattern, workflow_name):
                return False
        
        # Check workflow tags if available
        workflow_tags = workflow.get("tags", [])
        if isinstance(workflow_tags, list):
            tag_names = [tag.get("name", "").lower() if isinstance(tag, dict) else str(tag).lower() for tag in workflow_tags]
            
            # Check for production tags
            if any(tag in self.production_tags for tag in tag_names):
                return True
            
            # Check for test tags
            if any(tag in self.test_tags for tag in tag_names):
                return False
        
        # Check if workflow is active (inactive workflows might be for testing)
        if not workflow.get("active", True):
            return False
        
        return True  # Default to production if no clear indicators
    
    def _is_production_timing(self, execution: Dict[str, Any]) -> bool:
        """Check if execution timing suggests production usage"""
        started_at = execution.get("startedAt")
        if not started_at:
            return True  # No timing info, assume production
        
        try:
            # Parse execution time
            exec_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            
            # Check if execution is during typical business hours
            # This is a simple heuristic - you might want to customize based on timezone
            hour = exec_time.hour
            
            # Very late night or early morning executions might be automated (production)
            if hour >= 22 or hour <= 6:
                return True
            
            # Business hours executions could be either, don't filter based on this alone
            return True
            
        except Exception:
            return True  # If we can't parse time, assume production
    
    def _has_test_indicators(self, execution: Dict[str, Any]) -> bool:
        """Check for test indicators in execution data"""
        
        # Check for test-related error messages
        error_message = execution.get("error", {}).get("message", "") if execution.get("error") else ""
        if error_message:
            error_lower = error_message.lower()
            test_keywords = ["test", "debug", "sample", "demo", "example"]
            if any(keyword in error_lower for keyword in test_keywords):
                return True
        
        # Check execution data for test indicators
        execution_data = execution.get("data", {})
        if isinstance(execution_data, dict):
            # Look for test-related keys or values
            data_str = str(execution_data).lower()
            if "test" in data_str or "debug" in data_str:
                return True
        
        return False
    
    def get_production_filter_config(self, client_id: int) -> Dict[str, Any]:
        """Get production filter configuration for a client"""
        # This could be customized per client in the future
        # For now, return default configuration
        return {
            "exclude_manual": True,
            "exclude_test_workflows": True,
            "test_workflow_patterns": self.test_workflow_patterns,
            "production_workflow_patterns": self.production_workflow_patterns,
            "test_tags": list(self.test_tags),
            "production_tags": list(self.production_tags)
        }
    
    def validate_execution_batch(
        self,
        executions: List[Dict[str, Any]],
        workflows: Dict[str, Dict[str, Any]],
        custom_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter a batch of executions to include only production runs
        
        Args:
            executions: List of n8n execution data
            workflows: Dictionary mapping workflow IDs to workflow data
            custom_filters: Custom filtering rules
        
        Returns:
            Filtered list of production executions
        """
        production_executions = []
        
        for execution in executions:
            workflow_id = execution.get("workflowId")
            workflow = workflows.get(str(workflow_id)) if workflow_id else None
            
            if self.is_production_execution(execution, workflow, custom_filters):
                production_executions.append(execution)
        
        logger.info(
            f"Filtered {len(executions)} executions to {len(production_executions)} production executions "
            f"({len(production_executions)/len(executions)*100:.1f}% production rate)"
        )
        
        return production_executions


# Global filter instance
production_filter = ProductionExecutionFilter()