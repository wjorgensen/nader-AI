import { useState, useEffect } from 'react';
import styles from '../../styles/Home.module.css';
import { useConnectModal } from '@rainbow-me/rainbowkit';
import { useAccount, useSendTransaction } from 'wagmi';

interface WalletConnectProps {
  onPaymentComplete: () => void;
}

export default function WalletConnect({ onPaymentComplete }: WalletConnectProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentComplete, setPaymentComplete] = useState(false);
  
  // Rainbow Kit and Wagmi hooks
  const { openConnectModal } = useConnectModal();
  const { address, isConnected } = useAccount();
  const { sendTransaction, isPending } = useSendTransaction();
  
  // Send payment function using Wagmi
  const handleSendPayment = async () => {
    setIsProcessing(true);
    
    try {
      await sendTransaction({
        to: '0xbA8C2947d12C34A4319D1edCbaE8B6F0736b4467', // Replace with actual recipient address
        value: BigInt(100000000000000), // 0.001 ETH in wei (adjust as needed)
      });
      
      setPaymentComplete(true);
      onPaymentComplete();
    } catch (error) {
      console.error('Payment error:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Effect to handle transaction pending state
  useEffect(() => {
    if (isPending) {
      setIsProcessing(true);
    } else if (!isPending && isProcessing) {
      setIsProcessing(false);
    }
  }, [isPending]);

  if (paymentComplete) {
    return null; // Return null because the message will be handled by the parent component
  }

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
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Send Payment'}
          </button>
        </>
      )}
    </div>
  );
} 