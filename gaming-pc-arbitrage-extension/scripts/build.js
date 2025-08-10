#!/usr/bin/env node

/**
 * Build Script
 * Package the extension for distribution
 */

import { execSync } from 'child_process';
import fs from 'fs-extra';
import path from 'path';
import archiver from 'archiver';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.join(__dirname, '..');
const distDir = path.join(rootDir, 'dist');
const buildDir = path.join(rootDir, 'build');

async function build() {
  console.log('🏗️  Building Gaming PC Arbitrage Extension...\n');

  try {
    // Step 1: Clean previous builds
    console.log('📦 Cleaning previous builds...');
    await fs.remove(distDir);
    await fs.remove(buildDir);
    await fs.ensureDir(distDir);
    await fs.ensureDir(buildDir);

    // Step 2: Build core package
    console.log('🔨 Building core package...');
    execSync('npm run build:core', { stdio: 'inherit', cwd: rootDir });

    // Step 3: Build extension
    console.log('🔨 Building extension...');
    execSync('npm run build:extension', { stdio: 'inherit', cwd: rootDir });

    // Step 4: Copy static files
    console.log('📋 Copying static files...');
    await copyStaticFiles();

    // Step 5: Generate manifest
    console.log('📝 Generating manifest...');
    await generateManifest();

    // Step 6: Optimize assets
    console.log('🎨 Optimizing assets...');
    await optimizeAssets();

    // Step 7: Create production bundle
    console.log('📦 Creating production bundle...');
    await createProductionBundle();

    // Step 8: Create source bundle for Chrome Web Store
    console.log('📦 Creating source bundle...');
    await createSourceBundle();

    // Step 9: Validate extension
    console.log('✅ Validating extension...');
    await validateExtension();

    console.log('\n✨ Build completed successfully!');
    console.log(`📍 Production bundle: ${path.join(buildDir, 'extension.zip')}`);
    console.log(`📍 Source bundle: ${path.join(buildDir, 'source.zip')}`);

  } catch (error) {
    console.error('\n❌ Build failed:', error);
    process.exit(1);
  }
}

async function copyStaticFiles() {
  const staticFiles = [
    'extension/icons',
    'extension/popup.html',
    'extension/options.html',
    'extension/dashboard.html',
    'extension/_locales',
  ];

  for (const file of staticFiles) {
    const src = path.join(rootDir, file);
    const dest = path.join(distDir, path.basename(file));
    
    if (await fs.pathExists(src)) {
      await fs.copy(src, dest);
    }
  }
}

async function generateManifest() {
  const manifestTemplate = await fs.readJson(path.join(rootDir, 'extension/manifest.json'));
  const packageJson = await fs.readJson(path.join(rootDir, 'package.json'));

  // Update version from package.json
  manifestTemplate.version = packageJson.version;

  // Production optimizations
  if (process.env.NODE_ENV === 'production') {
    // Remove development permissions
    manifestTemplate.permissions = manifestTemplate.permissions.filter(
      p => !['debugger', 'management'].includes(p)
    );

    // Update CSP for production
    manifestTemplate.content_security_policy = {
      extension_pages: "script-src 'self'; object-src 'self'"
    };
  }

  await fs.writeJson(path.join(distDir, 'manifest.json'), manifestTemplate, { spaces: 2 });
}

async function optimizeAssets() {
  // Minify HTML files
  const htmlFiles = await fs.readdir(distDir);
  for (const file of htmlFiles.filter(f => f.endsWith('.html'))) {
    const content = await fs.readFile(path.join(distDir, file), 'utf8');
    const minified = content
      .replace(/\s+/g, ' ')
      .replace(/>\s+</g, '><')
      .trim();
    await fs.writeFile(path.join(distDir, file), minified);
  }

  // Remove source maps in production
  if (process.env.NODE_ENV === 'production') {
    const jsFiles = await fs.readdir(path.join(distDir, 'js'));
    for (const file of jsFiles.filter(f => f.endsWith('.map'))) {
      await fs.remove(path.join(distDir, 'js', file));
    }
  }
}

async function createProductionBundle() {
  const output = fs.createWriteStream(path.join(buildDir, 'extension.zip'));
  const archive = archiver('zip', { zlib: { level: 9 } });

  return new Promise((resolve, reject) => {
    output.on('close', resolve);
    archive.on('error', reject);

    archive.pipe(output);
    archive.directory(distDir, false);
    archive.finalize();
  });
}

async function createSourceBundle() {
  const output = fs.createWriteStream(path.join(buildDir, 'source.zip'));
  const archive = archiver('zip', { zlib: { level: 9 } });

  const excludePatterns = [
    'node_modules/**',
    'dist/**',
    'build/**',
    '.git/**',
    '*.log',
    '.env*',
    'coverage/**',
    '.vscode/**',
  ];

  return new Promise((resolve, reject) => {
    output.on('close', resolve);
    archive.on('error', reject);

    archive.pipe(output);
    
    // Add all source files except excluded
    archive.glob('**/*', {
      cwd: rootDir,
      ignore: excludePatterns,
    });

    archive.finalize();
  });
}

async function validateExtension() {
  const manifestPath = path.join(distDir, 'manifest.json');
  const manifest = await fs.readJson(manifestPath);

  // Check required files exist
  const requiredFiles = [
    manifest.background.service_worker,
    ...manifest.content_scripts.map(cs => cs.js).flat(),
    manifest.action.default_popup,
    manifest.options_page,
  ];

  for (const file of requiredFiles) {
    const filePath = path.join(distDir, file);
    if (!await fs.pathExists(filePath)) {
      throw new Error(`Required file missing: ${file}`);
    }
  }

  // Check permissions
  const sensitivePermissions = ['<all_urls>', 'cookies', 'debugger'];
  const usedSensitive = manifest.permissions.filter(p => sensitivePermissions.includes(p));
  if (usedSensitive.length > 0) {
    console.warn(`⚠️  Using sensitive permissions: ${usedSensitive.join(', ')}`);
  }

  // Check file sizes
  const stats = await fs.stat(path.join(buildDir, 'extension.zip'));
  const sizeMB = stats.size / (1024 * 1024);
  if (sizeMB > 10) {
    console.warn(`⚠️  Extension size is ${sizeMB.toFixed(2)}MB (recommended < 10MB)`);
  }

  console.log(`📏 Extension size: ${sizeMB.toFixed(2)}MB`);
}

// Run build
build();