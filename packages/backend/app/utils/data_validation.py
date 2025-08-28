"""Data validation utilities for checking data integrity"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.models import WorkflowExecution, MetricsAggregation, Client, AggregationPeriod

logger = logging.getLogger(__name__)


class DataValidator:
    """Utility class for validating data integrity and completeness"""
    
    @staticmethod
    def check_execution_gaps(
        db: Session, 
        client_id: int, 
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Check for gaps in execution data for a client
        
        Returns:
            Dict with gap analysis including missing dates and statistics
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        # Get all dates that have executions
        dates_with_executions = db.query(
            func.date(WorkflowExecution.started_at).label('execution_date')
        ).filter(
            and_(
                WorkflowExecution.client_id == client_id,
                WorkflowExecution.started_at >= datetime.combine(start_date, datetime.min.time()),
                WorkflowExecution.started_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            )
        ).group_by(
            func.date(WorkflowExecution.started_at)
        ).all()
        
        execution_dates = {row.execution_date for row in dates_with_executions}
        
        # Generate all dates in the range
        all_dates = set()
        current = start_date
        while current <= end_date:
            all_dates.add(current)
            current += timedelta(days=1)
        
        # Find missing dates
        missing_dates = sorted(all_dates - execution_dates)
        
        # Get execution counts by date
        daily_counts = db.query(
            func.date(WorkflowExecution.started_at).label('date'),
            func.count(WorkflowExecution.id).label('count')
        ).filter(
            and_(
                WorkflowExecution.client_id == client_id,
                WorkflowExecution.started_at >= datetime.combine(start_date, datetime.min.time()),
                WorkflowExecution.started_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            )
        ).group_by(
            func.date(WorkflowExecution.started_at)
        ).all()
        
        return {
            'client_id': client_id,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_days': days_back,
            'days_with_data': len(execution_dates),
            'days_missing_data': len(missing_dates),
            'missing_dates': [d.isoformat() for d in missing_dates],
            'data_completeness_percentage': (len(execution_dates) / len(all_dates)) * 100,
            'daily_execution_counts': {
                row.date.isoformat(): row.count for row in daily_counts
            }
        }
    
    @staticmethod
    def validate_aggregations(
        db: Session,
        client_id: int,
        period_type: AggregationPeriod = AggregationPeriod.DAILY,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Validate that aggregations match the underlying execution data
        
        Returns:
            Dict with validation results and any discrepancies found
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        # Get aggregations for the period
        aggregations = db.query(MetricsAggregation).filter(
            and_(
                MetricsAggregation.client_id == client_id,
                MetricsAggregation.period_type == period_type,
                MetricsAggregation.period_start >= start_date,
                MetricsAggregation.period_end <= end_date,
                MetricsAggregation.workflow_id.is_(None)  # Client-wide aggregations only
            )
        ).all()
        
        discrepancies = []
        
        for agg in aggregations:
            # Recompute from raw data
            actual_executions = db.query(WorkflowExecution).filter(
                and_(
                    WorkflowExecution.client_id == client_id,
                    WorkflowExecution.is_production == True,
                    WorkflowExecution.started_at >= datetime.combine(agg.period_start, datetime.min.time()),
                    WorkflowExecution.started_at < datetime.combine(agg.period_end + timedelta(days=1), datetime.min.time())
                )
            ).all()
            
            actual_total = len(actual_executions)
            actual_successful = len([e for e in actual_executions if e.status.value == 'success'])
            actual_failed = len([e for e in actual_executions if e.status.value == 'error'])
            
            if (actual_total != agg.total_executions or 
                actual_successful != agg.successful_executions or
                actual_failed != agg.failed_executions):
                
                discrepancies.append({
                    'period': f"{agg.period_start.isoformat()} to {agg.period_end.isoformat()}",
                    'aggregation': {
                        'total': agg.total_executions,
                        'successful': agg.successful_executions,
                        'failed': agg.failed_executions
                    },
                    'actual': {
                        'total': actual_total,
                        'successful': actual_successful,
                        'failed': actual_failed
                    },
                    'differences': {
                        'total': actual_total - agg.total_executions,
                        'successful': actual_successful - agg.successful_executions,
                        'failed': actual_failed - agg.failed_executions
                    }
                })
        
        return {
            'client_id': client_id,
            'period_type': period_type.value,
            'aggregations_checked': len(aggregations),
            'discrepancies_found': len(discrepancies),
            'is_valid': len(discrepancies) == 0,
            'discrepancies': discrepancies
        }
    
    @staticmethod
    def get_data_health_report(db: Session, client_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive health report for a client's data
        
        Returns:
            Dict with overall data health metrics
        """
        # Get execution statistics
        total_executions = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.client_id == client_id
        ).scalar() or 0
        
        # Get date range of executions
        date_range = db.query(
            func.min(WorkflowExecution.started_at).label('oldest'),
            func.max(WorkflowExecution.started_at).label('newest')
        ).filter(
            WorkflowExecution.client_id == client_id
        ).first()
        
        # Check recent gaps
        gaps_7d = DataValidator.check_execution_gaps(db, client_id, days_back=7)
        gaps_30d = DataValidator.check_execution_gaps(db, client_id, days_back=30)
        
        # Validate recent aggregations
        daily_validation = DataValidator.validate_aggregations(
            db, client_id, AggregationPeriod.DAILY, days_back=7
        )
        
        # Get aggregation coverage
        aggregation_coverage = db.query(
            MetricsAggregation.period_type,
            func.count(MetricsAggregation.id).label('count'),
            func.min(MetricsAggregation.period_start).label('oldest'),
            func.max(MetricsAggregation.period_end).label('newest')
        ).filter(
            MetricsAggregation.client_id == client_id
        ).group_by(
            MetricsAggregation.period_type
        ).all()
        
        return {
            'client_id': client_id,
            'execution_data': {
                'total_executions': total_executions,
                'date_range': {
                    'oldest': date_range.oldest.isoformat() if date_range.oldest else None,
                    'newest': date_range.newest.isoformat() if date_range.newest else None
                }
            },
            'data_gaps': {
                'last_7_days': {
                    'missing_days': gaps_7d['days_missing_data'],
                    'completeness': gaps_7d['data_completeness_percentage']
                },
                'last_30_days': {
                    'missing_days': gaps_30d['days_missing_data'],
                    'completeness': gaps_30d['data_completeness_percentage']
                }
            },
            'aggregation_validation': {
                'daily_aggregations_valid': daily_validation['is_valid'],
                'discrepancies_found': daily_validation['discrepancies_found']
            },
            'aggregation_coverage': {
                period.period_type.value: {
                    'count': period.count,
                    'oldest': period.oldest.isoformat() if period.oldest else None,
                    'newest': period.newest.isoformat() if period.newest else None
                }
                for period in aggregation_coverage
            },
            'health_score': DataValidator._calculate_health_score(
                gaps_7d, gaps_30d, daily_validation
            )
        }
    
    @staticmethod
    def _calculate_health_score(gaps_7d, gaps_30d, validation) -> float:
        """Calculate overall health score from 0-100"""
        # Weight recent completeness more heavily
        completeness_score = (
            gaps_7d['data_completeness_percentage'] * 0.6 +
            gaps_30d['data_completeness_percentage'] * 0.4
        )
        
        # Validation score
        validation_score = 100 if validation['is_valid'] else 50
        
        # Combined score
        return round((completeness_score * 0.7 + validation_score * 0.3), 2)


# Utility function for CLI/testing
def check_client_data_health(db: Session, client_name: str) -> None:
    """Check and print data health for a specific client"""
    client = db.query(Client).filter(Client.name == client_name).first()
    if not client:
        print(f"Client '{client_name}' not found")
        return
    
    validator = DataValidator()
    report = validator.get_data_health_report(db, client.id)
    
    print(f"\n=== Data Health Report for {client_name} ===")
    print(f"Total Executions: {report['execution_data']['total_executions']}")
    print(f"Date Range: {report['execution_data']['date_range']['oldest']} to {report['execution_data']['date_range']['newest']}")
    print(f"\nData Completeness:")
    print(f"  Last 7 days: {report['data_gaps']['last_7_days']['completeness']:.1f}%")
    print(f"  Last 30 days: {report['data_gaps']['last_30_days']['completeness']:.1f}%")
    print(f"\nAggregations Valid: {report['aggregation_validation']['daily_aggregations_valid']}")
    print(f"Overall Health Score: {report['health_score']}/100")
    
    if report['data_gaps']['last_7_days']['missing_days'] > 0:
        print(f"\n⚠️ Warning: Missing data for {report['data_gaps']['last_7_days']['missing_days']} days in the last week")
