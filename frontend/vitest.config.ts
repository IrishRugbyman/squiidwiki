import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vitest/config'

// Deliberately separate from vite.config.ts. The app config loads the TanStack
// Router plugin, which regenerates routeTree.gen.ts, and Tailwind, which
// compiles the stylesheet. Tests need neither, and both cost seconds on every
// watch-mode re-run.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // maplibre-gl, reactflow and terra-draw want WebGL and a real canvas, which
    // jsdom does not have. Testing them here buys flaky tests that prove nothing;
    // they are mocked at the module boundary instead (see src/test/setup.ts) and
    // the components that drive them are what gets tested.
    exclude: ['node_modules/**', 'dist/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/test/**',
        'src/routeTree.gen.ts',
        'src/**/*.test.{ts,tsx}',
        'src/components/ui/**',
      ],
    },
  },
})
