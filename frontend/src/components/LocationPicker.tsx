import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'

import { MAP_STYLE, type LngLat } from '../geo'

interface Props {
  value: LngLat
  onChange: (value: LngLat) => void
}

// small map with a pin the user can drag, or move by tapping the map
export default function LocationPicker({ value, onChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markerRef = useRef<maplibregl.Marker | null>(null)
  const initialValue = useRef(value)
  const onChangeRef = useRef(onChange)

  useEffect(() => {
    onChangeRef.current = onChange
  }, [onChange])

  // create the map and pin once
  useEffect(() => {
    if (!containerRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: initialValue.current,
      zoom: 17,
    })
    const marker = new maplibregl.Marker({ draggable: true, color: '#d62828' })
      .setLngLat(initialValue.current)
      .addTo(map)

    marker.on('dragend', () => {
      const { lng, lat } = marker.getLngLat()
      onChangeRef.current([lng, lat])
    })
    map.on('click', (event) => {
      marker.setLngLat(event.lngLat)
      onChangeRef.current([event.lngLat.lng, event.lngLat.lat])
    })

    mapRef.current = map
    markerRef.current = marker
    return () => {
      mapRef.current = null
      markerRef.current = null
      map.remove()
    }
  }, [])

  // follow the value when it changes from outside, e.g. when GPS arrives
  useEffect(() => {
    markerRef.current?.setLngLat(value)
    mapRef.current?.easeTo({ center: value })
  }, [value])

  return <div ref={containerRef} className="location-picker" />
}
