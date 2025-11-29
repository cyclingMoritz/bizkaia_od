//-----------------------------------------------------
// CONFIG
//-----------------------------------------------------
const SIRI_URL =
  "https://ctb-siri.s3.eu-south-2.amazonaws.com/bizkaibus-vehicle-positions.xml";

const REFRESH_MS = 15000;

let map = L.map("map").setView([40.75, -73.97], 12);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19
}).addTo(map);

let vehicleLayer = L.layerGroup().addTo(map);

//-----------------------------------------------------
// Fetch SIRI feed and update map
//-----------------------------------------------------
async function fetchSIRI() {
  try {
    const res = await fetch(SIRI_URL);
    const data = await res.json();

    const vehicles =
      data.Siri.ServiceDelivery.VehicleMonitoringDelivery[0]
        .VehicleActivity || [];

    vehicleLayer.clearLayers();

    vehicles.forEach((v) => {
      const mv = v.MonitoredVehicleJourney;
      if (!mv || !mv.VehicleLocation) return;

      const lat = mv.VehicleLocation.Latitude;
      const lon = mv.VehicleLocation.Longitude;
      const line = mv.LineRef || "Unknown route";
      const dest = mv.DestinationName || "Unknown destination";

      L.marker([lat, lon])
        .bindPopup(`<strong>${line}</strong><br>→ ${dest}`)
        .addTo(vehicleLayer);
    });

    console.log(`Updated at ${new Date().toLocaleTimeString()}`);
  } catch (err) {
    console.error("SIRI error:", err);
  }
}

fetchSIRI();
setInterval(fetchSIRI, REFRESH_MS);
