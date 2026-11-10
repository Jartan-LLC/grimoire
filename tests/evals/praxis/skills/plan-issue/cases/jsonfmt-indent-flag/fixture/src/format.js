// The one JSON style: two-space indent, a trailing newline, keys sorted on request.
function sortKeys(value) {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((k) => [k, sortKeys(value[k])]));
  }
  return value;
}

function format(text, { sort = false } = {}) {
  const data = JSON.parse(text);
  return JSON.stringify(sort ? sortKeys(data) : data, null, 2) + "\n";
}

module.exports = { format, sortKeys };
