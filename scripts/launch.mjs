#!/usr/bin/env node
// Interactive launcher for the AgentOS frontends. Useful from the IDE
// preview panel: invokes the right pnpm filter after asking the user
// which frontend to spin up.

import { spawn } from "node:child_process";
import readline from "node:readline";

const APPS = [
  { key: "1", label: "SvelteKit",  dir: "web-svelte", port: 5173, command: "dev:svelte" },
  { key: "2", label: "Next.js",    dir: "web-next",   port: 3000, command: "dev:next"   },
  { key: "3", label: "Nuxt 3",     dir: "web-vue",    port: 3001, command: "dev:vue"    },
  { key: "a", label: "Todos en paralelo (turbo)", command: "dev" },
];

function banner() {
  const lines = [
    "",
    "  AgentOS · launcher",
    "  ───────────────────",
    "",
  ];
  process.stdout.write(lines.join("\n"));
}

function menu() {
  for (const app of APPS) {
    const portTag = app.port ? `  http://localhost:${app.port}` : "";
    process.stdout.write(`  [${app.key}] ${app.label}${portTag}\n`);
  }
  process.stdout.write("  [q] Salir\n\n");
}

async function ask() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question("¿Cuál ejecutar? ", (answer) => {
      rl.close();
      resolve(answer.trim().toLowerCase());
    });
  });
}

function run(command) {
  const isWindows = process.platform === "win32";
  const child = spawn("pnpm", [command], {
    stdio: "inherit",
    shell: isWindows,
  });
  child.on("exit", (code) => process.exit(code ?? 0));
}

async function main() {
  banner();
  const fromArg = process.argv[2];
  const choice = fromArg ?? (menu(), await ask());

  if (choice === "q") {
    process.stdout.write("Bye.\n");
    return;
  }

  const app = APPS.find((a) => a.key === choice || a.label.toLowerCase().includes(choice));
  if (!app) {
    process.stderr.write(`Opción inválida: ${choice}\n`);
    process.exit(1);
  }
  process.stdout.write(`\n→ pnpm ${app.command}\n\n`);
  run(app.command);
}

main().catch((err) => {
  process.stderr.write(`launcher error: ${err}\n`);
  process.exit(1);
});
