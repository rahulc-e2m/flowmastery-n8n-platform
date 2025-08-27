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
        # Must be a completed execution (finished, regardless of success/failure)
        # Also include executions with definitive status even if finished=false
        finished = execution.get('finished')
        status = execution.get('status', '').lower()
        started_at = execution.get('startedAt')
        stopped_at = execution.get('stoppedAt')
        
        # Consider execution completed if:
        # 1. finished=true, OR
        # 2. has definitive status (success/error), OR  
        # 3. has both start and stop times (execution ran and completed)
        is_completed = (
            finished or 
            status in ['success', 'error', 'crashed', 'canceled', 'cancelled'] or
            (started_at and stopped_at)
        )
        
        if not is_completed:
            return False
        
        # Apply custom filters if provided
        if custom_filters:
            custom_result = self._apply_custom_filters(execution, workflow, custom_filters)
            if custom_result is not None:
                return custom_result
        
        # Check execution mode (primary filter)
        if not self._is_production_mode(execution):
            return False
        
        # Check workflow indicators if workflow data is available
        if workflow:
            if not self._is_production_workflow(workflow):
                return False
        
        # Check execution timing patterns (business hours vs off-hours)
        if not self._is_production_timing(execution):
            return False
        
        # Check for explicit test/debug indicators in execution data
        # Note: We're more conservative here to avoid excluding legitimate production errors
        if self._has_test_indicators(execution):
            return False
        
        # Include both successful AND failed production executions
        # Production errors are important for monitoring and should be tracked
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
        
        # Explicitly non-production modes
        if execution_mode in self.non_production_modes:
            return False
        
        # Explicitly production modes (automated executions)
        production_modes = ["webhook", "trigger", "integrated"]
        if execution_mode in production_modes:
            return True
        
        # Other modes (cli, error, internal) - default to production
        # These could be legitimate production executions or system operations
        return True
    
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
        
        # Check for test-related error messages (but be more selective)
        error_message = execution.get("error", {}).get("message", "") if execution.get("error") else ""
        if error_message:
            error_lower = error_message.lower()
            # Only exclude if error message explicitly mentions testing context
            explicit_test_keywords = ["test mode", "testing environment", "debug mode", "sample data", "demo execution"]
            if any(keyword in error_lower for keyword in explicit_test_keywords):
                return True
        
        # Check execution data for test indicators (but avoid false positives)
        execution_data = execution.get("data", {})
        if isinstance(execution_data, dict):
            # Only look for explicit test indicators, not just the word "test"
            data_str = str(execution_data).lower()
            explicit_indicators = ["test_mode", "debug_mode", "sample_data", "demo_run"]
            if any(indicator in data_str for indicator in explicit_indicators):
                return True
        
        return False
    
    def get_production_filter_config(self, client_id: int) -> Dict[str, Any]:
        """Get production filter configuration for a client"""
        # This could be customized per client in the future
        # For now, return default configuration that includes both success and error executions
        return {
            "exclude_manual": True,
            "exclude_test_workflows": True,
            "include_error_executions": True,  # Important: include production errors
            "include_success_executions": True,
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
        
        # Count execution types for better logging
        def is_success_execution(e):
            status = e.get('status', '').lower()
            if status:
                return status == 'success'
            # If finished=True and no error field, it's successful
            return e.get('finished') and not e.get('error')
        
        def is_error_execution(e):
            status = e.get('status', '').lower()
            if status:
                return status in ['error', 'crashed', 'canceled', 'cancelled']
            # If finished=False but has start and stop times, likely failed
            # Or if finished=True but has error field
            started_at = e.get('startedAt')
            stopped_at = e.get('stoppedAt')
            finished = e.get('finished')
            has_error = 'error' in e
            
            return (
                (finished and has_error) or  # Finished with error
                (not finished and started_at and stopped_at)  # Started and stopped but not finished
            )
        
        success_count = len([e for e in production_executions if is_success_execution(e)])
        error_count = len([e for e in production_executions if is_error_execution(e)])
        
        logger.info(
            f"Filtered {len(executions)} executions to {len(production_executions)} production executions "
            f"({len(production_executions)/max(1, len(executions))*100:.1f}% production rate) - "
            f"Success: {success_count}, Errors: {error_count}"
        )
        
        return production_executions


# Global filter instance
production_filter = ProductionExecutionFilter()