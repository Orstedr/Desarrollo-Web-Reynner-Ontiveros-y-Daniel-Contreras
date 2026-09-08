const mongoose = require('mongoose');
const { Schema } = mongoose;

const comentarioSchema = Schema({
    texto: String,
    calificacion: {
        type: Number,
        min: 1,
        max: 5
    },
    usuario: {
        type: Schema.Types.ObjectId,
        ref: 'Usuario'
    },
    producto: {
        type: Schema.Types.ObjectId,
        ref: 'Producto'
    }
}, { timestamps: true });

module.exports = mongoose.model('Comentario', comentarioSchema);
