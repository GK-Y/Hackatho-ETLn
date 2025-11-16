// src/utils/date.js
export function formatTs(ts) {
  try {
    return new Date(ts).toLocaleString();
  } catch (e) {
    return ts;
  }
}
