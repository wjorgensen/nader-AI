import { useState, useEffect } from 'react';
import styles from '../../styles/Home.module.css';
import { 
  useAccount, 
  useConnect, 
  useDisconnect, 
  useBalance, 
  useSendTransaction,
  useWaitForTransactionReceipt,
  useChainId,
  useSwitchChain
} from 'wagmi';
import { 
  ConnectButton,
  useConnectModal
} from '@rainbow-me/rainbowkit';
import { parseEther } from 'viem';

// Base Sepolia Chain ID
const BASE_SEPOLIA_CHAIN_ID = 84532;

interface WalletConnectProps {
  onPaymentComplete: () => void;
}

export default function WalletConnect({ onPaymentComplete }: WalletConnectProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Wallet connection states
  const { address, isConnected } = useAccount();
  const { openConnectModal } = useConnectModal();
  const { disconnect } = useDisconnect();
  const chainId = useChainId();
  
  // Chain switching
  const { switchChain } = useSwitchChain();
  
  // Get ETH balance if connected
  const { data: balance } = useBalance({
    address: address,
  });
  
  // Payment transaction - using sendTransaction instead of writeContract
  const { sendTransaction, isPending: isSendPending, data: sendData, error: sendError } = useSendTransaction();
  
  // Wait for transaction receipt - only when we have a hash
  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({
    hash: sendData,
  });

  // Check if we're on Base Sepolia
  const isCorrectNetwork = chainId === BASE_SEPOLIA_CHAIN_ID;

  // Get the explorer URL based on the chain
  const getExplorerUrl = (txHash: string) => {
    // Base Sepolia
    if (chainId === BASE_SEPOLIA_CHAIN_ID) {
      return `https://sepolia.basescan.org/tx/${txHash}`;
    }
    // Default to Ethereum mainnet
    return `https://etherscan.io/tx/${txHash}`;
  };
  
  // Handle connect wallet through RainbowKit
  const handleConnect = async () => {
    if (!isConnected && openConnectModal) {
      setErrorMessage(null);
      openConnectModal();
    }
  };

  // Handle network switching
  const handleSwitchNetwork = () => {
    setErrorMessage(null);
    try {
      switchChain({ chainId: BASE_SEPOLIA_CHAIN_ID });
    } catch (error) {
      console.error('Network switch error:', error);
      setErrorMessage('Failed to switch network. Please try manually.');
    }
  };
  
  // Handle payment with Wagmi
  const handlePayment = async () => {
    if (!isConnected) {
      return;
    }
    
    // Ensure we're on Base Sepolia
    if (!isCorrectNetwork) {
      setErrorMessage('Please switch to Base Sepolia network first');
      return;
    }
    
    setIsProcessing(true);
    setErrorMessage(null);
    
    try {
      // Send ETH directly to the specified address instead of calling a contract
      sendTransaction({
        to: '0xbA8C2947d12C34A4319D1edCbaE8B6F0736b4467',
        value: parseEther('0.0001'), // 0.0001 ETH fee
        chainId: BASE_SEPOLIA_CHAIN_ID, // Explicitly specify Base Sepolia chain ID
      });
    } catch (error) {
      console.error('Payment error:', error);
      setIsProcessing(false);
      setErrorMessage('Error sending transaction. Please try again.');
    }
  };
  
  // Handle successful transaction
  useEffect(() => {
    if (isConfirmed) {
      setIsProcessing(false);
      setErrorMessage(null);
      onPaymentComplete();
    }
  }, [isConfirmed, onPaymentComplete]);
  
  // Store sendData in txHash state when available
  useEffect(() => {
    if (sendData) {
      setTxHash(sendData);
    }
  }, [sendData]);
  
  // Handle errors, including user rejection
  useEffect(() => {
    if (sendError) {
      console.error('Transaction error:', sendError);
      setIsProcessing(false);
      
      // Check for user rejection error messages
      const errorString = sendError.message || '';
      if (
        errorString.includes('rejected') || 
        errorString.includes('denied') || 
        errorString.includes('cancelled') ||
        errorString.includes('user denied') ||
        errorString.includes('user rejected')
      ) {
        setErrorMessage('Transaction was rejected. Please try again when you\'re ready.');
      } else if (errorString.includes('insufficient funds')) {
        setErrorMessage('Insufficient funds in your wallet. Please add funds to continue.');
      } else if (errorString.includes('network')) {
        setErrorMessage('Network error. Please make sure you\'re connected to Base Sepolia.');
      } else {
        setErrorMessage('Error processing transaction. Please try again.');
      }
    }
  }, [sendError]);

  // Check for network changes
  useEffect(() => {
    if (isConnected && chainId !== BASE_SEPOLIA_CHAIN_ID) {
      setErrorMessage('Please switch to Base Sepolia network');
    } else if (isConnected) {
      setErrorMessage(null);
    }
  }, [chainId, isConnected]);
  
  return (
    <div className={styles.walletConnectContainer}>
      <p>Please connect your wallet to process the payment on Base Sepolia.</p>
      
      {/* Display balance if connected */}
      {isConnected && address && (
        <div className={styles.walletInfo}>
          <p>Connected: {address.slice(0, 6)}...{address.slice(-4)}</p>
          {balance && (
            <p>Balance: {balance.formatted.substring(0, 8)} {balance.symbol}</p>
          )}
          {isConnected && !isCorrectNetwork && (
            <p className={styles.networkWarning}>
              ⚠️ You are not on Base Sepolia network
            </p>
          )}
        </div>
      )}
      
      {/* Display error message if any */}
      {errorMessage && (
        <div className={styles.errorMessage}>
          {errorMessage}
        </div>
      )}
      
      {/* RainbowKit Connect Button - for a more customized experience */}
      <div className={styles.rainbowKitWrapper}>
        <ConnectButton.Custom>
          {({
            account,
            chain,
            openAccountModal,
            openChainModal,
            openConnectModal,
            mounted,
          }) => {
            return (
              <div
                {...(!mounted && {
                  'aria-hidden': true,
                  'style': {
                    opacity: 0,
                    pointerEvents: 'none',
                    userSelect: 'none',
                  },
                })}
              >
                {(() => {
                  if (!mounted || !account || !chain) {
                    return (
                      <button 
                        className={styles.sendButton}
                        onClick={openConnectModal}
                        disabled={isProcessing}
                      >
                        {isProcessing ? 'Processing...' : 'Connect Wallet'}
                      </button>
                    );
                  }
                  
                  // Check if the chain is supported - specifically Base Sepolia
                  if (chain.id !== BASE_SEPOLIA_CHAIN_ID) {
                    return (
                      <button 
                        className={styles.sendButton}
                        onClick={openChainModal}
                      >
                        Switch to Base Sepolia
                      </button>
                    );
                  }

                  return (
                    <button 
                      className={styles.sendButton}
                      onClick={isSendPending || isConfirming ? undefined : handlePayment}
                      disabled={isProcessing || isSendPending || isConfirming}
                    >
                      {isProcessing || isSendPending || isConfirming 
                        ? 'Processing Payment...' 
                        : 'Pay Fee (0.0001 ETH)'}
                    </button>
                  );
                })()}
              </div>
            );
          }}
        </ConnectButton.Custom>
      </div>
      
      {/* Display transaction hash if available */}
      {txHash && (
        <div className={styles.walletInfo}>
          <p>Transaction submitted!</p>
          <p>
            <a 
              href={getExplorerUrl(txHash)} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ wordBreak: 'break-all', fontSize: '12px' }}
            >
              View on Block Explorer: {txHash.slice(0, 10)}...{txHash.slice(-8)}
            </a>
          </p>
        </div>
      )}
    </div>
  );
} 