const fs = require('fs');
const path = require('path');

// Fusiona dos objetos de resolvers de forma profunda (deep merge).
// Es necesario porque, por ejemplo, "Query" y "Mutation" reciben aportes
// de VARIOS archivos (usuario.resolvers.js, categoria.resolvers.js, etc.)
// y hay que combinarlos en un solo objeto Query / Mutation al final.
function mergeResolvers(target, source) {
    for (const key of Object.keys(source)) {
        const value = source[key];
        const esObjetoPlano =
            typeof value === 'object' && value !== null && !Array.isArray(value);

        if (esObjetoPlano) {
            target[key] = mergeResolvers(target[key] || {}, value);
        } else {
            target[key] = value;
        }
    }
    return target;
}

// Igual que en typeDefs/index.js: se cargan automáticamente todos los
// archivos *.resolvers.js que existan en esta carpeta. Cada entidad nueva
// solo agrega su propio archivo, sin tocar este index.js.
const resolvers = fs
    .readdirSync(__dirname)
    .filter((file) => file !== 'index.js' && file.endsWith('.resolvers.js'))
    .map((file) => require(path.join(__dirname, file)))
    .reduce((acumulado, parcial) => mergeResolvers(acumulado, parcial), {});

module.exports = resolvers;
