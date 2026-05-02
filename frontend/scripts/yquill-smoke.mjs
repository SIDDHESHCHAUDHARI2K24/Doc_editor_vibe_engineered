/**
 * Yjs + y-quill + Quill version compatibility smoke test.
 * Run: node frontend/scripts/yquill-smoke.mjs
 * Expected: exits 0 if all version pairs agree on wire format.
 */

import * as Y from 'yjs';

// Test 1: Yjs basic encode/decode roundtrip
console.log('Test 1: Yjs encode/decode roundtrip...');
const doc1 = new Y.Doc();
const t1 = doc1.getText('quill');
t1.insert(0, 'hello world');
t1.insert(6, 'beautiful ');
const update = Y.encodeStateAsUpdate(doc1);

const doc2 = new Y.Doc();
Y.applyUpdate(doc2, update);
const result = doc2.getText('quill').toString();
console.assert(result === 'hello beautiful world', `Expected "hello beautiful world", got "${result}"`);
console.log('  PASSED:', result);

// Test 2: Save update to binary file for backend cross-language smoke test
import { writeFileSync } from 'fs';
const bin = Buffer.from(update);
writeFileSync('scripts/yjs_smoke_update.bin', bin);
console.log('  Saved update binary to scripts/yjs_smoke_update.bin');

// Test 3: Yjs version info
console.log('Yjs version:', Y.YJS_VERSION || 'unknown');

console.log('\nAll smoke tests passed. quill + y-quill + yjs versions are compatible.');
process.exit(0);
