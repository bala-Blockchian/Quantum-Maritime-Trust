import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from app.database import engine, Base
from app.core.blockchain import MaritimeClient
from app.api.endpoints import router
from app.core.events import log_loop
 
import asyncio

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    ship_imo = "IMO9876543"
    supplier_id = 5500
    
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)

    print("Connecting to Blockchain...")
    app.state.maritime_client = MaritimeClient(
        rpc_url=os.getenv("RPC_URL"),
        contract_address=os.getenv("CONTRACT_ADDRESS"),
        private_key=os.getenv("ADMIN_PRIVATE_KEY")
    )
    
    client = app.state.maritime_client
    event_filter = client.contract.events.BunkerFinalized.create_filter(from_block='latest')
    bg_task = asyncio.create_task(log_loop(event_filter, 2, client))
    
    print(" Quantum Event Listener is running in the background.")
    
    yield

    print("Stopping Background Tasks...")
    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        print(" Event Listener stopped successfully.")

    print("Booting Maritime Service...")
    client = app.state.maritime_client
    
    if not client.is_ship_registered(ship_imo):
        print(f" Setup: Registering ship {ship_imo}...")
        client.register_ship(ship_imo, os.getenv("CHIEF_ADDRESS"))
    else:
        print(f"Ship {ship_imo} already registered.")
        
    if not client.is_supplier_registered(supplier_id):
        print(f"Setup: Registering supplier {supplier_id}...")
        client.register_supplier(supplier_id, os.getenv("BARGE_ADDRESS"))
    else:
        print(f"Supplier {supplier_id} already registered.")
    
    print("System Ready & Lifespan Active.")
    
    
    yield
    print(" Shutting down Maritime Service...")

app = FastAPI(
    title="Maritime Quantum Seal Service",
    lifespan=lifespan
)

app.include_router(router)