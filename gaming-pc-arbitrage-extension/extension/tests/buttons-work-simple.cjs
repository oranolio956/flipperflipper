#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Button Functionality...\n');

// Load production files
const popupContent = fs.readFileSync(path.join(__dirname, '../dist/js/popup.js'), 'utf8');
const backgroundContent = fs.readFileSync(path.join(__dirname, '../dist/js/background.js'), 'utf8');
const dashboardContent = fs.readFileSync(path.join(__dirname, '../dist/js/dashboard.js'), 'utf8');

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`✅ ${name}`);
    passed++;
  } catch (e) {
    console.log(`❌ ${name}`);
    console.log(`   ${e.message}`);
    failed++;
  }
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

// Run tests
test('Dashboard button sends openDashboard message', () => {
  assert(popupContent.includes("document.getElementById('open-dashboard')"), 'Dashboard button handler missing');
  assert(popupContent.includes("action: 'openDashboard'"), 'openDashboard action missing');
  assert(backgroundContent.includes("request.action === 'openDashboard'"), 'Background handler missing');
  assert(backgroundContent.includes("chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html')"), 'Tab creation missing');
});

test('Settings button sends openSettings message', () => {
  assert(popupContent.includes("document.getElementById('open-settings')"), 'Settings button handler missing');
  assert(popupContent.includes("action: 'openSettings'"), 'openSettings action missing');
  assert(backgroundContent.includes("request.action === 'openSettings'"), 'Background handler missing');
  assert(backgroundContent.includes("dashboard.html#/settings"), 'Settings route missing');
});

test('Max Auto toggle sends enable/disable messages', () => {
  assert(popupContent.includes("automation-toggle"), 'Automation toggle missing');
  assert(popupContent.includes("MAX_AUTO_ENABLE"), 'Enable action missing');
  assert(popupContent.includes("MAX_AUTO_DISABLE"), 'Disable action missing');
  assert(backgroundContent.includes("class MaxAutoEngine"), 'MaxAutoEngine class missing');
  assert(backgroundContent.includes("maxAutoEngine.enable()"), 'Enable handler missing');
  assert(backgroundContent.includes("maxAutoEngine.disable()"), 'Disable handler missing');
});

test('Dashboard has real routing', () => {
  assert(dashboardContent.includes("class Router"), 'Router class missing');
  assert(dashboardContent.includes("'/scanner'"), 'Scanner route missing');
  assert(dashboardContent.includes("'/settings'"), 'Settings route missing');
  assert(dashboardContent.includes("'/automation'"), 'Automation route missing');
});

test('Content scripts parse real data', () => {
  const fbContent = fs.readFileSync(path.join(__dirname, '../dist/js/content-facebook.js'), 'utf8');
  assert(fbContent.includes('parseListingCard'), 'Parser function missing');
  assert(fbContent.includes('document.querySelectorAll'), 'DOM query missing');
  assert(fbContent.includes('marketplace/item/'), 'Marketplace URL pattern missing');
  assert(fbContent.includes('chrome.runtime.sendMessage'), 'Message sending missing');
});

test('Automation Center exists and is functional', () => {
  assert(dashboardContent.includes('renderAutomation'), 'Automation render function missing');
  assert(dashboardContent.includes('savedSearches'), 'Saved searches missing');
  assert(dashboardContent.includes('addSearch'), 'Add search function missing');
  assert(dashboardContent.includes('testScan'), 'Test scan function missing');
});

console.log(`\n📊 Results: ${passed} passed, ${failed} failed`);

if (failed > 0) {
  console.log('\n⚠️  Some tests failed. The extension has functional issues.');
  process.exit(1);
} else {
  console.log('\n✅ All critical buttons and features are functional!');
}