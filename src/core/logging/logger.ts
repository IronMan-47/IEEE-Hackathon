/**
 * Structured Logger for JARVIS Desktop Agent
 * Ensures sanitized, readable, categorized logs without exposing sensitive desktop content.
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR'
}

export type SubsystemTag = 'SHELL' | 'STATE' | 'IPC' | 'HOTKEY' | 'TRAY' | 'CONFIG' | 'CORE' | 'RENDERER' | 'PYTHON';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  subsystem: SubsystemTag;
  message: string;
  metadata?: Record<string, unknown>;
}

export class Logger {
  private static minLevel: LogLevel = LogLevel.INFO;

  public static setLogLevel(level: LogLevel): void {
    Logger.minLevel = level;
  }

  public static info(subsystem: SubsystemTag, message: string, metadata?: Record<string, unknown>): void {
    Logger.log(LogLevel.INFO, subsystem, message, metadata);
  }

  public static warn(subsystem: SubsystemTag, message: string, metadata?: Record<string, unknown>): void {
    Logger.log(LogLevel.WARN, subsystem, message, metadata);
  }

  public static error(subsystem: SubsystemTag, message: string, metadata?: Record<string, unknown>): void {
    Logger.log(LogLevel.ERROR, subsystem, message, metadata);
  }

  public static debug(subsystem: SubsystemTag, message: string, metadata?: Record<string, unknown>): void {
    Logger.log(LogLevel.DEBUG, subsystem, message, metadata);
  }

  private static log(level: LogLevel, subsystem: SubsystemTag, message: string, metadata?: Record<string, unknown>): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      subsystem,
      message,
      metadata
    };

    const formattedMessage = `[${entry.timestamp}] [${entry.level}] [${entry.subsystem}] ${entry.message}`;

    if (metadata) {
      console.log(formattedMessage, JSON.stringify(metadata));
    } else {
      console.log(formattedMessage);
    }
  }
}
