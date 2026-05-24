import { Markup } from 'telegraf';
import { GeoService } from '../services/geoService';
import { t } from '../utils/i18n';
import { MyContext } from '../types/context';

export const handleFindChefs = async (ctx: MyContext) => {
  const lang = ctx.session?.language || 'en';
  const h3Index = ctx.session?.h3Index;

  if (!h3Index) {
    return ctx.reply(t('request_location_first', lang));
  }

  await ctx.reply(t('matching_chef', lang));

  // In a real scenario, this would query the DB for chefs in these H3 cells
  const nearbyIndexes = GeoService.getNearbyIndexes(h3Index);

  // Mock results
  const mockChefs = [
    { id: 'chef_1', name: 'Nonna Maria', specialty: 'Pasta' },
    { id: 'chef_2', name: 'Sushi Master', specialty: 'Sashimi' },
  ];

  if (mockChefs.length === 0) {
    return ctx.reply(t('no_chefs_found', lang));
  }

  for (const chef of mockChefs) {
    await ctx.reply(
      `👨‍🍳 ${chef.name}\n🍳 ${chef.specialty}`,
      Markup.inlineKeyboard([
        [Markup.button.callback(t('view_menu', lang), `view_chef_${chef.id}`)],
        [Markup.button.callback(t('order_now', lang), `order_${chef.id}`)]
      ])
    );
  }
};
