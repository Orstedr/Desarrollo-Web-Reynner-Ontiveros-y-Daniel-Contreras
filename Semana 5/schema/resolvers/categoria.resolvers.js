const Categoria = require('../../models/categoria');
const Producto = require('../../models/producto');

module.exports = {
    Query: {
        async getCategorias() {
            return await Categoria.find();
        },
        async getCategoriaById(obj, { id }) {
            return await Categoria.findById(id);
        }
    },
    Mutation: {
        async addCategoria(obj, { input }) {
            const categoria = new Categoria(input);
            await categoria.save();
            return categoria;
        },
        async updCategoria(obj, { id, input }) {
            return await Categoria.findByIdAndUpdate(id, input, { new: true });
        },
        async delCategoria(obj, { id }) {
            await Categoria.deleteOne({ _id: id });
            return { message: 'Categoría eliminada' };
        }
    },
    Categoria: {
        async productos(categoria) {
            return await Producto.find({ categoria: categoria.id });
        }
    }
};
