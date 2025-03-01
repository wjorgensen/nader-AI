import { useState, useEffect, useRef } from 'react';
import { useConfig, useChainId, useSwitchChain } from 'wagmi';
import styles from '../../styles/Home.module.css';

interface ChainSelectorProps {
  onChainChange: (chainId: number) => void;
}

const ChainSelector: React.FC<ChainSelectorProps> = ({ onChainChange }) => {
  const config = useConfig();
  const chainId = useChainId();
  const { error, isPending, switchChain } = useSwitchChain();
  const [selectedChainId, setSelectedChainId] = useState<number>(chainId);
  const indicatorRef = useRef<HTMLDivElement>(null);
  const itemsRef = useRef<Map<number, HTMLDivElement>>(new Map());

  useEffect(() => {
    if (chainId) {
      setSelectedChainId(chainId);
      onChainChange(chainId);
    }
  }, [chainId, onChainChange]);

  // Position the indicator when selection changes
  useEffect(() => {
    const moveIndicator = () => {
      const selectedElement = itemsRef.current.get(selectedChainId);
      const indicator = indicatorRef.current;
      
      if (selectedElement && indicator) {
        indicator.style.width = `${selectedElement.offsetWidth}px`;
        indicator.style.left = `${selectedElement.offsetLeft}px`;
      }
    };
    
    moveIndicator();
    window.addEventListener('resize', moveIndicator);
    
    return () => window.removeEventListener('resize', moveIndicator);
  }, [selectedChainId]);

  const handleChainChange = (chainId: number) => {
    setSelectedChainId(chainId);
    onChainChange(chainId);
    if (switchChain) {
      switchChain({ chainId });
    }
  };

  return (
    <div className={styles.chainSelectorContainer}>
      <div className={styles.pillSelector}>
        <div className={styles.pillBackground} ref={indicatorRef}></div>
        {config.chains.map((chainOption) => (
          <div 
            key={chainOption.id}
            ref={(el) => {
              if (el) itemsRef.current.set(chainOption.id, el);
            }}
            className={`${styles.pillOption} ${selectedChainId === chainOption.id ? styles.selectedPill : ''}`}
            onClick={() => handleChainChange(chainOption.id)}
          >
            {chainOption.name}
          </div>
        ))}
      </div>
      {isPending && (
        <div className={styles.switchingNetwork}>
          Switching network...
        </div>
      )}
      {error && (
        <div className={styles.switchError}>
          {error.message}
        </div>
      )}
    </div>
  );
};

export default ChainSelector; 