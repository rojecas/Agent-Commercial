from sqlalchemy import Column, String, Text, BigInteger
from sqlalchemy.orm import relationship
from src.database.base import Base, TenantMixin, SoftDeleteMixin, AuditableMixin

class User(Base, TenantMixin, SoftDeleteMixin, AuditableMixin):
    """
    Core User/Lead table.
    Tracks individuals who have interacted with the bot across any channel within a specific tenant.
    """
    __tablename__ = "users"

    # Surrogate Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Primary identifiers extracted by the bot
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone_number = Column(String(50), nullable=True, index=True)
    company_name = Column(String(255), nullable=True)
    
    # Platform-specific unique identifiers (e.g. Telegram ID, WhatsApp number)
    # The combination of tenant_id + platform_id identifies the user
    platform = Column(String(50), nullable=False)   # 'telegram', 'whatsapp', 'web'
    platform_user_id = Column(String(255), nullable=False, index=True)
    
    # Short description of what they are looking for, usually populated right before handoff
    problem_statement = Column(Text, nullable=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    opportunities = relationship("LeadsOpportunity", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base, TenantMixin, SoftDeleteMixin, AuditableMixin):
    """
    Represents a specific session/conversation thread with a user.
    """
    __tablename__ = "conversations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True, nullable=False)
    
    # Status: 'active', 'closed', 'handed_off_to_human', 'ignored'
    status = Column(String(50), default="active", nullable=False, index=True)
    intent_category = Column(String(100), nullable=True) # e.g., 'sales', 'support'
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base, TenantMixin, AuditableMixin):
    """
    The literal transcript of the conversation. Used for short-term memory and audit.
    Note: Usually messages are not soft-deleted individually to preserve audit trails.
    """
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, index=True, nullable=False)
    
    # 'user', 'assistant', 'system', 'tool'
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class LeadsOpportunity(Base, TenantMixin, SoftDeleteMixin, AuditableMixin):
    """
    Represents a specific commercial opportunity or interest expressed by a user.
    """
    __tablename__ = "leads_opportunities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True, nullable=False)
    
    # 'qualified', 'needs_expert', 'closed'
    status = Column(String(50), default="qualified", nullable=False)
    problem_statement = Column(Text, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="opportunities")
    recommendations = relationship("OpportunityProductRecommendation", back_populates="opportunity", cascade="all, delete-orphan")

class OpportunityProductRecommendation(Base, TenantMixin, AuditableMixin):
    """
    The specific products from the PHP Web App Catalog recommended to solve the lead's problem.
    """
    __tablename__ = "opportunity_product_recommendations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    opportunity_id = Column(BigInteger, index=True, nullable=False)
    
    product_sku = Column(String(100), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    justification = Column(Text, nullable=True) # E.g., "Recommended because of high turbidity requirement"
    
    # Relationships
    opportunity = relationship("LeadsOpportunity", back_populates="recommendations")
