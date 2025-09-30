const fs = require('fs');
const path = require('path');

const publicDir = path.resolve(__dirname, '..', 'public');
const src = path.join(publicDir, 'logo192.png');
const dest = path.join(publicDir, 'fitter_logo.png');

try {
  if (!fs.existsSync(dest)) {
    if (fs.existsSync(src)) {
      fs.copyFileSync(src, dest);
      console.log('Copied logo192.png -> fitter_logo.png');
    } else {
      console.warn('logo192.png not found in public/. Please add your fitter_logo.png manually to public/.');
    }
  } else {
    console.log('fitter_logo.png already exists.');
  }
} catch (err) {
  console.error('Failed to ensure fitter_logo.png:', err);
  process.exitCode = 1;
}
