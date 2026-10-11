import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRef } from 'react';
import { searchGeocode, analyzeTrip } from './client';
import { AnalyzeRequest, AnalyzeResponse, GeocodeResponse } from '../types/api';

export function useGeocode(query: string) {
  return useQuery<GeocodeResponse, Error>({
    queryKey: ['geocode', query],
    queryFn: ({ signal }) => searchGeocode(query, signal),
    enabled: query.trim().length >= 2,
    staleTime: 1000 * 60 * 15, // 15 mins cache
    gcTime: 1000 * 60 * 30,
    retry: 1,
  });
}

export function useAnalyzeTrip() {
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  return useMutation<AnalyzeResponse, Error, AnalyzeRequest>({
    mutationFn: async (request: AnalyzeRequest) => {
      // Cancel previous in-flight request if user submits again
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const result = await analyzeTrip(request, controller.signal);
        return result;
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    },
    onSuccess: (data) => {
      // Store in query cache as current trip
      queryClient.setQueryData(['currentTrip'], data);
    },
  });
}
