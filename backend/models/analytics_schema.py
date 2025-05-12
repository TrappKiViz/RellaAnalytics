from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(String(36), primary_key=True)  # UUID
    date = Column(DateTime, nullable=False)
    location_name = Column(String(100), nullable=False)
    client_id = Column(String(36), ForeignKey('clients.id'))
    staff_id = Column(String(36), ForeignKey('staff.id'))
    gross_sales = Column(Float)
    discount_amount = Column(Float)
    refund_amount = Column(Float)
    net_sales = Column(Float)
    sales_tax = Column(Float)
    service_category = Column(String(50))  # tox, filler, facials, lasers, weight loss, retail
    is_new_patient = Column(Boolean, default=False)
    
    # Relationships
    client = relationship("Client", back_populates="transactions")
    staff = relationship("Staff", back_populates="transactions")

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(100), nullable=False)
    first_visit_date = Column(DateTime)
    last_visit_date = Column(DateTime)
    total_visits = Column(Integer, default=0)
    is_member = Column(Boolean, default=False)
    membership_start_date = Column(DateTime)
    lead_source = Column(String(50))  # website, social, referral, etc.
    
    # Relationships
    transactions = relationship("Transaction", back_populates="client")
    appointments = relationship("Appointment", back_populates="client")

class Staff(Base):
    __tablename__ = 'staff'
    
    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(100), nullable=False)
    role = Column(String(50))
    
    # Relationships
    transactions = relationship("Transaction", back_populates="staff")
    appointments = relationship("Appointment", back_populates="provider")

class Appointment(Base):
    __tablename__ = 'appointments'
    
    id = Column(String(36), primary_key=True)  # UUID
    client_id = Column(String(36), ForeignKey('clients.id'))
    provider_id = Column(String(36), ForeignKey('staff.id'))
    date = Column(DateTime, nullable=False)
    service_type = Column(String(50))
    status = Column(String(20))  # scheduled, completed, no-show, cancelled
    room_id = Column(String(36))
    duration_minutes = Column(Integer)
    
    # Relationships
    client = relationship("Client", back_populates="appointments")
    provider = relationship("Staff", back_populates="appointments")

class MarketingMetrics(Base):
    __tablename__ = 'marketing_metrics'
    
    id = Column(String(36), primary_key=True)  # UUID
    date = Column(DateTime, nullable=False)
    channel = Column(String(50))  # website, instagram, facebook, email
    visits = Column(Integer)
    leads = Column(Integer)
    bookings = Column(Integer)
    cost = Column(Float)
    revenue = Column(Float)
    
class FinancialMetrics(Base):
    __tablename__ = 'financial_metrics'
    
    id = Column(String(36), primary_key=True)  # UUID
    date = Column(DateTime, nullable=False)
    category = Column(String(50))  # payroll, rent, supplies, etc.
    amount = Column(Float)
    is_expense = Column(Boolean)
    location_name = Column(String(100)) 