#!/usr/bin/env python3
"""
Basic usage example for the Dataverse SDK.

This example demonstrates the fundamental operations:
- Authentication
- Creating entities
- Reading entities
- Updating entities
- Querying entities
- Deleting entities
"""

import asyncio
import os
from dataverse_sdk import DataverseSDK


async def main():
    """Main example function."""
    
    # Initialize SDK with environment variables
    # Make sure to set these in your environment:
    # DATAVERSE_URL, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
    sdk = DataverseSDK()
    
    async with sdk:
        print("🚀 Dataverse SDK Basic Usage Example")
        print("=" * 50)
        
        # 1. Create an account
        print("\n1. Creating a new account...")
        account_data = {
            "name": "SDK Example Account",
            "websiteurl": "https://example.com",
            "telephone1": "555-0123",
            "description": "Account created by SDK example"
        }
        
        account_id = await sdk.create("accounts", account_data)
        print(f"✅ Created account with ID: {account_id}")
        
        try:
            # 2. Read the account
            print("\n2. Reading the account...")
            account = await sdk.read("accounts", account_id)
            print(f"✅ Account name: {account['name']}")
            print(f"   Website: {account['websiteurl']}")
            print(f"   Phone: {account['telephone1']}")
            
            # 3. Update the account
            print("\n3. Updating the account...")
            update_data = {
                "description": "Updated by SDK example",
                "websiteurl": "https://updated-example.com"
            }
            
            await sdk.update("accounts", account_id, update_data)
            print("✅ Account updated successfully")
            
            # 4. Verify the update
            print("\n4. Verifying the update...")
            updated_account = await sdk.read("accounts", account_id, 
                                            select=["name", "description", "websiteurl"])
            print(f"✅ Updated description: {updated_account['description']}")
            print(f"   Updated website: {updated_account['websiteurl']}")
            
            # 5. Query accounts
            print("\n5. Querying accounts...")
            accounts = await sdk.query("accounts", {
                "select": ["name", "websiteurl", "createdon"],
                "filter": "contains(name, 'SDK')",
                "order_by": ["createdon desc"],
                "top": 5
            })
            
            print(f"✅ Found {len(accounts.value)} accounts with 'SDK' in name:")
            for acc in accounts.value:
                print(f"   - {acc['name']} ({acc['websiteurl']})")
            
            # 6. Create a contact associated with the account
            print("\n6. Creating a contact for the account...")
            contact_data = {
                "firstname": "John",
                "lastname": "Doe",
                "emailaddress1": "john.doe@example.com",
                "telephone1": "555-0456",
                f"parentcustomerid@odata.bind": f"accounts({account_id})"
            }
            
            contact_id = await sdk.create("contacts", contact_data)
            print(f"✅ Created contact with ID: {contact_id}")
            
            # 7. Query the account with expanded contact
            print("\n7. Reading account with related contacts...")
            account_with_contacts = await sdk.read("accounts", account_id,
                expand=["contact_customer_accounts($select=fullname,emailaddress1)"])
            
            contacts = account_with_contacts.get("contact_customer_accounts", [])
            print(f"✅ Account has {len(contacts)} related contacts:")
            for contact in contacts:
                print(f"   - {contact['fullname']} ({contact['emailaddress1']})")
            
            # Clean up the contact
            await sdk.delete("contacts", contact_id)
            print(f"✅ Deleted contact {contact_id}")
            
        finally:
            # 8. Clean up - delete the account
            print("\n8. Cleaning up...")
            await sdk.delete("accounts", account_id)
            print(f"✅ Deleted account {account_id}")
        
        print("\n🎉 Example completed successfully!")


if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = ["DATAVERSE_URL", "AZURE_CLIENT_ID", "AZURE_TENANT_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables and try again.")
        exit(1)
    
    # Run the example
    asyncio.run(main())

