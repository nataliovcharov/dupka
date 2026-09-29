export type LngLat = [number, number] // [longitude, latitude], same order as GeoJSON

export const SKOPJE: LngLat = [21.4316, 41.9981]
export const MAP_STYLE = 'https://tiles.openfreemap.org/styles/liberty'

// same rough bounding box the API checks
const BOUNDS = { minLon: 20.45, maxLon: 23.04, minLat: 40.85, maxLat: 42.37 }

export function isInNorthMacedonia([lon, lat]: LngLat): boolean {
  return (
    lon >= BOUNDS.minLon &&
    lon <= BOUNDS.maxLon &&
    lat >= BOUNDS.minLat &&
    lat <= BOUNDS.maxLat
  )
}

export function getCurrentPosition(): Promise<LngLat> {
  return new Promise((resolve, reject) => {
    if (!('geolocation' in navigator)) {
      reject(new Error('Location is not available on this device'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve([position.coords.longitude, position.coords.latitude]),
      (error) => reject(new Error(error.message)),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 },
    )
  })
}
