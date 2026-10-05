import { spawn, ChildProcess } from 'child_process';
import * as http from 'http';
import { Logger } from '../../../core/logging/logger';

import { app } from 'electron';
import * as path from 'path';

export class PythonProcessManager {
  private pythonProcess: ChildProcess | null = null;
  private isReady: boolean = false;
  private port: number = 8765;

  constructor() {}

  public async startDaemon(): Promise<boolean> {
    Logger.info('CORE', 'Starting Python Agent Core process daemon...');

    try {
      const isPackaged = app.isPackaged;
      
      let command: string;
      let args: string[];
      let spawnCwd: string;

      if (isPackaged) {
        command = path.join(process.resourcesPath, 'jarvis-agent.exe');
        args = [];
        spawnCwd = path.dirname(command);
      } else {
        command = 'python';
        args = ['-m', 'agent.main'];
        spawnCwd = process.cwd();
      }

      this.pythonProcess = spawn(command, args, {
        env: { ...process.env, PYTHONPATH: '.' },
        cwd: spawnCwd,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      this.pythonProcess.stdout?.on('data', (data) => {
        Logger.info('CORE', `[Python Core] ${data.toString().trim()}`);
      });

      this.pythonProcess.stderr?.on('data', (data) => {
        Logger.warn('CORE', `[Python Core Error] ${data.toString().trim()}`);
      });

      this.pythonProcess.on('exit', (code, signal) => {
        Logger.warn('CORE', `Python Agent Core process exited with code ${code}, signal ${signal}`);
        this.isReady = false;
        this.pythonProcess = null;
      });

      // Health check poll until ready (up to 5 seconds)
      this.isReady = await this.pollHealth(10, 500);
      if (this.isReady) {
        Logger.info('CORE', `Python Agent Core is healthy and listening on port ${this.port}`);
      } else {
        Logger.warn('CORE', 'Python Agent Core health check timed out. Will fallback gracefully if unreachable.');
      }

      return this.isReady;
    } catch (err: unknown) {
      Logger.error('CORE', 'Failed to spawn Python process daemon', { error: String(err) });
      return false;
    }
  }

  private async pollHealth(maxAttempts: number, intervalMs: number): Promise<boolean> {
    for (let i = 0; i < maxAttempts; i++) {
      const ok = await this.checkHealth();
      if (ok) return true;
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
    return false;
  }

  private checkHealth(): Promise<boolean> {
    return new Promise((resolve) => {
      const req = http.get(`http://127.0.0.1:${this.port}/health`, (res) => {
        if (res.statusCode === 200) {
          resolve(true);
        } else {
          resolve(false);
        }
      });
      req.on('error', () => resolve(false));
      req.setTimeout(1000, () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  public isAgentReady(): boolean {
    return this.isReady;
  }

  public stopDaemon(): void {
    if (this.pythonProcess) {
      Logger.info('CORE', 'Terminating Python process daemon...');
      this.pythonProcess.kill('SIGTERM');
      this.pythonProcess = null;
      this.isReady = false;
    }
  }
}
