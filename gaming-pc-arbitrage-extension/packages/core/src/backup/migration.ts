/**
 * Migration functionality
 */

export interface Migration {
  version: number;
  up: () => Promise<void>;
  down: () => Promise<void>;
}

export class MigrationManager {
  private migrations: Migration[] = [];
  
  register(migration: Migration): void {
    this.migrations.push(migration);
    this.migrations.sort((a, b) => a.version - b.version);
  }
  
  async up(targetVersion?: number): Promise<void> {
    const target = targetVersion ?? this.migrations[this.migrations.length - 1]?.version;
    
    for (const migration of this.migrations) {
      if (migration.version <= target) {
        await migration.up();
      }
    }
  }
  
  async down(targetVersion: number = 0): Promise<void> {
    const reversedMigrations = [...this.migrations].reverse();
    
    for (const migration of reversedMigrations) {
      if (migration.version > targetVersion) {
        await migration.down();
      }
    }
  }
}