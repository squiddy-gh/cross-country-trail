/* Shared CCT map configuration and data endpoints. */
window.CCTMapConfig = {
  dataBase: 'https://raw.githubusercontent.com/squiddy-gh/cross-county-trail/main/data/',
  urls: {
    gpx: 'trail/GC_CCT.gpx',
    pois: 'curated_pois_enriched.csv',
    transit: 'transit.csv',
    amenities: 'osm_amenities.csv'
  },
  services: {
    wmataTripPlanner: 'https://www.wmata.com/schedules/trip-planner/',
    fairfaxConnector: 'https://www.fairfaxcounty.gov/connector/',
    vre: 'https://www.vre.org/'
  }
};
