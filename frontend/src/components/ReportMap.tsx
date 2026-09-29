import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

import { fetchReports } from '../api'
import { MAP_STYLE, SKOPJE, type LngLat } from '../geo'

interface Props {
  refreshKey: number // bump this to reload the reports, e.g. after a new upload
  onCenterChange: (center: LngLat) => void
}

// load the reports inside the visible area
async function loadReports(map: maplibregl.Map): Promise<void> {
  const bounds = map.getBounds()
  const bbox = [
    bounds.getWest(),
    bounds.getSouth(),
    bounds.getEast(),
    bounds.getNorth(),
  ].join(',')
  const reports = await fetchReports(bbox)
  const source = map.getSource('reports') as maplibregl.GeoJSONSource | undefined
  source?.setData(reports)
}

export default function ReportMap({ refreshKey, onCenterChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const onCenterChangeRef = useRef(onCenterChange)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    onCenterChangeRef.current = onCenterChange
  }, [onCenterChange])

  // create the map once
  useEffect(() => {
    if (!containerRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: SKOPJE,
      zoom: 13,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    mapRef.current = map

    function refresh() {
      loadReports(map)
        .then(() => setError(null))
        .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load reports'))
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
      refresh()
    })
    map.on('moveend', () => {
      const { lng, lat } = map.getCenter()
      onCenterChangeRef.current([lng, lat])
      refresh()
    })

    return () => {
      mapRef.current = null
      map.remove()
    }
  }, [])

  // reload when asked to, e.g. right after a new report is created
  useEffect(() => {
    const map = mapRef.current
    if (refreshKey === 0 || !map?.getSource('reports')) return
    loadReports(map)
      .then(() => setError(null))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load reports'))
  }, [refreshKey])

  return (
    <div className="map-wrapper">
      <div ref={containerRef} className="map" />
      {error && <div className="map-error">{error}</div>}
    </div>
  )
}
