// @ts-check
// Convert temperatures between units, by way of Celsius.

const TO_CELSIUS = {
  C: (v) => v,
  F: (v) => ((v - 32) * 5) / 9,
  K: (v) => v - 273.15,
};

const FROM_CELSIUS = {
  C: (c) => c,
  F: (c) => (c * 9) / 5 + 32,
  K: (c) => c + 273.15,
};

export function convert(value, from, to) {
  const toCelsius = Object.hasOwn(TO_CELSIUS, from) ? TO_CELSIUS[from] : null;
  if (!toCelsius) throw new Error(`unknown unit ${from}`);
  const fromCelsius = Object.hasOwn(FROM_CELSIUS, to) ? FROM_CELSIUS[to] : null;
  if (!fromCelsius) throw new Error(`unknown unit ${to}`);
  const celsius = toCelsius(value);
  if (celsius < -273.15) throw new Error(`${value} ${from} is below absolute zero`);
  return fromCelsius(celsius);
}

export function formatTemp(value) {
  return value.toFixed(1);
}
