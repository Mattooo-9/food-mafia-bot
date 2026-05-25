import { useTonConnectUI } from '@tonconnect/ui-react';

export const useTonConnect = () => {
  const [tonConnectUI] = useTonConnectUI();

  return {
    sender: {
      sendTransaction: async (args: any) => {
        return tonConnectUI.sendTransaction({
          messages: [
            {
              address: args.to.toString(),
              amount: args.value.toString(),
              payload: args.body?.toBoc().toString('base64'),
            },
          ],
          validUntil: Date.now() + 5 * 60 * 1000, // 5 minutes for user to approve
        });
      },
    },
    connected: tonConnectUI.connected,
    wallet: tonConnectUI.wallet,
    network: tonConnectUI.wallet?.account.network,
  };
};
