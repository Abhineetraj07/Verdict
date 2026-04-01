import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "./client";
import type { EvalSuiteCreate, DatasetCreate } from "./types";

export function useSuites() {
  return useQuery({ queryKey: ["suites"], queryFn: api.getSuites });
}

export function useSuite(id: string) {
  return useQuery({ queryKey: ["suites", id], queryFn: () => api.getSuite(id) });
}

export function useCreateSuite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: EvalSuiteCreate) => api.createSuite(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suites"] }),
  });
}

export function useDatasets() {
  return useQuery({ queryKey: ["datasets"], queryFn: api.getDatasets });
}

export function useDataset(id: string) {
  return useQuery({
    queryKey: ["datasets", id],
    queryFn: () => api.getDataset(id),
  });
}

export function useCreateDataset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: DatasetCreate) => api.createDataset(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["datasets"] }),
  });
}

export function useRuns() {
  return useQuery({ queryKey: ["runs"], queryFn: api.getRuns });
}

export function useRun(id: string) {
  return useQuery({
    queryKey: ["runs", id],
    queryFn: () => api.getRun(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 3000 : false;
    },
  });
}

export function useStartRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ suiteId, datasetId }: { suiteId: string; datasetId: string }) =>
      api.startRun(suiteId, datasetId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runs"] }),
  });
}

export function useCompare(runIds: string[]) {
  return useQuery({
    queryKey: ["compare", runIds],
    queryFn: () => api.compareRuns(runIds),
    enabled: runIds.length >= 2,
  });
}
