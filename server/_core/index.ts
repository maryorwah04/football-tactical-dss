import express from "express";
import { createServer, request as httpRequest } from "http";
import net from "net";
import { spawn, spawnSync, ChildProcess } from "child_process";
import { createExpressMiddleware } from "@trpc/server/adapters/express";
import { registerOAuthRoutes } from "./oauth";
import { registerStorageProxy } from "./storageProxy";
import { appRouter } from "../routers";
import { createContext } from "./context";
import { serveStatic, setupVite } from "./vite";

function isPortAvailable(port: number): Promise<boolean> { return new Promise(resolve => { const server = net.createServer(); server.listen(port, () => server.close(() => resolve(true))); server.on("error", () => resolve(false)); }); }
async function findAvailablePort(startPort: number) { for (let port = startPort; port < startPort + 20; port++) if (await isPortAvailable(port)) return port; throw new Error(`No available port found starting from ${startPort}`); }

function proxyDjango(app: express.Express, child: ChildProcess) {
  app.use("/django-api", (req, res) => {
    const payload = JSON.stringify(req.body || {});
    const headers: Record<string, string | number> = { ...req.headers as Record<string, string>, host: "127.0.0.1:8001", "content-length": Buffer.byteLength(payload) };
    const upstream = httpRequest({ hostname: "127.0.0.1", port: 8001, path: `/api${req.path}`, method: req.method, headers }, response => {
      res.status(response.statusCode || 502);
      Object.entries(response.headers).forEach(([key, value]) => { if (value) res.setHeader(key, value as string | string[]); });
      response.pipe(res);
    });
    upstream.on("error", error => res.status(502).json({ error: `Django backend unavailable: ${error.message}` }));
    if (req.method === "GET" || req.method === "HEAD") upstream.end(); else upstream.end(payload);
  });
}

async function startServer() {
  const app = express(); const server = createServer(app);
  app.use(express.json({ limit: "5mb" })); app.use(express.urlencoded({ limit: "5mb", extended: true }));
  const migration = spawnSync("python3", ["backend/manage.py", "migrate", "--noinput"], { cwd: process.cwd(), env: { ...process.env, PYTHONPATH: "backend" }, stdio: "inherit" });
  if (migration.status !== 0) throw new Error("Django migrations failed");
  const django = spawn("python3", ["backend/manage.py", "runserver", "127.0.0.1:8001", "--noreload"], { cwd: process.cwd(), env: { ...process.env, PYTHONPATH: "backend" }, stdio: "inherit" });
  process.on("exit", () => django.kill());
  proxyDjango(app, django);
  registerStorageProxy(app); registerOAuthRoutes(app);
  app.use("/api/trpc", createExpressMiddleware({ router: appRouter, createContext }));
  if (process.env.NODE_ENV === "development") await setupVite(app, server); else serveStatic(app);
  const preferredPort = parseInt(process.env.PORT || "3000"); const port = await findAvailablePort(preferredPort);
  server.listen(port, () => console.log(`Server running on http://localhost:${port}/`));
}
startServer().catch(console.error);
