import asyncio
import asyncpg
import sys
from uuid import uuid4

async def main():
    conn = await asyncpg.connect('postgresql://postgres.lckabcseysgzlvkjpgtg:Fleetguard%409411@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres?ssl=require')
    
    # Create driver
    await conn.execute(
        '''INSERT INTO drivers (name, phone_number, status, company_id) 
           VALUES ($1, $2, $3, $4)''', 
        'Test Driver', '+919999999999', 'INACTIVE', 216
    )
    
    row = await conn.fetchrow('SELECT id, status, verification_status FROM drivers WHERE phone_number = $1', '+919999999999')
    driver_id = row['id']
    print(f'Driver Created. Status: {row["status"]}, Verification: {row["verification_status"]}')
    
    # Simulate Document Upload
    doc_id = str(uuid4())
    await conn.execute(
        '''INSERT INTO documents (id, target_id, target_type, company_id, category, verification_status, original_filename, mime_type, storage_path, status, created_at, updated_at) 
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, now(), now())''', 
        doc_id, str(driver_id), 'DRIVER', 216, 'license_front', 'PENDING', 'test.jpg', 'image/jpeg', 'docs/test.jpg', 'UPLOADED'
    )
    
    doc_row = await conn.fetchrow('SELECT verification_status FROM documents WHERE id = $1', doc_id)
    print(f'Document Uploaded. Status: {doc_row["verification_status"]}')
    
    # Fetch as admin (Admin Company 216)
    records = await conn.fetch(
        '''SELECT id FROM documents WHERE target_id = $1 AND target_type = $2 AND company_id = $3''', 
        str(driver_id), 'DRIVER', 216
    )
    print(f'Admin View returned {len(records)} documents')
    
    # Simulate doc rejection
    await conn.execute('UPDATE documents SET verification_status = $1 WHERE id = $2', 'REJECTED', doc_id)
    doc_rej = await conn.fetchrow('SELECT verification_status FROM documents WHERE id = $1', doc_id)
    print(f'Document Rejected (simulation). Verification: {doc_rej["verification_status"]}')
    
    # Re-upload
    await conn.execute('UPDATE documents SET verification_status = $1 WHERE id = $2', 'PENDING', doc_id)
    doc_reup = await conn.fetchrow('SELECT verification_status FROM documents WHERE id = $1', doc_id)
    print(f'Document Re-uploaded (simulation). Verification: {doc_reup["verification_status"]}')
    
    # Approve doc
    await conn.execute('UPDATE documents SET verification_status = $1 WHERE id = $2', 'APPROVED', doc_id)
    
    # Admin approves driver
    await conn.execute('UPDATE drivers SET verification_status = $1, status = $2 WHERE id = $3', 'APPROVED', 'ACTIVE', driver_id)
    
    final_row = await conn.fetchrow('SELECT status, verification_status FROM drivers WHERE id = $1', driver_id)
    print(f'Final Driver Status: {final_row["status"]}, Verification: {final_row["verification_status"]}')
    
    # Cleanup
    await conn.execute('DELETE FROM documents WHERE id = $1', doc_id)
    await conn.execute('DELETE FROM drivers WHERE id = $1', driver_id)
    
    await conn.close()

asyncio.run(main())
