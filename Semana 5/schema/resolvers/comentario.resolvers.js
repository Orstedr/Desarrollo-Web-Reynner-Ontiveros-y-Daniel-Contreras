const Comentario = require('../../models/comentario');
const Usuario = require('../../models/usuario');
const Producto = require('../../models/producto');

module.exports = {
    Query: {
        async getComentarios() {
            return await Comentario.find();
        },
        async getComentariosByProducto(obj, { productoId }) {
            return await Comentario.find({ producto: productoId });
        }
    },
    Mutation: {
        async addComentario(obj, { input }) {
            const comentario = new Comentario({
                texto: input.texto,
                calificacion: input.calificacion,
                usuario: input.usuarioId,
                producto: input.productoId
            });
            await comentario.save();
            return comentario;
        },
        async delComentario(obj, { id }) {
            await Comentario.deleteOne({ _id: id });
            return { message: 'Comentario eliminado' };
        }
    },
    Comentario: {
        async usuario(comentario) {
            return await Usuario.findById(comentario.usuario);
        },
        async producto(comentario) {
            return await Producto.findById(comentario.producto);
        }
    },
    // Ambos bloques se fusionan (deep merge) con los resolvers "Usuario" y
    // "Producto" que ya existen desde PR1 / pedido.resolvers.js.
    Usuario: {
        async comentarios(usuario) {
            return await Comentario.find({ usuario: usuario.id });
        }
    },
    Producto: {
        async comentarios(producto) {
            return await Comentario.find({ producto: producto.id });
        }
    }
};
