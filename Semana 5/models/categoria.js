const mongoose = require('mongoose');

const categoriaSchema = mongoose.Schema({
    nombre: String,
    descripcion: String
}, { timestamps: true });

module.exports = mongoose.model('Categoria', categoriaSchema);
