import { Telegraf, session } from 'telegraf';
import * as dotenv from 'dotenv';
import { initI18n } from './utils/i18n';
import { handleStart, handleRoleSelection } from './handlers/registration';
import { handleLocation } from './handlers/geo';
import { MyContext } from './types/context';
import { handleStreamRequest, handleSanitaryCheck } from './handlers/webhooks';

dotenv.config();

const bot = new Telegraf<MyContext>(process.env.BOT_TOKEN || '');

// Middleware for session management
bot.use(session());

// Initialize i18n
initI18n().then(() => {
  console.log('I18n initialized');
});

// Command handlers
bot.start(handleStart);
bot.command('stream', handleStreamRequest);
bot.command('check', handleSanitaryCheck);

// Action handlers
bot.action(/role_(buyer|chef)/, handleRoleSelection);

// Location handlers
bot.on('location', handleLocation);

// Global error handler
bot.catch((err: any, ctx) => {
  console.error(`Error for ${ctx.updateType}`, err);
});

if (process.env.NODE_ENV !== 'test') {
  bot.launch().then(() => {
    console.log('Food Mafia Bot is running...');
  });
}

export default bot;
