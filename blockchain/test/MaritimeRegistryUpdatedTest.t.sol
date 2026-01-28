// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console} from "forge-std/Test.sol";
import {MaritimeRegistryUpdated} from "../src/MaritimeRegistryUpdated.sol";
import {HonkVerifier} from "../src/Verifier.sol";

contract MaritimeRegistryTest is Test {
    MaritimeRegistryUpdated public registry;
    HonkVerifier public verifier;

    address public owner = address(this);
    address public chiefEng = makeAddr("chiefEng");
    address public barge = makeAddr("barge");
    
    string public constant IMO = "IMO9876543";
    uint256 public constant SUPPLIER_ID = 123;
    bytes32 public constant DELIVERY_ID = keccak256("DELIVERY_001");

    function setUp() public {
        verifier = new HonkVerifier();
        registry = new MaritimeRegistryUpdated(verifier);

        registry.registerShip(IMO, chiefEng);
        registry.registerSupplier(SUPPLIER_ID, barge);
    }

    function _generateZKProof(uint256 sulphur, uint256 threshold, bytes32 salt) 
        internal 
        returns (bytes memory proof, bytes32 commitment) 
    {
        string[] memory inputs = new string[](7);
        inputs[0] = "npx";
        inputs[1] = "tsx";
        inputs[2] = "js-script/generate_noir_proof.ts"; 
        inputs[3] = vm.toString(sulphur);
        inputs[4] = vm.toString(threshold);
        inputs[5] = vm.toString(salt);

        bytes memory result = vm.ffi(inputs);
        (bytes memory _proof, bytes32[] memory _publicInputs) = abi.decode(result, (bytes, bytes32[]));
        
        return (_proof, _publicInputs[1]);
    }

    function test_FullBunkerLifecycle() public {
        uint256 actualSulphur = 40; // 0.40%
        uint256 threshold = 50;    // 0.50%
        bytes32 salt = keccak256("secret_salt");

        (bytes memory proof, bytes32 commitment) = _generateZKProof(actualSulphur, threshold, salt);

        vm.prank(barge);
        registry.nominateBunker(
            DELIVERY_ID, 
            IMO, 
            SUPPLIER_ID, 
            actualSulphur, 
            proof, 
            threshold, 
            commitment
        );

        MaritimeRegistryUpdated.BunkerNote memory note = registry.getNote(DELIVERY_ID);
        assertEq(uint(note.status), uint(MaritimeRegistryUpdated.BunkerStatus.Nominated));
        assertEq(note.sulphurCommitment, commitment);
    }

    function testFail_NominateWithInvalidProof() public {
        uint256 actualSulphur = 60;
        uint256 threshold = 50; 
        
        (bytes memory proof, bytes32 commitment) = _generateZKProof(actualSulphur, threshold, keccak256("salt"));

        vm.prank(barge);
        registry.nominateBunker(DELIVERY_ID, IMO, SUPPLIER_ID, actualSulphur, proof, threshold, commitment);
    }
}