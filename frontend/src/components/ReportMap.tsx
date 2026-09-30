import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

import { fetchIssues } from '../api'
import { MAP_STYLE, SKOPJE, type LngLat } from '../geo'
import type { IssueCollection, Report, ReportCollection, Severity } from '../types'

const SEVERITIES: { value: Severity; label: string; color: string }[] = [
  { value: 'high', label: 'High', color: '#d62828' },
  { value: 'medium', label: 'Medium', color: '#f77f00' },
  { value: 'low', label: 'Low', color: '#fcbf49' },
]

const EMPTY: IssueCollection = { type: 'FeatureCollection', features: [] }

interface Props {
  refreshKey: number // bump this to reload the reports, e.g. after a new upload
  onCenterChange: (center: LngLat) => void
  myReports: Report[] // sent from this browser, shown before they are approved
  onSelect: (issueId: string) => void // a dot was tapped
}

function toGeoJSON(reports: Report[]): ReportCollection {
  return {
    type: 'FeatureCollection',
    features: reports.map((report) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [report.longitude, report.latitude] },
      properties: {
        id: report.id,
        status: report.status,
        damage_type: report.damage_type,
        severity: report.severity,
        created_at: report.created_at,
      },
    })),
  }
}

// load the issues inside the visible area
async function loadIssues(map: maplibregl.Map): Promise<IssueCollection> {
  const bounds = map.getBounds()
  const bbox = [
    bounds.getWest(),
    bounds.getSouth(),
    bounds.getEast(),
    bounds.getNorth(),
  ].join(',')
  return fetchIssues(bbox)
}

// filtered here and not with a layer filter, so clusters only count what's shown
function showIssues(map: maplibregl.Map, issues: IssueCollection, severities: Severity[]) {
  const source = map.getSource('reports') as maplibregl.GeoJSONSource | undefined
  source?.setData({
    ...issues,
    // issues without a severity are always shown
    features: issues.features.filter(
      (f) => !f.properties.severity || severities.includes(f.properties.severity),
    ),
  })
}

export default function ReportMap({ refreshKey, onCenterChange, myReports, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const onCenterChangeRef = useRef(onCenterChange)
  const onSelectRef = useRef(onSelect)
  const myReportsRef = useRef(myReports)
  const issuesRef = useRef<IssueCollection>(EMPTY) // last loaded, before filtering
  const [severities, setSeverities] = useState<Severity[]>(['high', 'medium', 'low'])
  const severitiesRef = useRef(severities)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    onCenterChangeRef.current = onCenterChange
    onSelectRef.current = onSelect
  }, [onCenterChange, onSelect])

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
      loadIssues(map)
        .then((issues) => {
          issuesRef.current = issues
          showIssues(map, issues, severitiesRef.current)
          setError(null)
        })
        .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load reports'))
    }

    map.on('load', () => {
      map.addSource('reports', {
        type: 'geojson',
        data: EMPTY,
        cluster: true,
        clusterMaxZoom: 15, // closer than this, every report is its own dot
        clusterRadius: 50,
        // count severities in each cluster, so it can take the worst one's colour
        clusterProperties: {
          high: ['+', ['case', ['==', ['get', 'severity'], 'high'], 1, 0]],
          medium: ['+', ['case', ['==', ['get', 'severity'], 'medium'], 1, 0]],
        },
      })
      map.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'reports',
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': [
            'case',
            ['>', ['get', 'high'], 0], '#d62828',
            ['>', ['get', 'medium'], 0], '#f77f00',
            '#fcbf49',
          ],
          'circle-radius': ['step', ['get', 'point_count'], 15, 10, 19, 50, 24],
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ffffff',
        },
      })
      map.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: 'reports',
        filter: ['has', 'point_count'],
        layout: {
          'text-field': ['get', 'point_count_abbreviated'],
          'text-font': ['Noto Sans Bold'],
          'text-size': 13,
        },
        paint: { 'text-color': '#ffffff' },
      })
      map.addLayer({
        id: 'reports',
        type: 'circle',
        source: 'reports',
        filter: ['!', ['has', 'point_count']],
        paint: {
          // bigger dots for worse damage
          'circle-radius': ['match', ['get', 'severity'], 'high', 9, 'medium', 7.5, 'low', 6, 7],
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
      // invisible, bigger circles so dots are easy to tap on a phone
      map.addLayer({
        id: 'reports-hit',
        type: 'circle',
        source: 'reports',
        filter: ['!', ['has', 'point_count']],
        paint: { 'circle-radius': 22, 'circle-opacity': 0 },
      })
      // how many reports an issue has, next to dots with more than one
      map.addLayer({
        id: 'issue-count',
        type: 'symbol',
        source: 'reports',
        filter: ['all', ['!', ['has', 'point_count']], ['>', ['get', 'report_count'], 1]],
        layout: {
          'text-field': ['to-string', ['get', 'report_count']],
          'text-font': ['Noto Sans Bold'],
          'text-size': 11,
          'text-offset': [1.1, -1.1],
          'text-allow-overlap': true,
        },
        paint: { 'text-color': '#111111', 'text-halo-color': '#ffffff', 'text-halo-width': 2 },
      })
      map.on('click', 'reports-hit', (event) => {
        const id = event.features?.[0]?.properties?.id
        if (id) onSelectRef.current(id)
      })
      // tapping a cluster zooms in until it splits
      map.on('click', 'clusters', (event) => {
        const feature = event.features?.[0]
        if (!feature || feature.geometry.type !== 'Point') return
        const [lng, lat] = feature.geometry.coordinates
        const source = map.getSource('reports') as maplibregl.GeoJSONSource
        source
          .getClusterExpansionZoom(feature.properties.cluster_id)
          .then((zoom) => map.easeTo({ center: [lng, lat], zoom }))
          .catch(() => map.easeTo({ center: [lng, lat], zoom: map.getZoom() + 2 }))
      })
      for (const layer of ['reports-hit', 'clusters']) {
        map.on('mouseenter', layer, () => {
          map.getCanvas().style.cursor = 'pointer'
        })
        map.on('mouseleave', layer, () => {
          map.getCanvas().style.cursor = ''
        })
      }
      // your own reports: hollow red rings until they are approved
      map.addSource('my-reports', { type: 'geojson', data: toGeoJSON(myReportsRef.current) })
      map.addLayer({
        id: 'my-reports',
        type: 'circle',
        source: 'my-reports',
        paint: {
          'circle-radius': 8,
          'circle-color': '#ffffff',
          'circle-stroke-width': 3,
          'circle-stroke-color': '#e0201b',
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

  // show new reports from this browser right away
  useEffect(() => {
    myReportsRef.current = myReports
    const source = mapRef.current?.getSource('my-reports') as maplibregl.GeoJSONSource | undefined
    source?.setData(toGeoJSON(myReports))
  }, [myReports])

  // reload when asked to, e.g. right after a new report is created
  useEffect(() => {
    const map = mapRef.current
    if (refreshKey === 0 || !map?.getSource('reports')) return
    loadIssues(map)
      .then((issues) => {
        issuesRef.current = issues
        showIssues(map, issues, severitiesRef.current)
        setError(null)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load reports'))
  }, [refreshKey])

  // redraw with the chosen severities, no new request needed
  useEffect(() => {
    severitiesRef.current = severities
    const map = mapRef.current
    if (map?.getSource('reports')) showIssues(map, issuesRef.current, severities)
  }, [severities])

  function toggle(severity: Severity) {
    setSeverities((current) =>
      current.includes(severity)
        ? current.filter((s) => s !== severity)
        : [...current, severity],
    )
  }

  return (
    <div className="map-wrapper">
      <div ref={containerRef} className="map" />
      <div className="map-filters" role="group" aria-label="Show severity">
        {SEVERITIES.map((s) => (
          <button
            key={s.value}
            className="filter-chip"
            aria-pressed={severities.includes(s.value)}
            onClick={() => toggle(s.value)}
          >
            <span className="filter-dot" style={{ background: s.color }} />
            {s.label}
          </button>
        ))}
      </div>
      {error && <div className="map-error">{error}</div>}
    </div>
  )
}
