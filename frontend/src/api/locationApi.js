import api from './client';

export const locationApi = {
  /**
   * Get autocomplete predictions for a location query.
   * @param {string} query 
   * @param {string} sessionToken 
   * @returns {Promise<Array>}
   */
  autocomplete: async (query, sessionToken = null) => {
    if (!query || query.length < 2) return [];
    const params = new URLSearchParams({ query });
    if (sessionToken) params.append('session_token', sessionToken);
    
    const res = await api.get(`/v1/locations/autocomplete?${params.toString()}`);
    return res.data;
  },

  /**
   * Get precise details for a selected place.
   * @param {string} placeId 
   * @param {string} sessionToken 
   * @returns {Promise<Object>}
   */
  getPlaceDetails: async (placeId, sessionToken = null) => {
    const params = new URLSearchParams({ place_id: placeId });
    if (sessionToken) params.append('session_token', sessionToken);
    
    const res = await api.get(`/v1/locations/details?${params.toString()}`);
    return res.data;
  },

  /**
   * Calculate route distance, duration, and toll estimate between two coordinates.
   * @param {Object} payload { origin_lat, origin_lng, destination_lat, destination_lng }
   * @returns {Promise<Object>}
   */
  calculateRoute: async (payload) => {
    const res = await api.post('/v1/routes/calculate', payload);
    return res.data;
  },

  /**
   * Utility to decode a Google Maps polyline string into an array of [lat, lng]
   * for Leaflet rendering.
   * @param {string} encoded 
   * @returns {Array<[number, number]>}
   */
  decodePolyline: (encoded) => {
    if (!encoded) return [];
    let points = [];
    let index = 0, len = encoded.length;
    let lat = 0, lng = 0;

    while (index < len) {
      let b, shift = 0, result = 0;
      do {
        b = encoded.charCodeAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);
      let dlat = ((result & 1) ? ~(result >> 1) : (result >> 1));
      lat += dlat;

      shift = 0;
      result = 0;
      do {
        b = encoded.charCodeAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);
      let dlng = ((result & 1) ? ~(result >> 1) : (result >> 1));
      lng += dlng;

      points.push([lat / 1E5, lng / 1E5]);
    }
    return points;
  }
};
