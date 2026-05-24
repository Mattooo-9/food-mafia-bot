import { Markup } from 'telegraf';
import { t } from '../utils/i18n';
import { MyContext } from '../types/context';

export const handleRateChef = async (ctx: MyContext) => {
  const lang = ctx.session?.language || 'en';

  await ctx.reply(
    t('rate_chef_prompt', lang),
    Markup.inlineKeyboard([
      [1, 2, 3, 4, 5].map(rating =>
        Markup.button.callback('⭐'.repeat(rating), `rate_${rating}`)
      )
    ])
  );
};

export const handleRatingSubmission = async (ctx: MyContext) => {
  const lang = ctx.session?.language || 'en';
  const callbackData = (ctx.callbackQuery as any).data;
  const rating = callbackData.split('_')[1];

  // Logic to save rating to DB and trigger smart contract if necessary
  // await prisma.review.create({ ... });

  await ctx.answerCbQuery();
  await ctx.reply(t('rating_submitted', lang, { rating }));
};
