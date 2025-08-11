// Test that the extension structure is valid
const fs = require('fs');
const path = require('path');

console.log('🧪 Testing extension structure...\n');

const distDir = path.join(__dirname, 'extension/dist');
const requiredFiles = [
  'manifest.json',
  'popup.html',
  'dashboard.html',
  'js/background.js',
  'js/popup.js',
  'js/dashboard.js',
  'js/scanner.js',
  'css/popup.css',
  'css/dashboard.css',
  'icons/icon-16.png',
  'icons/icon-128.png'
];

let allGood = true;

// Check files exist
requiredFiles.forEach(file => {
  const filePath = path.join(distDir, file);
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file}`);
  } else {
    console.log(`❌ Missing: ${file}`);
    allGood = false;
  }
});

// Check manifest
const manifest = JSON.parse(fs.readFileSync(path.join(distDir, 'manifest.json'), 'utf8'));
console.log(`\n📋 Manifest version: ${manifest.version}`);
console.log(`📋 Background script: ${manifest.background.service_worker}`);

// Check for static content
console.log('\n🔍 Checking for static content...');
const jsFiles = ['background.js', 'dashboard.js', 'scanner.js'];
jsFiles.forEach(file => {
  const content = fs.readFileSync(path.join(distDir, 'js', file), 'utf8');
  if (content.includes('TODO') || content.includes('placeholder')) {
    console.log(`⚠️  ${file} contains static markers`);
  } else {
    console.log(`✅ ${file} appears clean`);
  }
});

console.log(allGood ? '\n✅ Extension ready to load!' : '\n❌ Fix issues before loading');
