# Maritime Quantum-Resistant eBDN Service

This service provides a Post-Quantum Seal for bunker delivery notes using NIST-standardized ML-DSA (Dilithium).

## Features
- **Blockchain Listener:** Monitors for `BunkerFinalized` events.
- **Quantum Vault:** Signs eBDN hashes using `liboqs` (ML-DSA-65).
- **On-Chain Anchoring:** Anchors the PQC signature and SHA3-512 hash back to the blockchain.

## Prerequisites
1. **liboqs**: `brew install liboqs` (macOS)
2. **Dependencies**: `pip install -r requirements.txt`
3. **PQC Wrapper**: `pip install git+https://github.com/open-quantum-safe/liboqs-python.git`

## Environment Variables
Create a `.env` file:
- `PRIVATE_KEY`: Admin wallet for anchoring.
- `CONTRACT_ADDRESS`: Deployed Maritime contract.
- `RPC_URL`: e.g., http://127.0.0.1:8545