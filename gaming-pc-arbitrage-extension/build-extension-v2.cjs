const fs = require('fs-extra');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const archiver = require('archiver');

const execAsync = promisify(exec);

const ROOT_DIR = __dirname;
const EXTENSION_DIR = path.join(ROOT_DIR, 'extension');
const BUILD_DIR = path.join(ROOT_DIR, 'build');
const DIST_DIR = path.join(EXTENSION_DIR, 'dist');

async function buildExtension() {
  console.log('🔨 Building Gaming PC Arbitrage Extension v2...\n');

  try {
    // 1. Clean build directories
    console.log('📁 Cleaning build directories...');
    await fs.remove(BUILD_DIR);
    await fs.ensureDir(BUILD_DIR);

    // 2. Install dependencies if needed
    console.log('📦 Installing dependencies...');
    await execAsync('npm install', { cwd: ROOT_DIR });
    await execAsync('npm install', { cwd: EXTENSION_DIR });

    // 3. Build core package
    console.log('🏗️  Building core package...');
    await execAsync('npm run build', { cwd: path.join(ROOT_DIR, 'packages', 'core') });

    // 4. Build extension with Vite
    console.log('⚡ Building extension with Vite...');
    await execAsync('npm run build', { cwd: EXTENSION_DIR });

    // 5. Copy manifest to dist
    console.log('📋 Copying manifest...');
    await fs.copy(
      path.join(EXTENSION_DIR, 'manifest.json'),
      path.join(DIST_DIR, 'manifest.json')
    );

    // 6. Copy icons if not already there
    if (await fs.pathExists(path.join(EXTENSION_DIR, 'icons'))) {
      console.log('🎨 Copying icons...');
      await fs.copy(
        path.join(EXTENSION_DIR, 'icons'),
        path.join(DIST_DIR, 'icons')
      );
    }

    // 7. Create extension package
    console.log('📦 Creating extension package...');
    const output = fs.createWriteStream(path.join(BUILD_DIR, 'gaming-pc-arbitrage-extension.zip'));
    const archive = archiver('zip', { zlib: { level: 9 } });

    archive.pipe(output);
    archive.directory(DIST_DIR, false);

    await new Promise((resolve, reject) => {
      output.on('close', resolve);
      archive.on('error', reject);
      archive.finalize();
    });

    // 8. Copy to root
    await fs.copy(
      path.join(BUILD_DIR, 'gaming-pc-arbitrage-extension.zip'),
      path.join(ROOT_DIR, 'gaming-pc-arbitrage-extension.zip')
    );

    console.log('\n✅ Build complete!');
    console.log(`📦 Extension package: ${path.join(BUILD_DIR, 'gaming-pc-arbitrage-extension.zip')}\n`);
    console.log(`📁 Unpacked extension: ${DIST_DIR}\n`);
    console.log('To install:');
    console.log('1. Open Chrome and go to chrome://extensions/');
    console.log('2. Enable "Developer mode"');
    console.log('3. Click "Load unpacked" and select:', DIST_DIR);
    console.log('\n');

  } catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
  }
}

// Run the build
buildExtension();