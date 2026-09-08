const Usuario = require('../../models/usuario');

module.exports = {
    Query: {
        async getUsuarios() {
            return await Usuario.find();
        },
        async getUsuariosById(obj, { id }) {
            return await Usuario.findById(id);
        }
    },
    Mutation: {
        async addUsuario(obj, { input }) {
            const usuario = new Usuario(input);
            await usuario.save();
            return usuario;
        },
        async updUsuario(obj, { id, input }) {
            return await Usuario.findByIdAndUpdate(id, input, { new: true });
        },
        async delUsuario(obj, { id }) {
            await Usuario.deleteOne({ _id: id });
            return { message: 'Usuario eliminado' };
        }
    }
};
