import React from 'react';
import { motion } from 'framer-motion';

export const RainbowCategory = ({ type, title, color }: { type: string, title: string, color: string }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      style={{
        background: `linear-gradient(135deg, ${color} 0%, rgba(255,255,255,0.1) 100%)`,
        padding: '20px',
        borderRadius: '16px',
        color: '#fff',
        cursor: 'pointer',
        boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        backdropFilter: 'blur(4px)',
        border: '1px solid rgba(255, 255, 255, 0.18)',
        marginBottom: '15px'
      }}
    >
      <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{title}</h3>
      <p style={{ margin: '5px 0 0 0', opacity: 0.8, fontSize: '0.9rem' }}>
        {type === 'energy' ? 'Proteins & Energy' : type === 'detox' ? 'Fiber & Detox' : 'Antioxidants & Balance'}
      </p>
    </motion.div>
  );
};
