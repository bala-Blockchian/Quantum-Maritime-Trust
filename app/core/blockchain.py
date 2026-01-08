import os
import json
import time
from web3 import Web3
from eth_account.messages import encode_defunct
import requests

class MaritimeClient:
    def __init__(self, rpc_url, contract_address, private_key):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to RPC at {rpc_url}")

        self.admin_private_key = private_key
        self.admin_account = self.w3.eth.account.from_key(self.admin_private_key)
        self.contract_address = contract_address

        abi_path = "blockchain/out/MaritimeRegistry.sol/MaritimeRegistry.json"
        
        try:
            with open(abi_path, 'r') as f:
                contract_json = json.load(f)
                abi = contract_json.get('abi', contract_json)
            self.contract = self.w3.eth.contract(address=contract_address, abi=abi)
        except FileNotFoundError:
            print(f"⚠️ Warning: ABI file not found at {abi_path}. Using fallback ABI for registration.")
            self.contract = self.w3.eth.contract(address=contract_address, abi=[
                {"inputs":[{"internalType":"string","name":"","type":"string"}],"name":"shipToChiefEng","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"string","name":"_imo","type":"string"},{"internalType":"address","name":"_chiefEng","type":"address"}],"name":"registerShip","outputs":[],"stateMutability":"nonpayable","type":"function"}
            ])

    def is_ship_registered(self, imo: str) -> bool:
        chief_address = self.contract.functions.shipToChiefEng(imo).call()
        return chief_address != "0x0000000000000000000000000000000000000000"

    def register_ship(self, imo: str, chief_address: str):
        print(f"Anchoring Ship {imo} to Chief {chief_address}...")
        return self._send_transaction(
            self.contract.functions.registerShip(imo, chief_address),
            self.admin_private_key
        )  
        
    def is_supplier_registered(self, supplier_id: int) -> bool:
        barge_address = self.contract.functions.supplierToBarge(supplier_id).call()
        return barge_address != "0x0000000000000000000000000000000000000000"

    def register_supplier(self, supplier_id: int, barge_address: str):
        print(f"Registering Supplier ID {supplier_id} to Barge {barge_address}...")
        return self._send_transaction(
            self.contract.functions.registerSupplier(supplier_id, barge_address),
            self.admin_private_key
        )
        
    def nominate_bunker(self, delivery_id_bytes, imo, supplier_id, expected_sulphur, barge_private_key):
        print(f"Supplier {supplier_id} is nominating Delivery {delivery_id_bytes.hex()}...")
        
        return self._send_transaction(
            self.contract.functions.nominateBunker(
                delivery_id_bytes, 
                imo, 
                supplier_id, 
                expected_sulphur
            ),
            barge_private_key
        )
        
        
    def finalize_bunker(self, delivery_id, density, qty, sample_id, supplier_key, chief_key):
        note = self.contract.functions.getNote(delivery_id).call()
        imo_number = note[0]
        supplier_id = note[1]
        expected_sulphur = note[3]

        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("CHIEF_CHAT_ID")
        
        bunker_details = (
            f"*BUNKER FINALIZATION REQUEST*\n\n"
            f"*ID:* `{delivery_id.hex()[:12]}...`\n"
            f"*IMO:* {imo_number}\n"
            f"*Density:* {density}\n"
            f"*Quantity:* {qty} MT\n"
            f"*Sample:* {sample_id}\n\n"
            f"Reply with *'SIGN'* to authorize this record."
        )

        print(f"[{delivery_id.hex()[:6]}] Sending Telegram request...")
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                     data={"chat_id": chat_id, "text": bunker_details, "parse_mode": "Markdown"})

        approved = False
        timeout = 60  
        start_time = time.time()

        while time.time() - start_time < timeout:
            updates = requests.get(f"https://api.telegram.org/bot{token}/getUpdates").json()
            if updates["result"]:
                last_msg = updates["result"][-1].get("message", {}).get("text", "")
                if last_msg.upper() == "SIGN":
                    print("Approval received via Telegram!")
                    approved = True
                    break
            time.sleep(3)

        if not approved:
            raise Exception("Transaction aborted: Telegram approval timed out.")
        
        message_hash = Web3.solidity_keccak(
            ['bytes32', 'string', 'uint256', 'uint256', 'uint256', 'uint256', 'string'],
            [delivery_id, imo_number, supplier_id, density, expected_sulphur, qty, sample_id]
        )
        msg_eth_signed = encode_defunct(message_hash)
        
        sig_supplier = self.w3.eth.account.sign_message(msg_eth_signed, private_key=supplier_key).signature
        sig_chief = self.w3.eth.account.sign_message(msg_eth_signed, private_key=chief_key).signature

        print("Submitting signatures to blockchain...")
        receipt = self._send_transaction(
            self.contract.functions.finalizeBunker(
                delivery_id, density, qty, sample_id, sig_supplier, sig_chief
            ),
            self.admin_private_key
        )

        if receipt.status == 1:
            self.notify_telegram_success(delivery_id.hex(), receipt.transactionHash.hex(), qty)
        
        return receipt
    
    def notify_telegram_success(self, delivery_id_str, tx_hash, qty):
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("CHIEF_CHAT_ID")
        
        success_msg = (
            f"*eBDN FINALIZED ON-CHAIN*\n\n"
            f"*ID:* `{delivery_id_str}`\n"
            f"*Qty:* {qty} MT\n"
            f"*Tx:* [{tx_hash[:12]}...](https://etherscan.io/tx/{tx_hash})\n\n"
            f"The record is now immutable."
        )
        
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": success_msg, "parse_mode": "Markdown"}
        )
        
    def anchor_quantum_seal(self, delivery_id_bytes: bytes, pdf_hash_hex: str, quantum_sig_bytes: bytes):
        admin_address = self.w3.eth.account.from_key(self.admin_private_key).address
        
        tx = self.contract.functions.anchorQuantumSeal(
            delivery_id_bytes,    
            pdf_hash_hex,         
            quantum_sig_bytes     
        ).build_transaction({
            'from': admin_address,
            'nonce': self.w3.eth.get_transaction_count(admin_address),
            'gas': 1000000,
            'gasPrice': self.w3.to_wei('20', 'gwei')
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.admin_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
        
    def _send_transaction(self, contract_function, private_key):
        account = self.w3.eth.account.from_key(private_key)
        
        txn = contract_function.build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': 500000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(account.address),
        })

        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=private_key)
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            return self.w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            print(f"Transaction Failed! Possible Ownership Issue: {e}")
            raise e