# Food Mafia Bot - Global P2P Food Marketplace

A decentralized, anonymous, hyper-local food marketplace built for Telegram.

## Features

- **Hyper-Local Discovery**: Uses Uber H3 hex-grids (Resolution 9) for matching Buyers and Chefs within 100m - 2km.
- **Strict Anonymity**:
  - End-to-end encrypted order details.
  - Temporary E2EE video stream webhooks for kitchen transparency.
  - Secret-based delivery confirmation via Web3 escrow.
- **Web3 Escrow & Economy**:
  - 1% platform fee logic built into the `FoodEscrow` Solidity contract.
  - Support for Jettons (TON) or EVM-based tokens.
- **Multilingual Support**: Full i18n support for English and Russian.
- **Sanitary Verification**: Automated checklist for chefs to ensure safety.
- **Decentralized Ratings**: Transparent rating system recorded on-chain.

## Tech Stack

- **Backend**: Node.js, TypeScript, Telegraf (Telegram Bot API)
- **Database**: PostgreSQL with Prisma ORM
- **Geo-indexing**: Uber H3
- **Smart Contracts**: Solidity (EVM)
- **Localization**: i18next

## Setup

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Environment Variables**:
   Create a `.env` file based on `.env.example`:
   ```
   BOT_TOKEN=your_telegram_bot_token
   DATABASE_URL=postgresql://user:password@localhost:5432/foodmafia
   ```

3. **Database Setup**:
   ```bash
   npx prisma generate
   npx prisma migrate dev
   ```

4. **Run the Bot**:
   ```bash
   npm start
   ```

## Architecture

- `src/handlers/`: Contains the business logic for various bot interactions (registration, geo, matching, reviews, webhooks).
- `src/contracts/`: Solidity smart contracts for the escrow system.
- `src/services/`: Utility services like `GeoService` for H3 operations.
- `src/utils/`: General utilities, including i18n configuration.
- `locales/`: Localization files for Russian and English.

## Smart Contract

The `FoodEscrow.sol` contract implements:
- `createOrder`: Buyers lock funds and provide a hash of a secret.
- `completeOrder`: Funds are released to the chef (99%) and owner (1%) upon providing the correct secret.
- `disputeOrder`: Marks an order as disputed for administrative intervention.
