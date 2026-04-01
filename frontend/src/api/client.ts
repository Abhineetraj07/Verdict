import axios from "axios";
import type {
  EvalSuiteCreate,
  EvalSuiteResponse,
  DatasetCreate,
  DatasetResponse,
  EvalRunResponse,
  EvalRunSummary,
  CompareResponse,
} from "./types";

const api = axios.create({ baseURL: "/api" });

// Suites
export const getSuites = () =>
  api.get<EvalSuiteResponse[]>("/suites").then((r) => r.data);

export const getSuite = (id: string) =>
  api.get<EvalSuiteResponse>(`/suites/${id}`).then((r) => r.data);

export const createSuite = (data: EvalSuiteCreate) =>
  api.post<EvalSuiteResponse>("/suites", data).then((r) => r.data);

// Datasets
export const getDatasets = () =>
  api.get<DatasetResponse[]>("/datasets").then((r) => r.data);

export const getDataset = (id: string) =>
  api.get<DatasetResponse>(`/datasets/${id}`).then((r) => r.data);

export const createDataset = (data: DatasetCreate) =>
  api.post<DatasetResponse>("/datasets", data).then((r) => r.data);

// Evaluations
export const getRuns = () =>
  api.get<EvalRunSummary[]>("/evaluations").then((r) => r.data);

export const getRun = (id: string) =>
  api.get<EvalRunResponse>(`/evaluations/${id}`).then((r) => r.data);

export const startRun = (suiteId: string, datasetId: string) =>
  api
    .post<EvalRunSummary>("/evaluations/run", {
      suite_id: suiteId,
      dataset_id: datasetId,
    })
    .then((r) => r.data);

// Compare
export const compareRuns = (runIds: string[]) =>
  api
    .get<CompareResponse>("/compare", {
      params: { run_ids: runIds.join(",") },
    })
    .then((r) => r.data);
