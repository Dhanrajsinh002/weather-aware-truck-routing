import React, { createContext, useContext, useState, useMemo, useCallback } from 'react';
import { AnalyzeResponse, RouteOption, Checkpoint } from '../types/api';

export interface TripContextType {
  tripData: AnalyzeResponse | null;
  setTripData: (data: AnalyzeResponse | null) => void;
  selectedRouteId: string | null;
  setSelectedRouteId: (id: string) => void;
  selectedRoute: RouteOption | null;
  hoveredCheckpointIndex: number | null;
  setHoveredCheckpointIndex: (idx: number | null) => void;
  hoveredCheckpoint: Checkpoint | null;
  popupCheckpoint: Checkpoint | null;
  setPopupCheckpoint: (chk: Checkpoint | null) => void;
  sliderHour: number;
  setSliderHour: (hour: number | ((prev: number) => number)) => void;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean | ((prev: boolean) => boolean)) => void;
  showHeatmap: boolean;
  setShowHeatmap: (show: boolean | ((prev: boolean) => boolean)) => void;
  showCheckpoints: boolean;
  setShowCheckpoints: (show: boolean | ((prev: boolean) => boolean)) => void;
  resetTrip: () => void;
}

const TripContext = createContext<TripContextType | undefined>(undefined);

export const TripProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tripData, setTripDataState] = useState<AnalyzeResponse | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [hoveredCheckpointIndex, setHoveredCheckpointIndex] = useState<number | null>(null);
  const [popupCheckpoint, setPopupCheckpoint] = useState<Checkpoint | null>(null);
  const [sliderHour, setSliderHour] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [showHeatmap, setShowHeatmap] = useState<boolean>(true);
  const [showCheckpoints, setShowCheckpoints] = useState<boolean>(true);

  const setTripData = useCallback((data: AnalyzeResponse | null) => {
    setTripDataState(data);
    if (data && data.routes && data.routes.length > 0) {
      // Pick recommended route by default or first route
      const rec = data.routes.find((r) => r.recommended) || data.routes[0];
      setSelectedRouteId(rec.id);
    } else {
      setSelectedRouteId(null);
    }
    setHoveredCheckpointIndex(null);
    setPopupCheckpoint(null);
    setSliderHour(0);
    setIsPlaying(false);
  }, []);

  const resetTrip = useCallback(() => {
    setTripDataState(null);
    setSelectedRouteId(null);
    setHoveredCheckpointIndex(null);
    setPopupCheckpoint(null);
    setSliderHour(0);
    setIsPlaying(false);
  }, []);

  const selectedRoute = useMemo(() => {
    if (!tripData || !selectedRouteId) return null;
    return tripData.routes.find((r) => r.id === selectedRouteId) || tripData.routes[0] || null;
  }, [tripData, selectedRouteId]);

  const hoveredCheckpoint = useMemo(() => {
    if (!selectedRoute || hoveredCheckpointIndex === null) return null;
    return selectedRoute.checkpoints.find((c) => c.index === hoveredCheckpointIndex) || null;
  }, [selectedRoute, hoveredCheckpointIndex]);

  const value = useMemo(
    () => ({
      tripData,
      setTripData,
      selectedRouteId,
      setSelectedRouteId,
      selectedRoute,
      hoveredCheckpointIndex,
      setHoveredCheckpointIndex,
      hoveredCheckpoint,
      popupCheckpoint,
      setPopupCheckpoint,
      sliderHour,
      setSliderHour,
      isPlaying,
      setIsPlaying,
      showHeatmap,
      setShowHeatmap,
      showCheckpoints,
      setShowCheckpoints,
      resetTrip,
    }),
    [
      tripData,
      setTripData,
      selectedRouteId,
      selectedRoute,
      hoveredCheckpointIndex,
      hoveredCheckpoint,
      popupCheckpoint,
      sliderHour,
      isPlaying,
      showHeatmap,
      showCheckpoints,
      resetTrip,
    ]
  );

  return <TripContext.Provider value={value}>{children}</TripContext.Provider>;
};

export function useTripContext(): TripContextType {
  const context = useContext(TripContext);
  if (!context) {
    throw new Error('useTripContext must be used within a TripProvider');
  }
  return context;
}
