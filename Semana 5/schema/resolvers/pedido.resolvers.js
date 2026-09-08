const Pedido = require('../../models/pedido');
const Usuario = require('../../models/usuario');
const Producto = require('../../models/producto');

module.exports = {
    Query: {
        async getPedidos() {
            return await Pedido.find();
        },
        async getPedidoById(obj, { id }) {
            return await Pedido.findById(id);
        },
        async getPedidosByUsuario(obj, { usuarioId }) {
            return await Pedido.find({ usuario: usuarioId });
        }
    },
    Mutation: {
        async addPedido(obj, { input }) {
            const pedido = new Pedido({
                usuario: input.usuarioId,
                productos: input.productos.map((p) => ({
                    producto: p.productoId,
                    cantidad: p.cantidad
                }))
            });
            await pedido.save();
            return pedido;
        },
        async updEstadoPedido(obj, { id, estado }) {
            return await Pedido.findByIdAndUpdate(id, { estado }, { new: true });
        },
        async delPedido(obj, { id }) {
            await Pedido.deleteOne({ _id: id });
            return { message: 'Pedido eliminado' };
        }
    },
    Pedido: {
        async usuario(pedido) {
            return await Usuario.findById(pedido.usuario);
        }
    },
    DetallePedido: {
        async producto(detalle) {
            return await Producto.findById(detalle.producto);
        }
    },
    // Esto se fusiona con el resolver "Usuario" que ya existe (de PR1),
    // gracias al deep merge que hace schema/resolvers/index.js.
    Usuario: {
        async pedidos(usuario) {
            return await Pedido.find({ usuario: usuario.id });
        }
    }
};
