// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Ownable} from "solady/auth/Ownable.sol";

/**
 * @title AgentWallet
 * @dev A wallet contract for AI agents that supports withdrawals and referral payments
 */
contract AgentWallet is Ownable {
    uint256 public constant REFERRAL_FEE = 0.01 ether;
    
    event Withdrawal(address indexed owner, uint256 amount);
    event ReferralPaid(address indexed referrer, uint256 amount);
    
    /**
     * @dev Constructor that sets the deployer as the initial owner
     */
    constructor() {
        _initializeOwner(msg.sender);
    }
    
    /**
     * @dev Fallback function to accept ETH transfers with data
     */
    fallback() external payable {}
    
    /**
     * @dev Receive function to accept ETH transfers
     */
    receive() external payable {}
    
    /**
     * @dev Withdraws all funds to the owner address
     */
    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
        
        (bool success, ) = owner().call{value: balance}("");
        require(success, "Transfer failed");
        
        emit Withdrawal(owner(), balance);
    }
    
    /**
     * @dev Pays the standard referral fee to a specified wallet
     * @param referrer Address to receive the referral fee
     */
    function payReferral(address referrer) external onlyOwner {
        require(referrer != address(0), "Invalid referrer address");
        require(address(this).balance >= REFERRAL_FEE, "Insufficient funds for referral");
        
        (bool success, ) = referrer.call{value: REFERRAL_FEE}("");
        require(success, "Referral payment failed");
        
        emit ReferralPaid(referrer, REFERRAL_FEE);
    }
}
