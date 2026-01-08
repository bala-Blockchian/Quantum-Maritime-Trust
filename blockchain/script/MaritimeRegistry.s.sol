// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console} from "forge-std/Script.sol";
import {MaritimeRegistry} from "../src/MaritimeRegistry.sol";

contract DeployMaritime is Script {
    function run() external returns (MaritimeRegistry) {
        uint256 deployerPrivateKey = vm.envOr(
            "ADMIN_PRIVATE_KEY",
            uint256(
                0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
            )
        );

        vm.startBroadcast(deployerPrivateKey);
        MaritimeRegistry registry = new MaritimeRegistry();
        vm.stopBroadcast();

        console.log("-----------------------------------------");
        console.log("MaritimeRegistry deployed at:", address(registry));
        console.log("Deployer Address:", vm.addr(deployerPrivateKey));
        console.log("-----------------------------------------");

        return registry;
    }
}

// forge script script/MaritimeRegistry.s.sol --rpc-url http://127.0.0.1:8545 --broadcast --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

//   -----------------------------------------
//   MaritimeRegistry deployed at: 0x5FbDB2315678afecb367f032d93F642f64180aa3
//   Deployer Address: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
//   -----------------------------------------
