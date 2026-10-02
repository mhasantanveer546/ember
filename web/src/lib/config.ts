/** Base URL of the Ember FastAPI backend (set in web/.env.local). */
export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
