import { useState, useEffect, useRef } from 'react';
import styles from '../../styles/Home.module.css';
import { useConnectModal } from '@rainbow-me/rainbowkit';
import { useAccount, useSendTransaction, useTransaction } from 'wagmi';
import ChainSelector from './ChainSelector';

interface WalletConnectProps {
  onPaymentComplete: () => void;
  onPaymentRejected: (reason: string) => void;
  onProviderDisconnect: () => void;
}

// Define the hex string type more explicitly
type HexString = `0x${string}`;

const WalletConnect: React.FC<WalletConnectProps> = ({ 
  onPaymentComplete, 
  onPaymentRejected, 
  onProviderDisconnect 
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  // Use the more explicit type definition
  const [txHash, setTxHash] = useState<HexString | undefined>(undefined);
  const [selectedChainId, setSelectedChainId] = useState<number>(8453); // Default to Base
  
  // Rainbow Kit and Wagmi hooks
  const { openConnectModal } = useConnectModal();
  const { address, isConnected } = useAccount();
  const { sendTransaction, data: transactionData, error: sendError } = useSendTransaction();
  
  // Track if we've ever been connected
  const hasEverConnected = useRef(false);
  
  // Transaction confirmation hook - conditionally run it
  const transactionResult = useTransaction({ 
    hash: txHash
  });
  
  const isConfirming = txHash ? transactionResult.isLoading : false;
  const isConfirmed = txHash ? transactionResult.isSuccess : false;

  // Handle chain change
  const handleChainChange = (chainId: number) => {
    setSelectedChainId(chainId);
  };

  // Add this effect to capture the transaction hash when available
  useEffect(() => {
    if (transactionData) {
      setTxHash(transactionData);
    }
  }, [transactionData]);

  useEffect(() => {
    if (sendError) {
      setIsProcessing(false);
      const reason = sendError instanceof Error ? sendError.message : 'Unknown payment error';
      onPaymentRejected(reason);
    }
  }, [sendError, onPaymentRejected]);

  // Effect for watching transaction confirmation
  useEffect(() => {
    if (isConfirmed && txHash) {
      // Transaction confirmed on the blockchain
      setIsProcessing(false);
      onPaymentComplete();
    }
  }, [isConfirmed, txHash, onPaymentComplete]);
  
  
  // Send payment function using Wagmi
  const handleSendPayment = () => {
    setIsProcessing(true);

    // Recipient addresses by chain
    const recipientAddresses: Record<number, `0x${string}`> = {
      8453: '0xbA8C2947d12C34A4319D1edCbaE8B6F0736b4467', // Base recipient
      324: '0xbA8C2947d12C34A4319D1edCbaE8B6F0736b4467',  // zkSync recipient
      747: '0xbA8C2947d12C34A4319D1edCbaE8B6F0736b4467'   // Flow recipient
    };

    // Payment amounts by chain - adjust based on token values
    const paymentAmounts: Record<number, bigint> = {
      8453: BigInt(100000000000000), // 0.001 ETH on Base
      324: BigInt(100000000000000),  // 0.001 ETH on zkSync
      747: BigInt(1000000000000000)  // 0.01 FLOW on Flow (adjusted for different token value)
    };

    sendTransaction({
      to: recipientAddresses[selectedChainId],
      value: paymentAmounts[selectedChainId],
    });
  };

  // Handle disconnect only after a wallet has connected and then disconnected
  useEffect(() => {
    // If we connect, mark that we've been connected
    if (isConnected) {
      hasEverConnected.current = true;
    }
    
    // Only trigger disconnect if we previously connected and then disconnected
    if (hasEverConnected.current && !isConnected && !txHash) {
      onProviderDisconnect();
    }
  }, [isConnected, txHash, onProviderDisconnect]);

  return (
    <div className={styles.walletConnectContainer}>
      {/* Chain Selector appears at the top regardless of connection status */}
      <ChainSelector onChainChange={handleChainChange} />
      
      {!isConnected ? (
        <>
          <p>Please connect your wallet to process the payment.</p>
          <button 
            className={styles.sendButton}
            onClick={openConnectModal}
            disabled={isProcessing}
          >
            {isProcessing ? 'Connecting...' : 'Connect Wallet'}
          </button>
        </>
      ) : (
        <>
          <p>Wallet connected! Please send payment to continue.</p>
          <p className={styles.walletAddress}>Your address: {address}</p>
          <button 
            className={styles.sendButton}
            onClick={handleSendPayment}
            disabled={isProcessing || isConfirming}
          >
            {isConfirming ? 'Confirming transaction...' : 
              isProcessing ? 'Processing...' : 'Send Payment'}
          </button>
          {isConfirming && (
            <p className={styles.transactionStatus}>
              Waiting for transaction confirmation on the blockchain...
            </p>
          )}
        </>
      )}
    </div>
  );
} 

export default WalletConnect;