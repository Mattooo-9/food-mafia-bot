import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, ShieldCheck, MapPin } from 'lucide-react';

export const FoodCard = ({ item }: { item: any }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <motion.div
      layout
      transition={{ duration: 0.3 }}
      style={{
        background: 'var(--tg-theme-secondary-bg-color, #f0f0f0)',
        borderRadius: '20px',
        padding: '15px',
        marginBottom: '20px',
        position: 'relative',
        boxShadow: '0 4px 15px rgba(0,0,0,0.1)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
        <div style={{ width: '80px', height: '80px', borderRadius: '15px', background: '#ccc' }}></div>
        <div style={{ flex: 1 }}>
          <h4 style={{ margin: 0 }}>{item.name}</h4>
          <p style={{ margin: '5px 0', color: 'var(--tg-theme-hint-color, #999)' }}>{item.price} TON</p>
        </div>
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={() => setIsOpen(!isOpen)}
          style={{ background: 'none', border: 'none', cursor: 'pointer' }}
        >
          <Info size={20} color="var(--tg-theme-button-color, #3390ec)" />
        </motion.button>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{ marginTop: '15px', borderTop: '1px solid rgba(0,0,0,0.05)', paddingTop: '15px' }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.85rem' }}>
              <div><strong>BJU:</strong> {item.params.bju}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <ShieldCheck size={14} color="#4caf50" />
                Trust: {item.trust}%
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <MapPin size={14} color="#f44336" />
                {item.origin}
              </div>
            </div>
            <button style={{
              marginTop: '15px',
              width: '100%',
              padding: '10px',
              borderRadius: '10px',
              background: 'var(--tg-theme-button-color, #3390ec)',
              color: '#fff',
              border: 'none',
              fontWeight: 'bold'
            }}>
              Add to Basket
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
