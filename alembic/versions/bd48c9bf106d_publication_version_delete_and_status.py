"""publication_version_delete_and_status

Revision ID: bd48c9bf106d
Revises: 3261e6b8f1e5
Create Date: 2025-01-20 10:52:20.119125

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.orm import Session
from sqlalchemy import desc

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 


# revision identifiers, used by Alembic.
revision = 'bd48c9bf106d'
down_revision = '3261e6b8f1e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('publication_versions', sa.Column('Deleted_At', sa.DateTime(), nullable=True))
    op.add_column('publication_versions', sa.Column('Status', sa.Unicode(length=64), nullable=False, server_default='active'))

    op.execute("""
        UPDATE pv
        SET Status = 'not_applicable'
        FROM publication_versions pv
        JOIN publications p ON pv.Publication_UUID = p.UUID
        JOIN publication_environments e ON p.Environment_UUID = e.UUID
        WHERE e.Has_State = 0
    """)

    op.execute("""
        WITH announcement_statuses AS (
            SELECT 
                pa.Act_Package_UUID,
                CASE WHEN SUM(CASE WHEN pap2.Report_Status = 'pending' THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END as has_pending_announcement,
                CASE WHEN SUM(CASE WHEN pap2.Report_Status = 'valid' THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END as has_valid_announcement
            FROM publication_announcements pa
            JOIN publication_announcement_packages pap2 ON pa.UUID = pap2.Announcement_UUID
            GROUP BY pa.Act_Package_UUID
        ),
        latest_packages AS (
            SELECT *
            FROM (
                SELECT 
                    pv.UUID as version_uuid,
                    pap.Report_Status,
                    pap.Package_Type,
                    p.Procedure_Type,
                    ISNULL(ans.has_pending_announcement, 0) as has_pending_announcement,
                    ISNULL(ans.has_valid_announcement, 0) as has_valid_announcement,
                    ROW_NUMBER() OVER (PARTITION BY pv.UUID ORDER BY pap.Modified_Date DESC) as rn
                FROM publication_versions pv
                LEFT JOIN publication_act_packages pap ON pv.UUID = pap.Publication_Version_UUID
                JOIN publications p ON pv.Publication_UUID = p.UUID
                JOIN publication_environments e ON p.Environment_UUID = e.UUID
                LEFT JOIN announcement_statuses ans ON pap.UUID = ans.Act_Package_UUID
                WHERE e.Has_State != 0
            ) ranked
            WHERE rn = 1
        )
        UPDATE pv
        SET Status = 
            CASE 
                WHEN lp.version_uuid IS NULL THEN 'active'
                WHEN lp.Package_Type = 'Validation' AND lp.Report_Status = 'pending' THEN 'validation'
                WHEN lp.Package_Type = 'Validation' AND lp.Report_Status = 'failed' THEN 'validation_failed'
                WHEN lp.Package_Type = 'Publication' AND lp.Report_Status = 'pending' THEN 'publication'
                WHEN lp.Package_Type = 'Publication' AND lp.Report_Status = 'failed' THEN 'publication_failed'
                WHEN lp.Package_Type = 'Publication' AND lp.Report_Status = 'valid' AND lp.Procedure_Type != 'draft' THEN 'completed'
                WHEN lp.Package_Type = 'Publication' AND lp.Report_Status = 'valid' AND lp.Procedure_Type = 'draft' AND lp.has_pending_announcement = 1 THEN 'announcement'
                WHEN lp.Package_Type = 'Publication' AND lp.Report_Status = 'valid' AND lp.Procedure_Type = 'draft' AND lp.has_valid_announcement = 1 THEN 'completed'
                ELSE 'active'
            END
        FROM publication_versions pv
        LEFT JOIN latest_packages lp ON pv.UUID = lp.version_uuid
        WHERE pv.Status != 'not_applicable'
    """)

def downgrade() -> None:
    op.execute("""
        DECLARE @ConstraintName nvarchar(200)
        SELECT @ConstraintName = name FROM sys.default_constraints
        WHERE parent_object_id = OBJECT_ID('publication_versions')
        AND col_name(parent_object_id, parent_column_id) = 'Status';
        IF @ConstraintName IS NOT NULL
            EXECUTE('ALTER TABLE publication_versions DROP CONSTRAINT ' + @ConstraintName)
    """)
    op.drop_column('publication_versions', 'Status')
    op.drop_column('publication_versions', 'Deleted_At')
