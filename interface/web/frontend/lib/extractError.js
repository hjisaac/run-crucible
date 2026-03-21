// Helper – pulls the most useful message out of an axios error.
// Usage: setError(extractError(e))
export function extractError(err) {
  return err?.response?.data?.detail ?? err?.response?.data ?? err.message;
}
