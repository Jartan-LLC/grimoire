const DEFAULT_PORT = 3000;

function port(env) {
  return Number(env.PORT) || DEFAULT_PORT;
}

module.exports = { DEFAULT_PORT, port };
