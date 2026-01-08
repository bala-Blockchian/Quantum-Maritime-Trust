from sqlalchemy import Column, Integer, String, Float, LargeBinary, DateTime
from app.database import Base
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from app.database import Base

class BunkerRecord(Base):
    __tablename__ = "bunker_records"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(String, unique=True, index=True) # Hex string
    imo_number = Column(String)
    supplier_id = Column(Integer)
    
    # Statuses: PENDING, NOMINATED, FINALIZING, FINALIZED, QUANTUM_SEALED
    status = Column(String, default="PENDING")
    
    sulphur_content = Column(Float)
    density = Column(Float, nullable=True)
    actual_qty = Column(Float, nullable=True)
    sample_id = Column(String, nullable=True)

    # Traditional Signatures (from Event)
    sig_supplier = Column(LargeBinary, nullable=True)
    sig_chief = Column(LargeBinary, nullable=True)

    # Quantum Seal Data
    pdf_blob = Column(LargeBinary, nullable=True)      
    pdf_hash = Column(String, nullable=True)           
    quantum_signature = Column(LargeBinary, nullable=True) 
    anchor_tx_hash = Column(String, nullable=True)     
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)