from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from starlette.requests import Request
import requests
import os

router = APIRouter()

@router.post("/nominate")
async def nominate_bunker(
    data: schemas.NominationCreate, 
    request: Request, 
    db: Session = Depends(get_db)
):
    client = request.app.state.maritime_client
    delivery_id_hash = client.w3.keccak(text=data.delivery_id).hex()
    existing = db.query(models.BunkerRecord).filter(models.BunkerRecord.delivery_id == delivery_id_hash).first()
    if existing:
        raise HTTPException(status_code=400, detail="Delivery ID already exists")

    new_record = models.BunkerRecord(
        delivery_id=delivery_id_hash,
        imo_number=data.imo_number,
        supplier_id=data.supplier_id,
        sulphur_content=data.expected_sulphur,
        status="NOMINATED"
    )
    db.add(new_record)
    db.commit()

    client = request.app.state.maritime_client
    try:
        delivery_id_bytes = client.w3.keccak(text=data.delivery_id) 
        
        barge_key = os.getenv("BARGE_PRIVATE_KEY")
        
        receipt = client.nominate_bunker(
            delivery_id_bytes=delivery_id_bytes,
            imo=data.imo_number,
            supplier_id=data.supplier_id,
            expected_sulphur=int(data.expected_sulphur * 100), 
            barge_private_key=barge_key
        )
        
        return {
            "status": "success", 
            "delivery_id": data.delivery_id,
            "tx_hash": receipt.transactionHash.hex(),
            "message": "Bunker nominated and anchored on-chain by Supplier"
        }

    except Exception as e:
        db.delete(new_record)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Blockchain Nomination Failed: {str(e)}")
    
    
@router.post("/finalize")
async def finalize_bunker(
    data: schemas.FinalizeDelivery, 
    request: Request, 
    db: Session = Depends(get_db)
):
    client = request.app.state.maritime_client
    delivery_id_hash = client.w3.keccak(text=data.delivery_id).hex()
    record = db.query(models.BunkerRecord).filter(models.BunkerRecord.delivery_id == delivery_id_hash).first()
    if not record:
        raise HTTPException(status_code=404, detail="Nomination not found")

    record.actual_qty = data.actual_qty
    record.density = data.density
    record.sample_id = data.sample_id
    db.commit()

    client = request.app.state.maritime_client
    try:
        delivery_id_bytes = client.w3.keccak(text=data.delivery_id)
        
        supplier_key = os.getenv("BARGE_PRIVATE_KEY")
        chief_key = os.getenv("CHIEF_PRIVATE_KEY")

        print(f"Starting finalization flow for {data.delivery_id}...")
        
        receipt = client.finalize_bunker(
            delivery_id=delivery_id_bytes,
            density=int(data.density),
            qty=int(data.actual_qty),
            sample_id=data.sample_id,
            supplier_key=supplier_key,
            chief_key=chief_key
        )

        record.status = "FINALIZED"
        record.blockchain_tx = receipt.transactionHash.hex()
        db.commit()

        return {
            "status": "success", 
            "message": "Bunker finalized on-chain",
            "tx_hash": record.blockchain_tx
        }

    except Exception as e:
        record.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))