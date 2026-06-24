import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000",
});

export const fetchDatasets = () => API.get("/datasets");

export const fetchDataset = (datasetName) => API.get(`/${datasetName}`);

export const fetchRegionInsights = (region) => API.get(`/regions/${region}/insights`);

export const fetchElectionCorrelations = () => API.get("/elections/correlations");