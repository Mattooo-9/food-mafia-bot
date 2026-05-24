import { latLngToCell } from 'h3-js';
import { t } from '../utils/i18n';
import { MyContext } from '../types/context';

export const handleLocation = async (ctx: MyContext) => {
  const lang = ctx.session?.language || 'en';
  const location = (ctx.message as any).location;

  if (!location) return;

  // Use H3 resolution 9 for ~100m - 200m accuracy
  const h3Index = latLngToCell(location.latitude, location.longitude, 9);

  ctx.session.h3Index = h3Index;

  // Update database with new location (mocked here, would use Prisma)
  // await prisma.user.update({ where: { telegramId: ctx.from.id }, data: { h3Index } });

  await ctx.reply(t('location_updated', lang, { h3Index }));
};
