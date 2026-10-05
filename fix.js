const fs = require('fs');
let code = fs.readFileSync('src/apps/desktop/renderer/components/overlay-view.ts', 'utf8');
code = code.replace(/\\\/g, '\');
code = code.replace(/\\\$/g, '$');
fs.writeFileSync('src/apps/desktop/renderer/components/overlay-view.ts', code);
