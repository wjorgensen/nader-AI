import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { WagmiProvider, createConfig, http } from 'wagmi';
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RainbowKitProvider, lightTheme } from '@rainbow-me/rainbowkit';
import '@rainbow-me/rainbowkit/styles.css';
import { base } from 'wagmi/chains';
import { zksync } from 'viem/chains';
import { flowMainnet } from 'viem/chains';

// Create wagmi config with only these chains
const config = createConfig({
  chains: [base, zksync, flowMainnet],
  transports: {
    [base.id]: http(), // base.id is 8453
    [zksync.id]: http(), // zksync.id is 324
    [flowMainnet.id]: http(), // flow.id is 747
  },
});

// Create a React-Query client
const queryClient = new QueryClient();

export default function App({ Component, pageProps }: AppProps) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider theme={lightTheme()}>
          <Component {...pageProps} />
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
