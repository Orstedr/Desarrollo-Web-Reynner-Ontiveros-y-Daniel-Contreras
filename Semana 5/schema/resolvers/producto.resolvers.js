const Producto = require('../../models/producto');
const Categoria = require('../../models/categoria');

module.exports = {
    Query: {
        async getProductos() {
            return await Producto.find();
        },
        async getProductoById(obj, { id }) {
            return await Producto.findById(id);
        },
        async getProductosByCategoria(obj, { categoriaId }) {
            return await Producto.find({ categoria: categoriaId });
        }
    },
    Mutation: {
        async addProducto(obj, { input }) {
            const producto = new Producto({
                nombre: input.nombre,
                precio: input.precio,
                stock: input.stock,
                categoria: input.categoriaId
            });
            await producto.save();
            return producto;
        },
        async updProducto(obj, { id, input }) {
            return await Producto.findByIdAndUpdate(
                id,
                {
                    nombre: input.nombre,
                    precio: input.precio,
                    stock: input.stock,
                    categoria: input.categoriaId
                },
                { new: true }
            );
        },
        async delProducto(obj, { id }) {
            await Producto.deleteOne({ _id: id });
            return { message: 'Producto eliminado' };
        }
    },
    Producto: {
        async categoria(producto) {
            return await Categoria.findById(producto.categoria);
        }
    }
};
