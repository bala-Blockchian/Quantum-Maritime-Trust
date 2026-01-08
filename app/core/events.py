import asyncio
import hashlib
from app.database import SessionLocal
from app import models
from app.services.pdf_engine import generate_ebdn_receipt
from app.services.quantum_vault import sign_with_mldsa
from app.core.blockchain import MaritimeClient

async def log_loop(event_filter, poll_interval, maritime_client):
    print("Quantum Watcher Active: Monitoring for BunkerFinalized...")
    
    while True:
        for event in event_filter.get_new_entries():
            db = SessionLocal()
            try:
                delivery_id_bytes = event['args']['deliveryId']
                delivery_id_hex = delivery_id_bytes.hex()
                print(f"Event Detected: {delivery_id_hex}. Finalizing eBDN...")

                record = db.query(models.BunkerRecord).filter(
                    models.BunkerRecord.delivery_id == delivery_id_hex
                ).first()

                if record:
                    record.sig_supplier = event['args']['sigSupplier']
                    record.sig_chief = event['args']['sigChiefEng']
                    record.actual_qty = event['args']['quantity']
                    record.status = "FINALIZED"
                    db.flush()

                    print(f"Generating PDF for {delivery_id_hex}...")
                    pdf_bytes = generate_ebdn_receipt(record)
                    record.pdf_blob = pdf_bytes

                    print(f"Calculating SHA3-512 Quantum Hash...")
                    sha3_obj = hashlib.sha3_512(pdf_bytes)
                    pdf_hash_bytes = sha3_obj.digest()      
                    pdf_hash_hex = sha3_obj.hexdigest()    

                    record.pdf_hash = pdf_hash_hex

                    print(f"Applying Post-Quantum Seal...")
                    quantum_sig, alg_name = sign_with_mldsa(pdf_hash_bytes)

                    record.quantum_signature = quantum_sig
                    record.status = "QUANTUM_SEALED"
                    
                    print(f"Anchoring Quantum Seal to Blockchain (3 Parameters)...")
                    try:
                        receipt = maritime_client.anchor_quantum_seal(
                            delivery_id_bytes=delivery_id_bytes,
                            pdf_hash_hex=pdf_hash_hex,
                            quantum_sig_bytes=quantum_sig
                        )
                        
                        record.anchor_tx_hash = receipt.transactionHash.hex()
                        record.status = "QUANTUM_SEALED"
                        db.commit()

                        print(f"QUANTUM ANCHOR SUCCESSFUL")
                        print(f"   TX Hash: {record.anchor_tx_hash}")
                    except Exception as e:
                        print(f"Blockchain Anchoring Failed: {str(e)}")
                        db.rollback() 
                    
                    db.commit()
                    print(f"Quantum Seal Created: {pdf_hash_hex[:16]}...")
                    print(f" quantum signature added to the DB using {alg_name}")
                
                else:
                    print(f"⚠️ Warning: Delivery ID {delivery_id_hex} not found in DB.")

            except Exception as e:
                print(f"Error in loop: {str(e)}")
            finally:
                db.close()
        
        await asyncio.sleep(poll_interval)