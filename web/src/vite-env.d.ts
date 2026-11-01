/// <reference types="vite/client" />

/** Build-time switches. `VITE_STATIC=1` serves the DTO from a baked file
 *  instead of the Python API; see src/api.ts. Declared so `strict` type
 *  checking covers them rather than widening them to `any`. */
interface ImportMetaEnv {
  readonly VITE_STATIC?: string;
  readonly BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
