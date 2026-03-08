from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from mrsa_schemas import MasterDefinitionCreate

class MasterDataService:
    @staticmethod
    def get_definitions_by_category(db: Session, category: str):
        if category == "WARD":
            # Dynamically fetch actual active wards from the data so the modal always matches the dashboard
            sql = text("SELECT DISTINCT ward FROM ast_weekly_aggregated ORDER BY ward")
            rows = db.execute(sql).fetchall()
            if rows:
                # Mock the MasterDefinition schema
                return [
                    {
                        "id": i + 1000, 
                        "category": "WARD", 
                        "label": r[0], 
                        "value": r[0], 
                        "is_active": True
                    } 
                    for i, r in enumerate(rows)
                ]
                
        # For SAMPLE_TYPE and others, use the static configuration database
        sql = text("SELECT * FROM master_definitions WHERE category = :cat AND is_active = TRUE ORDER BY label")
        result = db.execute(sql, {"cat": category}).fetchall()
        return result

    @staticmethod
    def create_definition(db: Session, def_in: MasterDefinitionCreate):
        # check duplicate
        check_sql = text("SELECT id FROM master_definitions WHERE category = :cat AND value = :val")
        existing = db.execute(check_sql, {"cat": def_in.category, "val": def_in.value}).fetchone()
        
        if existing:
            # If exists (even inactive), reactivate or error
            # Detailed logic: if inactive, update to active. If active, error.
            # Simplified: Reactivate/Update
            upd_sql = text("""
                UPDATE master_definitions 
                SET label = :lbl, is_active = TRUE 
                WHERE id = :id 
                RETURNING id, category, label, value, is_active
            """)
            updated = db.execute(upd_sql, {"lbl": def_in.label, "id": existing[0]}).fetchone()
            db.commit()
            return updated
        
        # Insert New
        ins_sql = text("""
            INSERT INTO master_definitions (category, label, value) 
            VALUES (:cat, :lbl, :val) 
            RETURNING id, category, label, value, is_active
        """)
        new_row = db.execute(ins_sql, {"cat": def_in.category, "lbl": def_in.label, "val": def_in.value}).fetchone()
        db.commit()
        return new_row

    @staticmethod
    def delete_definition(db: Session, id: int):
        # Soft delete
        sql = text("UPDATE master_definitions SET is_active = FALSE WHERE id = :id")
        db.execute(sql, {"id": id})
        db.commit()
        return {"message": "Deleted successfully"}
