import { t } from '../utils/i18n';
import { MyContext } from '../types/context';

/**
 * Handles the generation of temporary, E2EE video stream links.
 * In a production scenario, this would interface with a decentralized
 * streaming protocol or a temporary WebRTC signaling server.
 */
export const handleStreamRequest = async (ctx: MyContext) => {
  const lang = ctx.session?.language || 'en';
  const orderId = ctx.session?.activeOrderId;

  if (!orderId) {
    return ctx.reply(t('no_active_order', lang));
  }

  // Logic for creating a temporary webhook for video streaming
  const streamId = Math.random().toString(36).substring(7);
  const streamUrl = `https://stream.foodmafia.bot/v1/${streamId}`;

  await ctx.reply(t('stream_created', lang, { url: streamUrl }));
};

/**
 * Handles automated sanitary checklist verification.
 */
export const handleSanitaryCheck = async (ctx: MyContext) => {
  const lang = ctx.session?.language || 'en';

  const checklist = [
    t('checklist_gloves', lang),
    t('checklist_mask', lang),
    t('checklist_sanitized', lang),
  ];

  await ctx.reply(
    t('sanitary_verification', lang),
    {
      reply_markup: {
        inline_keyboard: checklist.map((item, index) => [
          { text: `✅ ${item}`, callback_data: `check_${index}` }
        ])
      }
    }
  );
};
