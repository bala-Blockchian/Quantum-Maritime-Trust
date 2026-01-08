from pydantic import BaseModel

class NominationCreate(BaseModel):
    delivery_id: str
    imo_number: str
    supplier_id: int
    expected_sulphur: float
    
    
class FinalizeDelivery(BaseModel):
    delivery_id: str
    actual_qty: float
    density: float
    sample_id: str