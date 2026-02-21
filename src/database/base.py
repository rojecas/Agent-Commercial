from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, declared_attr

# Declarative base for SQLAlchemy models
Base = declarative_base()

class TenantMixin:
    """
    Mixin that adds a tenant_id column to a model, making it tenant-aware.
    All models inheriting from this MUST be queried with a tenant filter.
    """
    @declared_attr
    def tenant_id(cls):
        return Column(String(50), nullable=False, index=True)

class SoftDeleteMixin:
    """
    Mixin that adds logical deletion capabilities to a model.
    Provides an is_deleted flag and a deleted_at timestamp.
    """
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    def soft_delete(self):
        """Marks the record as deleted and records the timestamp."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        
    def restore(self):
        """Restores a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None

class AuditableMixin:
    """
    Mixin to automatically track creation and update timestamps of records.
    """
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
