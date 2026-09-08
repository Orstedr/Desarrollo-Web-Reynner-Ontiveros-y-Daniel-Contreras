const mongoose = require('mongoose');

const usuarioSchema = mongoose.Schema({
    nombre: String,
    pass: String
}, { timestamps: true });

module.exports = mongoose.model('Usuario', usuarioSchema);
