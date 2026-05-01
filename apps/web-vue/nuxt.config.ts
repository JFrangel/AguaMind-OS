export default defineNuxtConfig({
  modules: ["@pinia/nuxt"],
  css: ["~/assets/main.css"],
  vite: {
    plugins: [],
  },
  postcss: {
    plugins: {
      "@tailwindcss/postcss": {},
    },
  },
  runtimeConfig: {
    backendUrl: process.env.BACKEND_URL ?? "http://localhost:8000",
  },
  compatibilityDate: "2025-04-01",
  typescript: {
    strict: true,
  },
});
