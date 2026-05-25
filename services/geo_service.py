# Lightweight GeoService to avoid 'h3' library build issues on Render
# This implementation uses a simple grid approximation instead of the full H3 library
class GeoService:
    RESOLUTION = 9

    @staticmethod
    def get_h3_index(lat: float, lng: float) -> str:
        """
        Provides a mock H3 index string to avoid external C-extension dependencies.
        In production, this should be replaced by a proper H3 binding if the environment allows.
        """
        # Simple string representation for matching
        return f"grid_{int(lat * 1000)}_{int(lng * 1000)}"

    @staticmethod
    def get_nearby_indexes(h3_index: str, radius_rings: int = 12) -> list:
        """
        Mock nearby index discovery.
        """
        return [h3_index]

    @staticmethod
    async def find_nearby_chefs(h3_index: str):
        """
        Mock chef discovery logic.
        """
        return [h3_index]
