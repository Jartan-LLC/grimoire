// @ts-check
// Convert temperatures between units, by way of Celsius.

const TO_CELSIUS = {
  C: (v) => v,
  F: (v) => ((v - 32) * 5) / 9,
};

const FROM_CELSIUS = {
  C: (c) => c,
  F: (c) => (c * 9) / 5 + 32,
};

export function convert(value, from, to) {
  const toCelsius = Object.hasOwn(TO_CELSIUS, from) ? TO_CELSIUS[from] : null;
  if (!toCelsius) throw new Error(`unknown unit ${from}`);
  const fromCelsius = Object.hasOwn(FROM_CELSIUS, to) ? FROM_CELSIUS[to] : null;
  if (!fromCelsius) throw new Error(`unknown unit ${to}`);
  return fromCelsius(toCelsius(value));
}

export function formatTemp(value) {
  return value.toFixed(1);
}
