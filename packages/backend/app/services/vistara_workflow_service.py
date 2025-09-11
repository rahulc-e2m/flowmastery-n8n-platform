"""
Vistara Workflow Service - Handles metrics synchronization and operations
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.vistara_workflow import VistaraWorkflow

logger = logging.getLogger(__name__)


class VistaraWorkflowService:
    """Service for managing Vistara workflows with metrics synchronization"""
    
    @staticmethod
    async def sync_workflow_metrics(db: AsyncSession, vistara_workflow: VistaraWorkflow) -> bool:
        """
        Sync metrics for a single Vistara workflow from its original workflow
        
        Args:
            db: Database session
            vistara_workflow: VistaraWorkflow instance to sync
            
        Returns:
            bool: True if sync was successful, False otherwise
        """
        try:
            if not vistara_workflow.original_workflow_id:
                logger.debug(f"Vistara workflow {vistara_workflow.id} has no original workflow linked")
                return False
            
            # Use the model's sync method
            sync_success = await vistara_workflow.update_metrics_from_original(db)
            
            if sync_success:
                logger.debug(f"Successfully synced metrics for Vistara workflow {vistara_workflow.id}")
            else:
                logger.warning(f"Failed to sync metrics for Vistara workflow {vistara_workflow.id}")
                
            return sync_success
            
        except Exception as e:
            logger.error(f"Error syncing metrics for Vistara workflow {vistara_workflow.id}: {e}")
            return False
    
    @staticmethod
    async def sync_all_linked_workflows(db: AsyncSession) -> Dict[str, Any]:
        """
        Sync metrics for all Vistara workflows that have original workflow links
        
        Args:
            db: Database session
            
        Returns:
            Dict containing sync results and statistics
        """
        try:
            # Get all active Vistara workflows with original workflow links
            query = select(VistaraWorkflow).where(
                and_(
                    VistaraWorkflow.is_active == True,
                    VistaraWorkflow.original_workflow_id.isnot(None)
                )
            ).options(selectinload(VistaraWorkflow.original_workflow))
            
            result = await db.execute(query)
            linked_workflows = result.scalars().all()
            
            sync_results = {
                "total_workflows": len(linked_workflows),
                "synced_successfully": 0,
                "sync_failed": 0,
                "no_metrics_found": 0,
                "errors": []
            }
            
            for vw in linked_workflows:
                try:
                    sync_success = await VistaraWorkflowService.sync_workflow_metrics(db, vw)
                    if sync_success:
                        sync_results["synced_successfully"] += 1
                    else:
                        sync_results["no_metrics_found"] += 1
                        
                except Exception as e:
                    sync_results["sync_failed"] += 1
                    sync_results["errors"].append(f"Workflow {vw.id}: {str(e)}")
                    logger.error(f"Failed to sync Vistara workflow {vw.id}: {e}")
            
            # Commit all changes
            await db.commit()
            
            logger.info(
                f"Vistara metrics sync completed: "
                f"{sync_results['synced_successfully']} synced, "
                f"{sync_results['sync_failed']} failed, "
                f"{sync_results['no_metrics_found']} with no metrics"
            )
            
            return sync_results
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error during bulk Vistara workflow sync: {e}")
            return {
                "total_workflows": 0,
                "synced_successfully": 0,
                "sync_failed": 0,
                "no_metrics_found": 0,
                "errors": [str(e)]
            }
    
    @staticmethod
    async def get_workflows_with_fresh_metrics(
        db: AsyncSession, 
        category_id: Optional[str] = None,
        is_featured: Optional[bool] = None,
        sync_before_return: bool = True
    ) -> List[VistaraWorkflow]:
        """
        Get Vistara workflows with optionally fresh-synced metrics
        
        Args:
            db: Database session
            category_id: Optional category filter
            is_featured: Optional featured filter
            sync_before_return: Whether to sync metrics before returning data
            
        Returns:
            List of VistaraWorkflow instances
        """
        try:
            # Build query
            query = select(VistaraWorkflow).where(VistaraWorkflow.is_active == True)
            
            if category_id:
                query = query.where(VistaraWorkflow.category_id == category_id)
            
            if is_featured is not None:
                query = query.where(VistaraWorkflow.is_featured == is_featured)
            
            query = query.options(
                selectinload(VistaraWorkflow.category_ref),
                selectinload(VistaraWorkflow.original_workflow)
            ).order_by(VistaraWorkflow.display_order, VistaraWorkflow.workflow_name)
            
            result = await db.execute(query)
            workflows = result.scalars().all()
            
            # Sync metrics if requested
            if sync_before_return:
                synced_count = 0
                for vw in workflows:
                    if vw.original_workflow_id:
                        try:
                            sync_success = await VistaraWorkflowService.sync_workflow_metrics(db, vw)
                            if sync_success:
                                synced_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to sync workflow {vw.id} during fetch: {e}")
                
                # Commit synced changes
                if synced_count > 0:
                    await db.commit()
                    logger.debug(f"Synced {synced_count} workflows during fetch")
            
            return workflows
            
        except Exception as e:
            if sync_before_return:
                await db.rollback()
            logger.error(f"Error fetching Vistara workflows with fresh metrics: {e}")
            raise
    
    @staticmethod
    async def get_workflow_with_fresh_metrics(
        db: AsyncSession, 
        workflow_id: str,
        sync_before_return: bool = True
    ) -> Optional[VistaraWorkflow]:
        """
        Get a single Vistara workflow with optionally fresh-synced metrics
        
        Args:
            db: Database session
            workflow_id: ID of the workflow to fetch
            sync_before_return: Whether to sync metrics before returning data
            
        Returns:
            VistaraWorkflow instance or None if not found
        """
        try:
            # Get the workflow
            query = select(VistaraWorkflow).where(VistaraWorkflow.id == workflow_id).options(
                selectinload(VistaraWorkflow.category_ref),
                selectinload(VistaraWorkflow.original_workflow)
            )
            
            result = await db.execute(query)
            workflow = result.scalar_one_or_none()
            
            if not workflow:
                return None
            
            # Sync metrics if requested and workflow is linked
            if sync_before_return and workflow.original_workflow_id:
                try:
                    sync_success = await VistaraWorkflowService.sync_workflow_metrics(db, workflow)
                    if sync_success:
                        await db.commit()
                        logger.debug(f"Synced metrics for workflow {workflow_id}")
                except Exception as e:
                    logger.warning(f"Failed to sync workflow {workflow_id} during fetch: {e}")
                    await db.rollback()
            
            return workflow
            
        except Exception as e:
            if sync_before_return:
                await db.rollback()
            logger.error(f"Error fetching Vistara workflow {workflow_id} with fresh metrics: {e}")
            raise


# Global service instance
vistara_workflow_service = VistaraWorkflowService()
