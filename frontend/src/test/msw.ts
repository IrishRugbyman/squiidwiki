import { setupServer } from 'msw/node'

// No default handlers on purpose. `onUnhandledRequest: 'error'` plus an empty
// base set means every test states the responses it depends on, in the test,
// where the assertion can be read against them. A shared fixture drifts and
// then quietly decides what a dozen suites are asserting.
export const server = setupServer()

export { http, HttpResponse } from 'msw'
