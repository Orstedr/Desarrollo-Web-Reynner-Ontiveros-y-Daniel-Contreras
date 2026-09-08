const mongoose = require('mongoose');
const { Schema } = mongoose;

const productoSchema = Schema({
    nombre: String,
    precio: Number,
    stock: Number,
    categoria: {
        type: Schema.Types.ObjectId,
        ref: 'Categoria'
    }
}, { timestamps: true });

module.exports = mongoose.model('Producto', productoSchema);
