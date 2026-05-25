import React, { useState } from 'react';
import { TonConnectUIProvider } from '@tonconnect/ui-react';
import { TabBar } from './components/TabBar';
import { RainbowCategory } from './components/RainbowCategory';
import { FoodCard } from './components/FoodCard';

const mockItems = [
  { id: '1', name: 'Mafia Burger', price: 0.5, params: { bju: '20/15/30' }, trust: 98, origin: 'Local Farm' },
  { id: '2', name: 'Napoli Pizza', price: 0.3, params: { bju: '10/12/45' }, trust: 95, origin: 'Italy' },
];

function App() {
  const [activeTab, setActiveTab] = useState('catalog');

  return (
    <TonConnectUIProvider manifestUrl="https://food-mafia-bot.onrender.com/tonconnect-manifest.json">
      <div style={{ paddingBottom: '80px' }}>
        {activeTab === 'catalog' && (
          <div style={{ padding: '15px' }}>
            <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', marginBottom: '20px' }}>
              <button style={{ padding: '8px 15px', borderRadius: '20px', border: '1px solid #ccc', whiteSpace: 'nowrap' }}>Healthy</button>
              <button style={{ padding: '8px 15px', borderRadius: '20px', border: '1px solid #ccc', whiteSpace: 'nowrap' }}>Vegan</button>
              <button style={{ padding: '8px 15px', borderRadius: '20px', border: '1px solid #ccc', whiteSpace: 'nowrap' }}>Keto</button>
            </div>
            {mockItems.map(item => <FoodCard key={item.id} item={item} />)}
          </div>
        )}

        {activeTab === 'rainbow' && (
          <div style={{ padding: '15px' }}>
            <RainbowCategory type="energy" title="Energy & Red" color="#ff4d4d" />
            <RainbowCategory type="detox" title="Detox & Green" color="#4db24d" />
            <RainbowCategory type="balance" title="Balance & Purple" color="#994db2" />
          </div>
        )}

        <TabBar activeTab={activeTab} setActiveTab={setActiveTab} />
      </div>
    </TonConnectUIProvider>
  );
}

export default App;
