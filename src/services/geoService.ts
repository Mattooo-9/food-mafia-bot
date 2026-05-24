import { gridDisk, latLngToCell } from 'h3-js';

export class GeoService {
  private static RESOLUTION = 9;

  /**
   * Converts coordinates to H3 index
   */
  static getH3Index(lat: number, lng: number): string {
    return latLngToCell(lat, lng, this.RESOLUTION);
  }

  /**
   * Returns a list of H3 indexes within a given radius (in hex rings)
   * For resolution 9, each ring is roughly 170m.
   * A radius of 12 rings is ~2km.
   */
  static getNearbyIndexes(h3Index: string, radiusRings: number = 12): string[] {
    return gridDisk(h3Index, radiusRings);
  }

  /**
   * Mock matching logic
   */
  static async findNearbyChefs(h3Index: string): Promise<string[]> {
    const nearbyIndexes = this.getNearbyIndexes(h3Index);
    // In a real app: return prisma.chefProfile.findMany({ where: { user: { h3Index: { in: nearbyIndexes } } } })
    return nearbyIndexes;
  }
}
