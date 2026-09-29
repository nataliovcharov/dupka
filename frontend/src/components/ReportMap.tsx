import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

import { fetchReports } from '../api'

const SKOPJE: [number, number] = [21.4316, 41.9981] // [lon, lat]
const MAP_STYLE = 'https://tiles.openfreemap.org/styles/liberty'

export default function ReportMap() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: SKOPJE,
      zoom: 13,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-right')

    // load the reports inside the visible area
    async function loadReports() {
      const bounds = map.getBounds()
      const bbox = [
        bounds.getWest(),
        bounds.getSouth(),
        bounds.getEast(),
        bounds.getNorth(),
      ].join(',')
      try {
        const reports = await fetchReports(bbox)
        const source = map.getSource('reports') as maplibregl.GeoJSONSource | undefined
        source?.setData(reports)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reports')
      }
    }

    map.on('load', () => {
      map.addSource('reports', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: 'reports',
        type: 'circle',
        source: 'reports',
        paint: {
          'circle-radius': 8,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          // colour by severity; grey while the AI hasn't processed it yet
          'circle-color': [
            'match',
            ['get', 'severity'],
            'high', '#d62828',
            'medium', '#f77f00',
            'low', '#fcbf49',
            '#8d99ae',
          ],
        },
      })
      loadReports()
    })
    map.on('moveend', loadReports)

    return () => map.remove()
  }, [])

  return (
    <div className="map-wrapper">
      <div ref={containerRef} className="map" />
      {error && <div className="map-error">{error}</div>}
    </div>
  )
}
