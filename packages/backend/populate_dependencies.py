#!/usr/bin/env python3
"""
Script to populate dependencies table with initial data from CSV file.
Run this after creating the admin user and running migrations.
"""

import asyncio
import csv
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.connection import engine
from app.models.dependency import Dependency
from app.schemas.dependency import DependencyCreate
from app.services.dependency_service import DependencyService
from sqlalchemy.ext.asyncio import AsyncSession


async def populate_dependencies():
    """Populate dependencies table with initial data"""
    
    # CSV file path (relative to backend directory)
    csv_file_path = Path(__file__).parent / "Copy of Dependancy  - Sheet1.csv"
    
    if not csv_file_path.exists():
        print(f"CSV file not found at: {csv_file_path}")
        return False
    
    dependencies_data = []
    
    # Read CSV file
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                platform_name = row.get('Service/Platform', '').strip()
                where_to_get = row.get('Where to get them', '').strip()
                guide_link = row.get('How to Generate Guide', '').strip()
                documentation_link = row.get('Documentation Link', '').strip()
                
                # Skip empty rows or rows without platform name
                if not platform_name or platform_name == '':
                    continue
                
                # Create dependency data
                dependency_data = DependencyCreate(
                    platform_name=platform_name,
                    where_to_get=where_to_get if where_to_get else None,
                    guide_link=guide_link if guide_link else None,
                    documentation_link=documentation_link if documentation_link else None,
                    description=f"API setup guide for {platform_name}"
                )
                dependencies_data.append(dependency_data)
                
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False
    
    if not dependencies_data:
        print("No valid dependency data found in CSV file")
        return False
    
    # Create database session and populate data
    try:
        async with AsyncSession(engine) as session:
            dependency_service = DependencyService(session)
            
            print(f"Found {len(dependencies_data)} dependencies to create")
            
            # Bulk create dependencies
            created_dependencies = await dependency_service.bulk_create_dependencies(dependencies_data)
            
            print(f"Successfully created {len(created_dependencies)} dependencies")
            
            # Print summary
            for dep in created_dependencies:
                print(f"  - {dep.platform_name}")
            
            return True
            
    except Exception as e:
        print(f"Error creating dependencies: {e}")
        return False


async def main():
    """Main function"""
    print("🔄 Populating dependencies table with initial data...")
    
    success = await populate_dependencies()
    
    if success:
        print("✅ Dependencies populated successfully!")
    else:
        print("❌ Failed to populate dependencies")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())