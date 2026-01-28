// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {MessageHashUtils} from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {IVerifier} from "./Verifier.sol";

contract MaritimeRegistryUpdated is Ownable {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    IVerifier public immutable i_verifier;

    enum BunkerStatus {
        None,
        Nominated,
        Finalized,
        QuantumSealed
    }

    struct BunkerNote {
        string imoNumber;
        uint256 supplierId;
        uint256 densityAt15C;
        uint256 sulphurContent;
        bytes32 sulphurCommitment;
        uint256 quantityMT;
        string sampleId;
        uint256 timestamp;
        BunkerStatus status;
        bytes signatureSupplier;
        bytes signatureChiefEng;
        string pdfHash;
        bytes32 quantumSignatureHash;
    }

    mapping(string => address) public shipToChiefEng;
    mapping(uint256 => address) public supplierToBarge;
    mapping(bytes32 => BunkerNote) public bunkerNotes;

    event BunkerNominated(bytes32 indexed deliveryId, string imo, uint256 supplierId, bytes32 commitment);
    event BunkerFinalized(
        bytes32 indexed deliveryId, string imo, uint256 quantity, bytes sigSupplier, bytes sigChiefEng
    );
    event QuantumSealAnchored(bytes32 indexed deliveryId, string pdfHash);

    constructor(IVerifier _verifier) Ownable(msg.sender) {
        i_verifier = _verifier;
    }

    function registerShip(string calldata _imo, address _chiefEng) external onlyOwner {
        shipToChiefEng[_imo] = _chiefEng;
    }

    function registerSupplier(uint256 _supplierId, address _barge) external onlyOwner {
        supplierToBarge[_supplierId] = _barge;
    }

    function nominateBunker(
        bytes32 _deliveryId,
        string calldata _imo,
        uint256 _supplierId,
        uint256 _expectedSulphur,
        bytes calldata _proof,
        uint256 _threshold,
        bytes32 _commitment
    ) external {
        require(msg.sender == supplierToBarge[_supplierId], "Only authorized barge can nominate");
        require(bunkerNotes[_deliveryId].status == BunkerStatus.None, "Delivery ID exists");

        bytes32[] memory publicInputs = new bytes32[](2);
        publicInputs[0] = bytes32(_threshold);
        publicInputs[1] = _commitment;

        if (!i_verifier.verify(_proof, publicInputs)) {
            revert("MaritimeRegistry: Nominated fuel exceeds sulfur limits or invalid proof");
        }

        BunkerNote storage note = bunkerNotes[_deliveryId];
        note.imoNumber = _imo;
        note.supplierId = _supplierId;
        note.sulphurContent = _expectedSulphur;
        note.sulphurCommitment = _commitment;
        note.status = BunkerStatus.Nominated;

        emit BunkerNominated(_deliveryId, _imo, _supplierId, _commitment);
    }

    function finalizeBunker(
        bytes32 _deliveryId,
        uint256 _finalDensity,
        uint256 _finalQty,
        string calldata _sampleId,
        bytes calldata _sigSupplier,
        bytes calldata _sigChiefEng
    ) external onlyOwner {
        BunkerNote storage note = bunkerNotes[_deliveryId];
        require(note.status == BunkerStatus.Nominated, "Bunker not nominated");

        // ['bytes32', 'string', 'uint256', 'uint256', 'uint256', 'uint256', 'string'],
        // [delivery_id, imo_number, supplier_id, density, expected_sulphur, qty, sample_id]

        bytes32 messageHash = keccak256(
                abi.encode(
                    _deliveryId,
                    note.imoNumber,
                    note.supplierId,
                    _finalDensity,
                    note.sulphurContent,
                    _finalQty,
                    _sampleId
                )
            ).toEthSignedMessageHash();

        address recoveredSupplier = messageHash.recover(_sigSupplier);
        address recoveredChief = messageHash.recover(_sigChiefEng);

        require(recoveredSupplier == supplierToBarge[note.supplierId], "Invalid Supplier Signature");
        require(recoveredChief == shipToChiefEng[note.imoNumber], "Invalid Chief Engineer Signature");

        note.densityAt15C = _finalDensity;
        note.quantityMT = _finalQty;
        note.sampleId = _sampleId;
        note.signatureSupplier = _sigSupplier;
        note.signatureChiefEng = _sigChiefEng;
        note.timestamp = block.timestamp;
        note.status = BunkerStatus.Finalized;

        emit BunkerFinalized(_deliveryId, note.imoNumber, _finalQty, _sigSupplier, _sigChiefEng);
    }

    function anchorQuantumSeal(bytes32 _deliveryId, string calldata _pdfHash, bytes32 _quantumSigHash)
        external
        onlyOwner
    {
        BunkerNote storage note = bunkerNotes[_deliveryId];
        require(note.status == BunkerStatus.Finalized, "Bunker not finalized");

        note.pdfHash = _pdfHash;
        note.quantumSignatureHash = _quantumSigHash;
        note.status = BunkerStatus.QuantumSealed;

        emit QuantumSealAnchored(_deliveryId, _pdfHash);
    }

    function getNote(bytes32 _deliveryId) external view returns (BunkerNote memory) {
        return bunkerNotes[_deliveryId];
    }

    function verifyStoredNote(bytes32 _deliveryId)
        external
        view
        returns (bool allSignaturesValid, string memory imoVerified, address recoveredChief, address recoveredBarge)
    {
        BunkerNote storage note = bunkerNotes[_deliveryId];
        require(note.status >= BunkerStatus.Finalized, "Bunker note not finalized");

        bytes32 messageHash = keccak256(
                abi.encode(
                    _deliveryId,
                    note.imoNumber,
                    note.supplierId,
                    note.densityAt15C,
                    note.sulphurContent,
                    note.quantityMT,
                    note.sampleId
                )
            ).toEthSignedMessageHash();

        address actualBarge = messageHash.recover(note.signatureSupplier);
        address actualChief = messageHash.recover(note.signatureChiefEng);

        bool supplierMatch = (actualBarge == supplierToBarge[note.supplierId]);
        bool shipMatch = (actualChief == shipToChiefEng[note.imoNumber]);

        return ((supplierMatch && shipMatch), note.imoNumber, actualChief, actualBarge);
    }
}
