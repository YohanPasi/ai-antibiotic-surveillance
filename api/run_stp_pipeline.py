"""Quick script to verify STP tables and run pipeline"""
from database import engine
from sqlalchemy import text

print("Verifying STP tables in Supabase...")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name LIKE 'stp_%'
        ORDER BY table_name
    """))
    tables = [row[0] for row in result]
    print(f'\n✓ Found {len(tables)} STP tables:')
    for t in tables:
        print(f'  - {t}')

if len(tables) >= 9:
    print('\n✅ Schema deployment successful!')
    print('\nNow running ingestion pipeline...')
    
    from data_processor.stp_stage_1_ingest import ingest_stp_data
    from data_processor.stp_wide_to_long_transform import transform_wide_to_long
    
    # Run ingestion
    result = ingest_stp_data(dataset_version='v1.0.0', force_reload=False)
    print(f'\nIngestion result: {result}')
    
    # Run transformation
    if result.get('status') == 'success':
        transform_result = transform_wide_to_long(dataset_version='v1.0.0')
        print(f'\nTransformation result: {transform_result}')
else:
    print(f'\n❌ Expected at least 9 tables, found {len(tables)}')
