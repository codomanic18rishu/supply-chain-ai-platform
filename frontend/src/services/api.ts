import axios from "axios";

const api = axios.create({
  baseURL: "https://supply-chain-ai-platform.onrender.com",
});

export default api;