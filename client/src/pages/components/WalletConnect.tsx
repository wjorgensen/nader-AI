import { useState, useEffect } from 'react';
import styles from '../../styles/Home.module.css';
import { useConnectModal } from '@rainbow-me/rainbowkit';
import { useAccount, useSendTransaction, useTransaction } from 'wagmi';

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
  
  // Rainbow Kit and Wagmi hooks
  const { openConnectModal } = useConnectModal();
  const { address, isConnected } = useAccount();
  const { sendTransaction, data: transactionData, error: sendError } = useSendTransaction();
  
  // Transaction confirmation hook - conditionally run it
  const transactionResult = useTransaction({ 
    hash: txHash
  });
  
  const isConfirming = txHash ? transactionResult.isLoading : false;
  const isConfirmed = txHash ? transactionResult.isSuccess : false;

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

    sendTransaction({
      to: '0xbA8C2947d12C34A4319D1edCbaE8B6F0736b4467', // Replace with actual recipient address
      value: BigInt(100000000000000), // 0.001 ETH in wei (adjust as needed)
    });
  };

  // Handle disconnect
  useEffect(() => {
    const handleDisconnect = () => {
      if (!isConnected && !txHash) {
        onProviderDisconnect();
      }
    };

    // Check connection status when it changes
    handleDisconnect();
    
    return () => {
      // Cleanup if needed
    };
  }, [isConnected, txHash, onProviderDisconnect]);

  return (
    <div className={styles.walletConnectContainer}>
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