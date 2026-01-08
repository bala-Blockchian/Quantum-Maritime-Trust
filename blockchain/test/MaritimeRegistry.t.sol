// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console, Vm} from "forge-std/Test.sol";
import {MaritimeRegistry, MessageHashUtils} from "../src/MaritimeRegistry.sol";

contract MaritimeRegistryTest is Test {
    MaritimeRegistry public registry;

    Vm.Wallet public admin;
    Vm.Wallet public supplier;
    Vm.Wallet public chiefEng;

    string constant IMO = "IMO9876543";
    uint256 constant SUPPLIER_ID = 5500;
    bytes32 constant DELIVERY_ID = keccak256("Bunker_Job_001");
    uint256 constant EXPECTED_SULPHUR = 49;

    string constant MOCK_PDF_HASH = "af2bdbe1aa9b6ec1e2ade1d694f41fc71a831d02621ec82097a1";
    bytes MOCK_QUANTUM_SIG = hex"aabbccddeeff11223344556677889900aabbccddeeff";

    function setUp() public {
        admin = vm.createWallet("admin_wallet");
        supplier = vm.createWallet("supplier_wallet");
        chiefEng = vm.createWallet("chief_engineer_wallet");

        vm.prank(admin.addr);
        registry = new MaritimeRegistry();
    }

    function _reachFinalizedState() internal {
        vm.startPrank(admin.addr);
        registry.registerShip(IMO, chiefEng.addr);
        registry.registerSupplier(SUPPLIER_ID, supplier.addr);
        vm.stopPrank();

        vm.prank(supplier.addr);
        registry.nominateBunker(DELIVERY_ID, IMO, SUPPLIER_ID, EXPECTED_SULPHUR);

        uint256 finalDensity = 991;
        uint256 finalQty = 500;
        string memory sampleId = "SEAL-2026";

        bytes32 messageHash =
            keccak256(abi.encode(DELIVERY_ID, IMO, SUPPLIER_ID, finalDensity, EXPECTED_SULPHUR, finalQty, sampleId));
        bytes32 ethSignedHash = MessageHashUtils.toEthSignedMessageHash(messageHash);

        (uint8 vS, bytes32 rS, bytes32 sS) = vm.sign(supplier.privateKey, ethSignedHash);
        bytes memory sigSupplier = abi.encodePacked(rS, sS, vS);

        (uint8 vC, bytes32 rC, bytes32 sC) = vm.sign(chiefEng.privateKey, ethSignedHash);
        bytes memory sigChief = abi.encodePacked(rC, sC, vC);

        vm.prank(admin.addr);
        registry.finalizeBunker(DELIVERY_ID, finalDensity, finalQty, sampleId, sigSupplier, sigChief);
    }

    function test_QuantumSealAnchoring() public {
        _reachFinalizedState();

        MaritimeRegistry.BunkerNote memory noteBefore = registry.getNote(DELIVERY_ID);
        assertEq(uint256(noteBefore.status), uint256(MaritimeRegistry.BunkerStatus.Finalized));

        vm.expectRevert();
        vm.prank(chiefEng.addr);
        registry.anchorQuantumSeal(DELIVERY_ID, MOCK_PDF_HASH, MOCK_QUANTUM_SIG);

        vm.prank(admin.addr);
        vm.expectEmit(true, false, false, true);
        emit MaritimeRegistry.QuantumSealAnchored(DELIVERY_ID, MOCK_PDF_HASH);

        registry.anchorQuantumSeal(DELIVERY_ID, MOCK_PDF_HASH, MOCK_QUANTUM_SIG);

        MaritimeRegistry.BunkerNote memory noteAfter = registry.getNote(DELIVERY_ID);
        assertEq(uint256(noteAfter.status), uint256(MaritimeRegistry.BunkerStatus.QuantumSealed));
        assertEq(noteAfter.pdfHash, MOCK_PDF_HASH);
        assertEq(noteAfter.quantumSignature, MOCK_QUANTUM_SIG);
    }

    function test_AnchorWithoutFinalization() public {
        vm.startPrank(admin.addr);
        registry.registerShip(IMO, chiefEng.addr);
        registry.registerSupplier(SUPPLIER_ID, supplier.addr);
        vm.stopPrank();

        vm.prank(supplier.addr);
        registry.nominateBunker(DELIVERY_ID, IMO, SUPPLIER_ID, EXPECTED_SULPHUR);

        vm.prank(admin.addr);
        vm.expectRevert("Bunker not finalized");
        registry.anchorQuantumSeal(DELIVERY_ID, MOCK_PDF_HASH, MOCK_QUANTUM_SIG);
    }
}
