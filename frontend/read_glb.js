const fs = require('fs');

const buffer = fs.readFileSync('C:/Fleetguard/model.glb');
const magic = buffer.toString('utf8', 0, 4);
if (magic !== 'glTF') {
  console.log('Not a valid GLB file');
  process.exit(1);
}

const version = buffer.readUInt32LE(4);
const length = buffer.readUInt32LE(8);

const chunkLength = buffer.readUInt32LE(12);
const chunkType = buffer.toString('utf8', 16, 20);

if (chunkType === 'JSON') {
  const jsonChunk = buffer.toString('utf8', 20, 20 + chunkLength);
  const data = JSON.parse(jsonChunk);
  console.log("Meshes:");
  if (data.meshes) {
    data.meshes.forEach(m => console.log(' - ' + m.name));
  }
  console.log("Nodes:");
  if (data.nodes) {
    data.nodes.forEach(n => console.log(' - ' + n.name));
  }
  console.log("Materials:");
  if (data.materials) {
    data.materials.forEach(m => console.log(' - ' + m.name));
  }
  
  // Triangle count estimation (sum of all indices counts / 3)
  let triangles = 0;
  if (data.meshes) {
    data.meshes.forEach(mesh => {
      if (mesh.primitives) {
        mesh.primitives.forEach(prim => {
          if (prim.indices !== undefined) {
             const accessor = data.accessors[prim.indices];
             triangles += accessor.count / 3;
          } else if (prim.attributes && prim.attributes.POSITION !== undefined) {
             const accessor = data.accessors[prim.attributes.POSITION];
             triangles += accessor.count / 3;
          }
        });
      }
    });
  }
  console.log("Approximate Triangles:", triangles);
} else {
  console.log('First chunk is not JSON');
}
