

# Maritime ZK-Shield: Future-Proof eBDN Registry

A decentralized Maritime Registry for Electronic Bunker Delivery Notes (eBDNs), leveraging Zero-Knowledge Proofs (Noir) and Post-Quantum Cryptography to ensure secure, private, and tamper-proof fuel transactions.

## Overview

This project replicates and enhances digital workflows for maritime bunkering (inspired by platforms like ZeroNorth). It addresses the conflict between data privacy and regulatory compliance:

* **Compliance:** Vessels can prove fuel sulfur content is within legal limits (e.g., < 0.50%) on-chain.
* **Privacy:** The exact sulfur percentage and proprietary fuel data remain hidden off-chain.
* **Security:** Trust is anchored using a "Quantum Seal" involving ECDSA and ML-DSA signature hashes.

## Tech Stack

* **ZKP:** Noir Lang (UltraHonk Backend)
* **Smart Contracts:** Solidity 0.8.28 (Foundry)
* **Frontend/Tooling:** Node.js, ethers.js, @aztec/bb.js
* **Security:** ECDSA (OpenZeppelin) and ML-DSA readiness

---

## Architecture

### 1. Zero-Knowledge Circuit

The Noir circuit performs a range check on the private `sulphur_content` against a public `threshold`. It returns a `commitment` (Poseidon hash) to bind the proof to a specific bunker delivery, preventing proof reuse.

### 2. Smart Contract Registry

The `MaritimeRegistryUpdated.sol` contract manages:

* **Ship and Supplier Registration:** Restricts access to authorized entities.
* **ZK-Nomination:** Verifies the SNARK proof before allowing a delivery to be nominated.
* **Dual-Signature Finalization:** Requires signatures from both the Chief Engineer and Barge Master.
* **Quantum Anchoring:** Seals final PDF hashes with post-quantum signature hashes.

---

## Getting Started

### Prerequisites

* Nargo v1.0.0-beta.18
* Foundry
* Node.js and npm

### Installation

1. Install dependencies:
```bash
npm install

```


2. Compile Circuits:
```bash
cd circuits && nargo compile

```


3. Build Contracts:
```bash
forge build --via-ir

```

## Contribution and Discussion

Current development challenges regarding the Honk verifier stack depth are documented here:
[GitHub Discussion #29](https://github.com/Cyfrin/noir-programming-and-zk-circuits-cu/discussions/29)

---
