import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// Dirección del backend. Se puede cambiar con la variable API_TARGET.
// Se usa 127.0.0.1 (no "localhost") para evitar el conflicto IPv4/IPv6.
const API_TARGET = process.env.API_TARGET || "http://127.0.0.1:8000";

const proxy = {
  "/api": { target: API_TARGET, changeOrigin: true },
};

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true, // escucha en todas las interfaces (localhost, 127.0.0.1 y la red local)
    proxy,
  },
  preview: {
    host: true,
    proxy,
  },
});
