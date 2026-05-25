import h3

class GeoService:
    RESOLUTION = 9

    @staticmethod
    def get_h3_index(lat: float, lng: float) -> str:
        return h3.latlng_to_cell(lat, lng, GeoService.RESOLUTION)

    @staticmethod
    def get_nearby_indexes(h3_index: str, radius_rings: int = 12) -> list:
        return list(h3.grid_disk(h3_index, radius_rings))

    @staticmethod
    async def find_nearby_chefs(h3_index: str):
        # This would normally query the database
        return GeoService.get_nearby_indexes(h3_index)
