import { Markup } from 'telegraf';
import { t } from '../utils/i18n';
import { MyContext } from '../types/context';

export const handleStart = async (ctx: MyContext) => {
  const lang = ctx.session?.language || 'en';
  await ctx.reply(
    t('welcome', lang),
    Markup.inlineKeyboard([
      [Markup.button.webApp(t('open_marketplace', lang), process.env.WEBAPP_URL || 'https://foodmafia.bot/app')],
      [Markup.button.callback(t('buyer', lang), 'role_buyer')],
      [Markup.button.callback(t('seller', lang), 'role_chef')],
      [Markup.button.callback(t('settings', lang), 'settings')],
    ])
  );
};

export const handleRoleSelection = async (ctx: MyContext) => {
  const lang = ctx.session?.language || 'en';
  const callbackData = (ctx.callbackQuery as any).data;

  if (callbackData === 'role_buyer') {
    ctx.session.role = 'BUYER';
    await ctx.answerCbQuery();
    await ctx.reply(t('buyer_welcome', lang));
  } else if (callbackData === 'role_chef') {
    ctx.session.role = 'CHEF';
    await ctx.answerCbQuery();
    await ctx.reply(t('chef_onboarding', lang));
  }
};
