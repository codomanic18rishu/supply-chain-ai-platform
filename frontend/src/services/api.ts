import axios from "axios";
console.log("API BASE URL ->:", import.meta.env.VITE_API_BASE_URL);
const api = axios.create({
  // baseURL: "http://127.0.0.1:8000/",
  baseURL: "https://supply-chain-ai-platform.onrender.com/",
});

export default api;
