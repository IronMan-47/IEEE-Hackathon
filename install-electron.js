const https = require('https');
const fs = require('fs');
const path = require('path');
const childProcess = require('child_process');

const zipFile = path.resolve('electron-download.zip');
const distDir = path.resolve('node_modules/electron/dist');
const pathFile = path.resolve('node_modules/electron/path.txt');

fs.mkdirSync(distDir, { recursive: true });

function download(url) {
  console.log('Downloading Electron from:', url);
  https.get(url, (res) => {
    if (res.statusCode === 301 || res.statusCode === 302) {
      download(res.headers.location);
      return;
    }
    const fileStream = fs.createWriteStream(zipFile);
    res.pipe(fileStream);

    fileStream.on('finish', () => {
      fileStream.close(() => {
        console.log('Download complete. Extracting tar zip archive...');
        try {
          childProcess.execSync(`tar -xf "${zipFile}" -C "${distDir}"`);
          fs.writeFileSync(pathFile, 'electron.exe');
          console.log('✅ ELECTRON INSTALLED SUCCESSFULLY!');
        } catch (err) {
          console.error('Tar extraction failed, fallback to extract-zip:', err);
          const extract = require('extract-zip');
          extract(zipFile, { dir: distDir }).then(() => {
            fs.writeFileSync(pathFile, 'electron.exe');
            console.log('✅ ELECTRON INSTALLED SUCCESSFULLY VIA EXTRACT-ZIP!');
          });
        }
      });
    });
  }).on('error', (err) => {
    console.error('Download failed:', err);
  });
}

download('https://github.com/electron/electron/releases/download/v34.2.0/electron-v34.2.0-win32-x64.zip');
