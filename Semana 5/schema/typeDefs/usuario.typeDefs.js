const { gql } = require('apollo-server-express');

const usuarioTypeDefs = gql`
    type Usuario {
        id: ID!
        nombre: String!
        pass: String!
    }

    input UsuarioInput {
        nombre: String!
        pass: String!
    }

    extend type Query {
        getUsuarios: [Usuario]
        getUsuariosById(id: ID!): Usuario
    }

    extend type Mutation {
        addUsuario(input: UsuarioInput): Usuario
        updUsuario(id: ID!, input: UsuarioInput): Usuario
        delUsuario(id: ID!): Alert
    }
`;

module.exports = usuarioTypeDefs;
