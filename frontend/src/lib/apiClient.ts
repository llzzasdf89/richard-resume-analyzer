import axios from "axios";
import { supabase } from "./supabase";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
});

apiClient.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use((response) => {
  const body = response.data;
  if (body && body.success === false) {
    throw new Error(body.message || "Request failed");
  }
  if (body && typeof body.code === "number" && body.code !== 200) {
    throw new Error(body.message || "Request failed");
  }
  return response;
});
