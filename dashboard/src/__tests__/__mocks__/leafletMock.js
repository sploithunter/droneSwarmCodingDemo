// Shared Leaflet mock for jsdom tests
const markerInstance = {
  setLatLng: function() { return this; },
  setIcon: function() { return this; },
  addTo: function() { return this; },
  bindPopup: function() { return this; },
  on: function() { return this; },
};

const leafletMock = {
  default: {
    map: () => ({
      setView: function() { return this; },
      remove: () => {},
      removeLayer: () => {},
    }),
    tileLayer: () => ({ addTo: () => {} }),
    marker: () => ({ ...markerInstance }),
    divIcon: () => ({}),
    polygon: () => ({ addTo: () => ({}) }),
    polyline: () => ({ addTo: function() { return this; }, setLatLngs: () => {} }),
  },
};

export default leafletMock;
