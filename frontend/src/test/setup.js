import '@testing-library/jest-dom/vitest'
import React from 'react'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Without `test.globals: true` in vite.config.js, Testing Library's
// auto-cleanup can't detect a global afterEach and never unmounts between
// tests — every test after the first in a file would render on top of the
// previous one's leftover DOM (e.g. two "Search for a region" inputs at
// once). Explicit cleanup here applies to every test file.
afterEach(() => {
  cleanup()
})

// This project's JSX is normally transformed via the automatic runtime
// (no React import needed), but under Vitest's transform pipeline — a
// different path than the app's actual Vite dev/build pipeline, which
// also runs through @rolldown/plugin-babel's React Compiler preset — JSX
// in test files ends up compiled to classic `React.createElement(...)`
// calls instead, which throws "React is not defined" even when the test
// file itself imports React (something downstream still drops it).
// Making React available as a true global sidesteps the mismatch without
// touching the app's production Vite config.
globalThis.React = React
