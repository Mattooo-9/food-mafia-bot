import React from 'react';
import { LayoutGrid, Rainbow, ShoppingBag, User } from 'lucide-react';

export const TabBar = ({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (tab: string) => void }) => {
  const tabs = [
    { id: 'catalog', label: 'Catalog', icon: LayoutGrid },
    { id: 'rainbow', label: 'Rainbow', icon: Rainbow },
    { id: 'orders', label: 'Orders', icon: ShoppingBag },
    { id: 'profile', label: 'Profile', icon: User },
  ];

  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: '70px',
      background: 'var(--tg-theme-secondary-bg-color, #f0f0f0)',
      display: 'flex',
      justifyContent: 'space-around',
      alignItems: 'center',
      borderTopLeftRadius: '20px',
      borderTopRightRadius: '20px',
      boxShadow: '0 -4px 10px rgba(0,0,0,0.05)',
      zIndex: 1000
    }}>
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: 'none',
              border: 'none',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              cursor: 'pointer',
              color: isActive ? 'var(--tg-theme-button-color, #3390ec)' : 'var(--tg-theme-hint-color, #999)'
            }}
          >
            <Icon size={24} />
            <span style={{ fontSize: '10px' }}>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
};
