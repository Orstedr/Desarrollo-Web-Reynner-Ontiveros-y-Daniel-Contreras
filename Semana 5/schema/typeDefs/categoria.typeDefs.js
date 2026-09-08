const { gql } = require('apollo-server-express');

const categoriaTypeDefs = gql`
    type Categoria {
        id: ID!
        nombre: String!
        descripcion: String
        productos: [Producto]
    }

    input CategoriaInput {
        nombre: String!
        descripcion: String
    }

    extend type Query {
        getCategorias: [Categoria]
        getCategoriaById(id: ID!): Categoria
    }

    extend type Mutation {
        addCategoria(input: CategoriaInput): Categoria
        updCategoria(id: ID!, input: CategoriaInput): Categoria
        delCategoria(id: ID!): Alert
    }
`;

module.exports = categoriaTypeDefs;
