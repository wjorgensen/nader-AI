// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "forge-std/Script.sol";
import {AgentWallet} from "../src/agentWallet.sol";

contract DeployAgentWallet is Script {
    function run() external returns (AgentWallet) {
        // Start broadcasting transactions
        vm.startBroadcast();
        
        // Deploy the AgentWallet contract
        AgentWallet wallet = new AgentWallet();
        
        // Stop broadcasting
        vm.stopBroadcast();
        
        return wallet;
    }
}
