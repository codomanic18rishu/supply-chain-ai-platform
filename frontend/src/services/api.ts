import axios from "axios";
console.log("API BASE URL:", import.meta.env.VITE_API_BASE_URL);
const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ||
    "https://supply-chain-ai-platform.onrender.com/api",
});

export default api;
