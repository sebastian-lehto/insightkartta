import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const fetchDatasets = () => API.get("/datasets");

export const fetchDataset = (datasetName) => API.get(`/${datasetName}`);