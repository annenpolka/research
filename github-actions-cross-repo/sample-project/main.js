#!/usr/bin/env node

/**
 * Sample project that demonstrates using external repositories
 * in a real-world scenario
 */

const fs = require('fs');
const path = require('path');

// Configuration
const EXTERNAL_LIBS_PATH = path.join(__dirname, '..', 'external-libs');

/**
 * Check if external libraries are available
 */
function checkExternalLibraries() {
  console.log('=== Checking External Libraries ===\n');

  const expectedLibs = [
    { name: 'toolkit', path: path.join(EXTERNAL_LIBS_PATH, 'toolkit') },
    { name: 'checkout', path: path.join(EXTERNAL_LIBS_PATH, 'checkout') },
  ];

  const availableLibs = [];

  expectedLibs.forEach(lib => {
    if (fs.existsSync(lib.path)) {
      console.log(`✓ ${lib.name} is available at ${lib.path}`);
      availableLibs.push(lib.name);
    } else {
      console.log(`✗ ${lib.name} is not available at ${lib.path}`);
    }
  });

  console.log();
  return availableLibs;
}

/**
 * Read package information from external library
 */
function readExternalPackageInfo(libName) {
  const packageJsonPath = path.join(EXTERNAL_LIBS_PATH, libName, 'package.json');

  if (fs.existsSync(packageJsonPath)) {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    return {
      name: packageJson.name,
      version: packageJson.version,
      description: packageJson.description,
    };
  }

  return null;
}

/**
 * List packages in toolkit
 */
function listToolkitPackages() {
  const packagesPath = path.join(EXTERNAL_LIBS_PATH, 'toolkit', 'packages');

  if (!fs.existsSync(packagesPath)) {
    return [];
  }

  return fs.readdirSync(packagesPath)
    .filter(item => {
      const itemPath = path.join(packagesPath, item);
      return fs.statSync(itemPath).isDirectory();
    });
}

/**
 * Main function
 */
function main() {
  console.log('Cross-Repository Integration Example\n');
  console.log('=====================================\n');

  // Check available libraries
  const availableLibs = checkExternalLibraries();

  if (availableLibs.length === 0) {
    console.log('No external libraries found.');
    console.log('Please run the GitHub Actions workflow to checkout external repositories.');
    return;
  }

  // Read package information
  console.log('=== External Library Information ===\n');

  availableLibs.forEach(libName => {
    const info = readExternalPackageInfo(libName);
    if (info) {
      console.log(`Library: ${libName}`);
      console.log(`  Name: ${info.name}`);
      console.log(`  Version: ${info.version}`);
      console.log(`  Description: ${info.description}`);
      console.log();
    }
  });

  // List toolkit packages
  if (availableLibs.includes('toolkit')) {
    console.log('=== Toolkit Packages ===\n');
    const packages = listToolkitPackages();
    packages.forEach(pkg => {
      console.log(`  - ${pkg}`);
    });
    console.log();
  }

  // Summary
  console.log('=== Summary ===\n');
  console.log(`Found ${availableLibs.length} external libraries`);
  console.log('External repository integration successful!');
}

// Run main function
if (require.main === module) {
  main();
}

module.exports = {
  checkExternalLibraries,
  readExternalPackageInfo,
  listToolkitPackages,
};
