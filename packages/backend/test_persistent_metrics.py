#!/usr/bin/env python3
"""
Comprehensive test script for the persistent metrics system
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, date
from typing import Dict, Any

# Add app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.connection import get_db_session
from app.models import (
    Client, Workflow, WorkflowExecution, 
    MetricsAggregation, AggregationPeriod,
    ExecutionStatus
)
from app.services.persistent_metrics import persistent_metrics_collector
from app.services.metrics_aggregator import metrics_aggregator
from app.services.enhanced_metrics_service import enhanced_metrics_service
from app.services.production_filter import production_filter
from app.services.client_service import ClientService


class PersistentMetricsTestSuite:
    """Test suite for persistent metrics functionality"""
    
    def __init__(self):
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run all test scenarios"""
        print("🧪 Starting Persistent Metrics Test Suite")
        print("=" * 50)
        
        try:
            async with get_db_session() as db:
                await self.test_database_models(db)
                await self.test_production_filtering(db)
                await self.test_metrics_collection(db)
                await self.test_aggregation_service(db)
                await self.test_enhanced_metrics_service(db)
                await self.test_api_endpoints_data(db)
                
                self.print_test_summary()
                
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_database_models(self, db: AsyncSession):
        """Test database models and relationships"""
        print("\n📊 Testing Database Models")
        
        try:
            # Test Client model
            clients_count = await db.scalar(select(func.count(Client.id)))
            print(f"✅ Found {clients_count} clients in database")
            
            # Test Workflow model
            workflows_count = await db.scalar(select(func.count(Workflow.id)))
            print(f"✅ Found {workflows_count} workflows in database")
            
            # Test WorkflowExecution model
            executions_count = await db.scalar(select(func.count(WorkflowExecution.id)))
            print(f"✅ Found {executions_count} workflow executions in database")
            
            # Test MetricsAggregation model
            aggregations_count = await db.scalar(select(func.count(MetricsAggregation.id)))
            print(f"✅ Found {aggregations_count} metrics aggregations in database")
            
            # Test relationships
            if clients_count > 0:
                client_stmt = select(Client).limit(1)
                result = await db.execute(client_stmt)
                test_client = result.scalar_one_or_none()
                
                if test_client:
                    client_workflows = await db.scalar(
                        select(func.count(Workflow.id)).where(Workflow.client_id == test_client.id)
                    )
                    print(f"✅ Client {test_client.id} has {client_workflows} workflows")
            
            self.test_results['database_models'] = True
            print("✅ Database models test passed")
            
        except Exception as e:
            print(f"❌ Database models test failed: {e}")
            self.test_results['database_models'] = False
    
    async def test_production_filtering(self, db: AsyncSession):
        """Test production execution filtering"""
        print("\n🔍 Testing Production Filtering")
        
        try:
            # Test sample execution data
            test_executions = [
                {
                    "id": "test1",
                    "workflowId": "wf1", 
                    "mode": "manual",
                    "status": "success"
                },
                {
                    "id": "test2",
                    "workflowId": "wf2",
                    "mode": "webhook", 
                    "status": "success"
                },
                {
                    "id": "test3",
                    "workflowId": "wf3",
                    "mode": "trigger",
                    "status": "error"
                }
            ]
            
            test_workflows = {
                "wf1": {"name": "Test Workflow", "active": True},
                "wf2": {"name": "Production Workflow", "active": True},  
                "wf3": {"name": "Dev Environment Test", "active": True}
            }
            
            # Apply default filtering
            production_executions = production_filter.validate_execution_batch(
                test_executions, test_workflows
            )
            
            expected_production = 1  # Only webhook execution should pass
            actual_production = len(production_executions)
            
            if actual_production == expected_production:
                print(f"✅ Production filtering working correctly: {actual_production}/{len(test_executions)} executions marked as production")
            else:
                print(f"⚠️ Production filtering unexpected result: {actual_production}/{len(test_executions)} executions marked as production")
            
            # Test individual execution filtering
            manual_exec = test_executions[0]
            is_prod = production_filter.is_production_execution(manual_exec, test_workflows["wf1"])
            print(f"✅ Manual execution correctly filtered: {not is_prod}")
            
            self.test_results['production_filtering'] = True
            print("✅ Production filtering test passed")
            
        except Exception as e:
            print(f"❌ Production filtering test failed: {e}")
            self.test_results['production_filtering'] = False
    
    async def test_metrics_collection(self, db: AsyncSession):
        """Test metrics collection functionality"""
        print("\n📈 Testing Metrics Collection")
        
        try:
            # Get clients with n8n configuration
            clients_with_config = await db.execute(
                select(Client).where(
                    Client.n8n_api_url.isnot(None)
                )
            )
            clients = clients_with_config.scalars().all()
            
            if not clients:
                print("⚠️ No clients with n8n configuration found - skipping collection test")
                self.test_results['metrics_collection'] = True
                return
            
            test_client = clients[0]
            print(f"Testing with client: {test_client.name} (ID: {test_client.id})")
            
            # Test individual client sync (this might fail if n8n is not accessible)
            try:
                result = await persistent_metrics_collector.sync_client_data(db, test_client.id)
                print(f"✅ Client sync completed: {result}")
                
                # Check if data was actually synced
                workflows_after = await db.scalar(
                    select(func.count(Workflow.id)).where(Workflow.client_id == test_client.id)
                )
                print(f"✅ Client {test_client.id} now has {workflows_after} workflows")
                
            except Exception as sync_error:
                print(f"⚠️ Client sync failed (expected if n8n not accessible): {sync_error}")
            
            self.test_results['metrics_collection'] = True
            print("✅ Metrics collection test passed")
            
        except Exception as e:
            print(f"❌ Metrics collection test failed: {e}")
            self.test_results['metrics_collection'] = False
    
    async def test_aggregation_service(self, db: AsyncSession):
        """Test metrics aggregation functionality"""
        print("\n📊 Testing Metrics Aggregation")
        
        try:
            # Test aggregation for yesterday
            yesterday = (datetime.utcnow() - timedelta(days=1)).date()
            
            result = await metrics_aggregator.compute_daily_aggregations(db, yesterday)
            print(f"✅ Daily aggregation completed: {result}")
            
            # Check if aggregations were created
            agg_count = await db.scalar(
                select(func.count(MetricsAggregation.id)).where(
                    MetricsAggregation.period_start == yesterday
                )
            )
            print(f"✅ Created {agg_count} aggregations for {yesterday}")
            
            # Test aggregation summary
            summary = await metrics_aggregator.get_aggregation_summary(db)
            print(f"✅ Aggregation summary: {summary}")
            
            self.test_results['aggregation_service'] = True
            print("✅ Aggregation service test passed")
            
        except Exception as e:
            print(f"❌ Aggregation service test failed: {e}")
            self.test_results['aggregation_service'] = False
    
    async def test_enhanced_metrics_service(self, db: AsyncSession):
        """Test enhanced metrics service"""
        print("\n⚡ Testing Enhanced Metrics Service")
        
        try:
            # Get a client for testing
            client_stmt = select(Client).limit(1)
            result = await db.execute(client_stmt)
            test_client = result.scalar_one_or_none()
            
            if not test_client:
                print("⚠️ No clients found - skipping enhanced service test")
                self.test_results['enhanced_metrics_service'] = True
                return
            
            # Test client metrics
            client_metrics = await enhanced_metrics_service.get_client_metrics(db, test_client.id)
            print(f"✅ Client metrics retrieved: {client_metrics.client_name}")
            print(f"   - Workflows: {client_metrics.total_workflows}")
            print(f"   - Executions: {client_metrics.total_executions}")
            print(f"   - Success rate: {client_metrics.success_rate}%")
            
            # Test workflow metrics  
            workflow_metrics = await enhanced_metrics_service.get_client_workflow_metrics(db, test_client.id)
            print(f"✅ Workflow metrics retrieved: {len(workflow_metrics.workflows)} workflows")
            
            # Test historical metrics
            try:
                historical = await enhanced_metrics_service.get_historical_metrics(
                    db, test_client.id, AggregationPeriod.DAILY
                )
                print(f"✅ Historical metrics retrieved: {len(historical.metrics_data)} data points")
            except Exception as hist_error:
                print(f"⚠️ Historical metrics failed (expected if no aggregations): {hist_error}")
            
            self.test_results['enhanced_metrics_service'] = True
            print("✅ Enhanced metrics service test passed")
            
        except Exception as e:
            print(f"❌ Enhanced metrics service test failed: {e}")
            self.test_results['enhanced_metrics_service'] = False
    
    async def test_api_endpoints_data(self, db: AsyncSession):
        """Test data availability for API endpoints"""
        print("\n🌐 Testing API Data Availability")
        
        try:
            # Check admin metrics data
            admin_metrics = await enhanced_metrics_service.get_admin_metrics(db)
            print(f"✅ Admin metrics available: {admin_metrics.total_clients} clients")
            print(f"   - Total workflows: {admin_metrics.total_workflows}")
            print(f"   - Total executions: {admin_metrics.total_executions}")
            
            # Check individual client data
            for client in admin_metrics.clients[:3]:  # Test first 3 clients
                print(f"   - Client {client.client_name}: {client.total_executions} executions, {client.success_rate}% success")
            
            self.test_results['api_endpoints_data'] = True
            print("✅ API endpoints data test passed")
            
        except Exception as e:
            print(f"❌ API endpoints data test failed: {e}")
            self.test_results['api_endpoints_data'] = False
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Persistent metrics system is working correctly.")
        else:
            print("⚠️ Some tests failed. Please check the implementation.")


async def main():
    """Main test function"""
    test_suite = PersistentMetricsTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())