const mongoose = require('mongoose');
const { Schema } = mongoose;

const detallePedidoSchema = Schema({
    producto: {
        type: Schema.Types.ObjectId,
        ref: 'Producto'
    },
    cantidad: Number
}, { _id: false });

const pedidoSchema = Schema({
    usuario: {
        type: Schema.Types.ObjectId,
        ref: 'Usuario'
    },
    productos: [detallePedidoSchema],
    estado: {
        type: String,
        enum: ['PENDIENTE', 'ENVIADO', 'ENTREGADO', 'CANCELADO'],
        default: 'PENDIENTE'
    }
}, { timestamps: true });

module.exports = mongoose.model('Pedido', pedidoSchema);
