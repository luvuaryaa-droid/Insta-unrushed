// node tools/stills.mjs <outdir> <scale> t1 t2 ...   (times in seconds)
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import path from 'node:path';
const [out, scale, ...ts] = process.argv.slice(2);
const serveUrl = await bundle({ entryPoint: path.resolve('src/index.ts') });
const browserExecutable = process.env.REMOTION_CHROME || '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const comp = await selectComposition({ serveUrl, id: 'Ocean', browserExecutable });
for (const t of ts) {
  const frame = Math.round(parseFloat(t) * 24);
  await renderStill({ composition: comp, serveUrl, frame, output: `${out}/t${String(t).padStart(5, '0')}.jpg`, imageFormat: 'jpeg', jpegQuality: 88, browserExecutable, scale: parseFloat(scale) });
  console.log('ok', t);
}
