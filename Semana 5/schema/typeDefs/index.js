const fs = require('fs');
const path = require('path');

// Carga automáticamente todos los archivos *.typeDefs.js que existan en esta
// carpeta (sin importar quién los haya agregado ni en qué PR). Así, cuando
// alguien agrega una entidad nueva, solo crea su archivo <entidad>.typeDefs.js
// y no necesita tocar este index.js -> cero conflictos de merge.
const typeDefs = fs
    .readdirSync(__dirname)
    .filter((file) => file !== 'index.js' && file.endsWith('.typeDefs.js'))
    .map((file) => require(path.join(__dirname, file)));

module.exports = typeDefs;
