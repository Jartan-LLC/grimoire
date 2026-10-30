import { fetchJson } from "./http.js";

/**
 * The temperature now at a place, in degrees Celsius.
 * @param {number} latitude
 * @param {number} longitude
 */
export async function currentTemperature(latitude, longitude) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m`;
  const data = await fetchJson(url);
  return data.current.temperature_2m;
}
