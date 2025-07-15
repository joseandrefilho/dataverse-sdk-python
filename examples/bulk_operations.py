#!/usr/bin/env python3
"""
Bulk operations example for the Dataverse SDK.

This example demonstrates:
- Bulk create operations
- Bulk update operations
- Bulk delete operations
- Error handling in bulk operations
- Performance optimization
"""

import asyncio
import time
from dataverse_sdk import DataverseSDK


async def main():
    """Main bulk operations example."""
    
    sdk = DataverseSDK()
    
    async with sdk:
        print("⚡ Dataverse SDK Bulk Operations Example")
        print("=" * 50)
        
        # 1. Bulk Create Example
        print("\n1. Bulk creating contacts...")
        
        # Generate test data
        contacts_data = []
        for i in range(50):
            contacts_data.append({
                "firstname": f"Contact{i:03d}",
                "lastname": "BulkTest",
                "emailaddress1": f"contact{i:03d}@bulktest.com",
                "telephone1": f"555-{i:04d}",
                "description": f"Bulk created contact #{i+1}"
            })
        
        start_time = time.time()
        
        # Bulk create with progress tracking
        result = await sdk.bulk_create(
            "contacts",
            contacts_data,
            batch_size=10,  # Process in batches of 10
            parallel=True   # Execute batches in parallel
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Bulk create completed in {duration:.2f} seconds")
        print(f"   Total processed: {result.total_processed}")
        print(f"   Successful: {result.successful}")
        print(f"   Failed: {result.failed}")
        print(f"   Success rate: {result.success_rate:.1f}%")
        
        if result.has_errors:
            print(f"   Errors encountered:")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"     - {error}")
        
        # Get the IDs of successfully created contacts
        created_contact_ids = []
        if result.successful > 0:
            # Query for our bulk test contacts
            query_result = await sdk.query("contacts", {
                "select": ["contactid"],
                "filter": "lastname eq 'BulkTest'",
                "top": result.successful
            })
            created_contact_ids = [c["contactid"] for c in query_result.value]
            print(f"   Retrieved {len(created_contact_ids)} contact IDs")
        
        try:
            # 2. Bulk Update Example
            if created_contact_ids:
                print(f"\n2. Bulk updating {len(created_contact_ids)} contacts...")
                
                # Prepare update data
                updates_data = []
                for i, contact_id in enumerate(created_contact_ids):
                    updates_data.append({
                        "id": contact_id,
                        "jobtitle": f"Position {i+1}",
                        "description": f"Updated bulk contact #{i+1}"
                    })
                
                start_time = time.time()
                
                update_result = await sdk.bulk_update(
                    "contacts",
                    updates_data,
                    batch_size=15,
                    parallel=True
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"✅ Bulk update completed in {duration:.2f} seconds")
                print(f"   Successful: {update_result.successful}")
                print(f"   Failed: {update_result.failed}")
                print(f"   Success rate: {update_result.success_rate:.1f}%")
            
            # 3. Bulk Upsert Example
            print(f"\n3. Bulk upsert example...")
            
            # Mix of new and existing data
            upsert_data = [
                {
                    "firstname": "NewContact1",
                    "lastname": "UpsertTest",
                    "emailaddress1": "new1@upserttest.com"
                },
                {
                    "firstname": "NewContact2", 
                    "lastname": "UpsertTest",
                    "emailaddress1": "new2@upserttest.com"
                }
            ]
            
            # Add some existing contacts for update
            if created_contact_ids[:2]:
                for i, contact_id in enumerate(created_contact_ids[:2]):
                    upsert_data.append({
                        "contactid": contact_id,
                        "firstname": f"UpdatedContact{i+1}",
                        "lastname": "UpsertTest",
                        "description": "Updated via upsert"
                    })
            
            upsert_result = await sdk.bulk_upsert(
                "contacts",
                upsert_data,
                batch_size=5
            )
            
            print(f"✅ Bulk upsert completed")
            print(f"   Total processed: {upsert_result.total_processed}")
            print(f"   Created: {upsert_result.created}")
            print(f"   Updated: {upsert_result.updated}")
            print(f"   Failed: {upsert_result.failed}")
            
            # Clean up upsert test contacts
            upsert_contacts = await sdk.query("contacts", {
                "select": ["contactid"],
                "filter": "lastname eq 'UpsertTest'"
            })
            
            upsert_contact_ids = [c["contactid"] for c in upsert_contacts.value]
            if upsert_contact_ids:
                await sdk.bulk_delete("contacts", upsert_contact_ids)
                print(f"   Cleaned up {len(upsert_contact_ids)} upsert test contacts")
            
            # 4. Performance Comparison
            print(f"\n4. Performance comparison...")
            
            # Create 10 contacts individually
            individual_data = [
                {
                    "firstname": f"Individual{i}",
                    "lastname": "PerfTest",
                    "emailaddress1": f"individual{i}@perftest.com"
                }
                for i in range(10)
            ]
            
            # Individual creates
            start_time = time.time()
            individual_ids = []
            for contact_data in individual_data:
                contact_id = await sdk.create("contacts", contact_data)
                individual_ids.append(contact_id)
            individual_time = time.time() - start_time
            
            # Bulk create
            start_time = time.time()
            bulk_result = await sdk.bulk_create("contacts", individual_data, batch_size=5)
            bulk_time = time.time() - start_time
            
            print(f"✅ Performance comparison (10 contacts):")
            print(f"   Individual creates: {individual_time:.2f} seconds")
            print(f"   Bulk create: {bulk_time:.2f} seconds")
            print(f"   Speedup: {individual_time/bulk_time:.1f}x faster")
            
            # Clean up performance test contacts
            perf_contacts = await sdk.query("contacts", {
                "select": ["contactid"],
                "filter": "lastname eq 'PerfTest'"
            })
            
            perf_contact_ids = [c["contactid"] for c in perf_contacts.value]
            if perf_contact_ids:
                await sdk.bulk_delete("contacts", perf_contact_ids)
                print(f"   Cleaned up {len(perf_contact_ids)} performance test contacts")
            
        finally:
            # 5. Bulk Delete Example
            if created_contact_ids:
                print(f"\n5. Bulk deleting {len(created_contact_ids)} contacts...")
                
                start_time = time.time()
                
                delete_result = await sdk.bulk_delete(
                    "contacts",
                    created_contact_ids,
                    batch_size=20,
                    parallel=True
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"✅ Bulk delete completed in {duration:.2f} seconds")
                print(f"   Successful: {delete_result.successful}")
                print(f"   Failed: {delete_result.failed}")
                print(f"   Success rate: {delete_result.success_rate:.1f}%")
        
        print("\n🎉 Bulk operations example completed!")


if __name__ == "__main__":
    asyncio.run(main())

