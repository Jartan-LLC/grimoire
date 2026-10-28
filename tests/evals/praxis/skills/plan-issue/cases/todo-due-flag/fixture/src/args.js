// Hand-rolled argument parsing, written before node:util's parseArgs was stable.
// Each flag is one more branch in the loop below.
function parseArgs(argv) {
  const args = { command: argv[0], positional: [], tag: null, all: false };
  for (let i = 1; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--tag") {
      args.tag = argv[i + 1];
      i++;
    } else if (arg.startsWith("--tag=")) {
      args.tag = arg.slice("--tag=".length);
    } else if (arg === "--all" || arg === "-a") {
      args.all = true;
    } else {
      args.positional.push(arg);
    }
  }
  return args;
}

module.exports = { parseArgs };
